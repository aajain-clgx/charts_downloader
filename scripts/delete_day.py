import os
import sqlite3
import argparse
import sys

# Setup paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'charts.db')
IMAGES_DIR = os.path.join(DATA_DIR, 'images')

def delete_day(date_str):
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find records for the day
    print(f"Searching for records on {date_str}...")
    cursor.execute("SELECT id, image_filename FROM charts WHERE chart_date = ?", (date_str,))
    rows = cursor.fetchall()

    if not rows:
        print(f"No records found for {date_str}.")
        conn.close()
        return

    print(f"Found {len(rows)} records.")
    confirm = input("Are you sure you want to delete them? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        conn.close()
        return

    deleted_count = 0
    errors = 0

    for row in rows:
        chart_id = row['id']
        filename = row['image_filename']
        
        # 1. Delete Image
        file_path = os.path.join(IMAGES_DIR, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Deleted image: {filename}")
            except Exception as e:
                print(f"Error deleting image {filename}: {e}")
                errors += 1
        else:
            print(f"Image not found (skipping): {filename}")

        # 2. Delete DB Record (and cascading tags if configured, otherwise manual)
        # We need to delete tags first if no cascade
        try:
            cursor.execute("DELETE FROM tags WHERE chart_id = ?", (chart_id,))
            cursor.execute("DELETE FROM charts WHERE id = ?", (chart_id,))
            deleted_count += 1
        except Exception as e:
            print(f"Error deleting DB record for id {chart_id}: {e}")
            errors += 1

    conn.commit()
    conn.close()
    
    print(f"Operation complete. Deleted {deleted_count} records. {errors} errors.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Delete charts for a specific day.')
    parser.add_argument('date', help='Date to delete (YYYY-MM-DD)')
    args = parser.parse_args()
    
    delete_day(args.date)
