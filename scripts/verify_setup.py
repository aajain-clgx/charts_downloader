import os
import sys
import shutil
from PIL import Image, ImageDraw, ImageFont

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
import db

IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'images')

def create_dummy_image(filename, text):
    img = Image.new('RGB', (800, 600), color = (30, 30, 30))
    d = ImageDraw.Draw(img)
    # Draw some random lines to look like a chart
    d.line([(0, 500), (200, 400), (400, 450), (600, 300), (800, 100)], fill=(0, 230, 118), width=3)
    d.text((10,10), text, fill=(255,255,255))
    img.save(os.path.join(IMAGES_DIR, filename))

def main():
    print("Initializing DB...")
    db.init_db()
    
    print("Creating dummy data...")
    dummy_data = [
        ("AAPL", "2023-10-26", "AAPL_2023-10-26.png"),
        ("GOOGL", "2023-10-26", "GOOGL_2023-10-26.png"),
        ("TSLA", "2023-10-25", "TSLA_2023-10-25.png"),
    ]
    
    for ticker, date, filename in dummy_data:
        create_dummy_image(filename, f"{ticker} - {date}")
        chart_id = db.add_chart(ticker, date, filename, f"http://example.com/{ticker}")
        print(f"Added {ticker} (ID: {chart_id})")
        
        if ticker == "AAPL":
            db.add_tag(chart_id, "Breakout")
            print(f"Added tag 'Breakout' to {ticker}")

    print("Verification data created. You can now run 'python src/app.py' to see the dashboard.")

if __name__ == '__main__':
    main()
