import os
import shutil
import sqlite3
import sys

# Setup paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'charts.db')
IMAGES_DIR = os.path.join(DATA_DIR, 'images')

def full_reset():
    print("WARNING: This will delete all data (database and images).")
    confirm = input("Are you sure you want to proceed? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return

    # 1. Remove Database
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print(f"Deleted database: {DB_PATH}")
        except Exception as e:
            print(f"Error deleting database: {e}")
    else:
        print("Database not found.")

    # 2. Remove Images
    if os.path.exists(IMAGES_DIR):
        try:
            # Delete all files in images dir
            for filename in os.listdir(IMAGES_DIR):
                file_path = os.path.join(IMAGES_DIR, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')
            print(f"Cleared images directory: {IMAGES_DIR}")
        except Exception as e:
            print(f"Error clearing images directory: {e}")
    
    # 3. Re-initialize DB (optional, but helpful)
    print("Re-initializing empty database...")
    try:
        # Add src to sys.path to import db module
        src_path = os.path.join(BASE_DIR, 'src')
        sys.path.append(src_path)
        import db
        db.init_db()
        print("Database re-initialized successfully.")
    except Exception as e:
        print(f"Error re-initializing database: {e}")

    print("Full reset complete.")

if __name__ == "__main__":
    full_reset()
