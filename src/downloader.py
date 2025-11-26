import os
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from PIL import Image
import holidays
import db

# Load environment variables
load_dotenv()

SC_USERNAME = os.getenv('SC_USERNAME')
SC_PASSWORD = os.getenv('SC_PASSWORD')
IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'images')

# Constants for image processing
SIDEBAR_COLOR = (14, 38, 62)
COLOR_TOLERANCE = 5

DEFAULT_URLS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'urls.txt')

def login(page):
    print("Logging in...")
    page.goto("https://stockcharts.com/login")
    # Adjust selectors based on actual login page
    # This is a best guess, might need adjustment
    page.fill("input#form_UserID", SC_USERNAME)
    page.fill("input#form_UserPassword", SC_PASSWORD)
    page.click("button.btn-green") # Click the Log In button
    # page.wait_for_load_state('networkidle') # Too strict for some sites
    page.wait_for_load_state('domcontentloaded')
    print("Login submitted.")

def crop_chart_image(filepath):
    """
    Crops the blue sidebar from the right side of the chart image if present.
    """
    try:
        with Image.open(filepath) as img:
            width, height = img.size
            mid_y = height // 2
            
            # Check if right edge is the specific dark blue sidebar color
            right_pixel = img.getpixel((width - 1, mid_y))
            
            # Allow for small variations in color just in case
            if (abs(right_pixel[0] - SIDEBAR_COLOR[0]) < COLOR_TOLERANCE and 
                abs(right_pixel[1] - SIDEBAR_COLOR[1]) < COLOR_TOLERANCE and 
                abs(right_pixel[2] - SIDEBAR_COLOR[2]) < COLOR_TOLERANCE):
                
                print("Detected blue sidebar. Cropping...")
                
                # Find the transition point (scan up to 200px)
                crop_x = width
                for i in range(200):
                    x = width - 1 - i
                    pixel = img.getpixel((x, mid_y))
                    # Check if pixel is NOT the blue color
                    if (abs(pixel[0] - SIDEBAR_COLOR[0]) > COLOR_TOLERANCE or 
                        abs(pixel[1] - SIDEBAR_COLOR[1]) > COLOR_TOLERANCE or 
                        abs(pixel[2] - SIDEBAR_COLOR[2]) > COLOR_TOLERANCE):
                        crop_x = x + 1 # Crop just after the non-blue pixel
                        break
                
                if crop_x < width:
                    img = img.crop((0, 0, crop_x, height))
                    img.save(filepath)
                    print(f"Cropped image to width {crop_x}")
                    return True
    except Exception as e:
        print(f"Error post-processing image: {e}")
    return False

def process_url(page, url):
    print(f"Processing {url}...")
    page.goto(url)
    # page.wait_for_load_state('networkidle') # Too strict
    page.wait_for_load_state('domcontentloaded')
    
    # Extract Ticker
    # Try to find ticker in input box or page title
    try:
        ticker = page.input_value("input#symbol") # Common ID for symbol input
    except:
        # Fallback: parse from URL or title
        ticker = url.split("s=")[-1].split("&")[0]
    
    # Extract Date
    # Usually stockcharts has a date on the chart or we use today's date
    # Let's use today's date for the record, but maybe try to find the "As of" date on page
    # For now, current date is safer for "when we downloaded it"
    chart_date = datetime.now().strftime("%Y-%m-%d")
    
    if db.chart_exists(ticker, chart_date):
        print(f"Chart for {ticker} on {chart_date} already exists. Skipping.")
        return
    
    # Find Chart Image
    # The main chart is usually an img tag with class 'chartimg' or inside a specific div
    # We need to be careful to get the generated chart.
    # StockCharts often generates the image dynamically.
    
    try:
        # Selector for the main chart image. 
        # Inspecting stockcharts (mental model): usually <img class="chartimg" ...>
        # Updated selector based on inspection:
        chart_element = page.wait_for_selector("div#chart-image-and-inspector-container img", timeout=10000)
        
        if not chart_element:
            print(f"Could not find chart image for {ticker}")
            return

        # Download image
        # We can't just 'download' the src if it's session based or blob.
        # Best way is to take a screenshot of the element.
        filename = f"{ticker}_{chart_date}_{int(time.time())}.png"
        filepath = os.path.join(IMAGES_DIR, filename)
        
        # Extract period
        try:
            period = page.locator('#period-menu-lower').input_value()
            print(f"Detected period: {period}")
        except Exception as e:
            print(f"Could not detect period: {e}")
            period = "Unknown"

        chart_element.screenshot(path=filepath)
        
        # Post-process: Remove blue sidebar if present
        crop_chart_image(filepath)

        print(f"Saved chart to {filepath}")
        
        # Save to DB
        db.add_chart(ticker, chart_date, filename, url, period)
        print(f"Recorded in database with period: {period}")
        
    except Exception as e:
        print(f"Error processing {url}: {e}")


def is_market_open():
    today = datetime.now().date()
    
    # Check for weekend (Saturday=5, Sunday=6)
    if today.weekday() >= 5:
        return False, "Weekend"
        
    # Check for NYSE holidays
    us_holidays = holidays.NYSE()
    if today in us_holidays:
        return False, f"Holiday: {us_holidays.get(today)}"
        
    return True, "Market Open"

def main():
    if not SC_USERNAME or not SC_PASSWORD:
        print("Error: SC_USERNAME and SC_PASSWORD must be set in .env")
        return

    parser = argparse.ArgumentParser(description='Download StockCharts images.')
    parser.add_argument('--urls', default=DEFAULT_URLS_FILE, help='Path to file containing URLs')
    parser.add_argument('--force', action='store_true', help='Force run even if market is closed')
    args = parser.parse_args()
    
    # Check if market is open
    is_open, reason = is_market_open()
    if not is_open and not args.force:
        print(f"Market is closed today ({reason}). Skipping download.")
        print("Use --force to override.")
        return
    
    if not is_open and args.force:
        print(f"Market is closed ({reason}), but --force flag used. Proceeding...")

    if not os.path.exists(args.urls):
        print(f"Error: URLs file {args.urls} not found.")
        return

    with open(args.urls, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Set headless=False to debug
        context = browser.new_context()
        page = context.new_page()
        
        try:
            login(page)
            # Small pause to ensure login session is established
            page.wait_for_timeout(2000)
            
            for url in urls:
                process_url(page, url)
                page.wait_for_timeout(1000) # Be nice to the server
                
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            browser.close()

if __name__ == '__main__':
    main()
