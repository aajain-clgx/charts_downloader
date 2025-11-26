import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'charts.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create charts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS charts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            chart_date TEXT NOT NULL,
            image_filename TEXT NOT NULL,
            original_url TEXT,
            period TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create tags table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chart_id INTEGER,
            tag_name TEXT NOT NULL,
            FOREIGN KEY (chart_id) REFERENCES charts (id),
            UNIQUE(chart_id, tag_name)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def add_chart(ticker, chart_date, image_filename, original_url, period=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO charts (ticker, chart_date, image_filename, original_url, period)
        VALUES (?, ?, ?, ?, ?)
    ''', (ticker, chart_date, image_filename, original_url, period))
    chart_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return chart_id

def add_tag(chart_id, tag_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO tags (chart_id, tag_name) VALUES (?, ?)', (chart_id, tag_name))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # Tag already exists for this chart
    finally:
        conn.close()

def chart_exists(ticker, chart_date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM charts WHERE ticker = ? AND chart_date = ?', (ticker, chart_date))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def get_charts(ticker=None, date_start=None, date_end=None, tags=None, latest_per_ticker=False, tag_operator='OR', period=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Base query
    query = "SELECT c.*, GROUP_CONCAT(t.tag_name) as tags FROM charts c LEFT JOIN tags t ON c.id = t.chart_id"
    conditions = []
    params = []
    
    # Filter by ticker
    if ticker:
        conditions.append("UPPER(c.ticker) = UPPER(?)")
        params.append(ticker)
    
    # Filter by period
    if period:
        conditions.append("c.period = ?")
        params.append(period)
    
    # Filter by date range
    if date_start:
        conditions.append("c.chart_date >= ?")
        params.append(date_start)
    if date_end:
        conditions.append("c.chart_date <= ?")
        params.append(date_end)
        
    # Filter by tags (list)
    if tags and len(tags) > 0:
        placeholders = ','.join(['?'] * len(tags))
        if tag_operator == 'AND':
            # Find charts that have ALL of the specified tags
            conditions.append(f"""
                c.id IN (
                    SELECT chart_id 
                    FROM tags 
                    WHERE tag_name IN ({placeholders}) 
                    GROUP BY chart_id 
                    HAVING COUNT(DISTINCT tag_name) = ?
                )
            """)
            params.extend(tags)
            params.append(len(set(tags))) # Count unique tags
        else:
            # OR logic: Find charts that have AT LEAST ONE of the specified tags
            conditions.append(f"c.id IN (SELECT chart_id FROM tags WHERE tag_name IN ({placeholders}))")
            params.extend(tags)
        
    # Apply conditions
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    # Grouping and Ordering
    query += " GROUP BY c.id"
    
    # If latest_per_ticker is True, we need to filter the results in Python or use a complex query.
    # A complex query is more efficient but harder to maintain with dynamic filters.
    # Given the scale is likely small, we can fetch and filter, OR use a window function approach if SQLite supports it (it does in newer versions).
    # Let's try a SQL approach using MAX(id) per ticker.
    
    if latest_per_ticker:
        # Wrap the previous query or modify it. 
        # Actually, simpler approach:
        # 1. Build the WHERE clause as above.
        # 2. If latest_per_ticker, add a condition that c.id must be the MAX(id) for that ticker *within the filtered set*.
        # That's hard.
        # Alternative: Filter in Python. It's safer and easier given the complexity.
        pass

    query += " ORDER BY c.chart_date DESC, c.id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    results = [dict(row) for row in rows]
    
    if latest_per_ticker:
        # Filter to keep only the first occurrence of each ticker (since we ordered by date DESC)
        seen_tickers = set()
        unique_results = []
        for row in results:
            if row['ticker'] not in seen_tickers:
                seen_tickers.add(row['ticker'])
                unique_results.append(row)
        return unique_results
        
    return results

if __name__ == '__main__':
    init_db()
