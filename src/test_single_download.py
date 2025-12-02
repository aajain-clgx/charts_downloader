import os
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load environment variables
load_dotenv()

SC_USERNAME = os.getenv('SC_USERNAME')
SC_PASSWORD = os.getenv('SC_PASSWORD')

def login(page):
    print("Logging in...")
    page.goto("https://stockcharts.com/login")
    page.fill("input#form_UserID", SC_USERNAME)
    page.fill("input#form_UserPassword", SC_PASSWORD)
    page.click("button.btn-green")
    page.wait_for_load_state('domcontentloaded')
    print("Login submitted.")

def test_download():
    # Use a specific URL for testing (e.g., SPY)
    url = "https://stockcharts.com/sc3/ui/?s=SPY"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            login(page)
            page.wait_for_timeout(2000)
            
            print(f"Navigating to {url}...")
            page.goto(url)
            page.wait_for_load_state('domcontentloaded')
            
            # Wait for chart
            chart_element = page.wait_for_selector("div#chart-image-and-inspector-container img", timeout=10000)
            
            if not chart_element:
                print("Could not find chart element.")
                return

            # Define test output path
            output_path = os.path.join(os.getcwd(), "test_chart_download.png")
            if os.path.exists(output_path):
                os.remove(output_path)

            print("Attempting right-click download...")
            try:
                with page.expect_download(timeout=30000) as download_info:
                    # Right click the chart to show context menu
                    chart_element.click(button="right")
                    
                    # Wait for the menu option to appear and click it
                    page.get_by_text("Download Chart Image", exact=True).click()
                
                download = download_info.value
                download.save_as(output_path)
                print(f"SUCCESS: Downloaded chart to {output_path}")
                
            except Exception as e:
                print(f"FAILED: Context menu download failed: {e}")
                
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            browser.close()

if __name__ == '__main__':
    test_download()
