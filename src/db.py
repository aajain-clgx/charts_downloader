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

    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_ticker ON charts(ticker)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_date ON charts(chart_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_charts_period ON charts(period)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_chart_id ON tags(chart_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_tag_name ON tags(tag_name)')
    
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

def remove_tag(chart_id, tag_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tags WHERE chart_id = ? AND tag_name = ?', (chart_id, tag_name))
    conn.commit()
    conn.close()

def chart_exists(ticker, chart_date, period=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if period:
        cursor.execute('SELECT 1 FROM charts WHERE ticker = ? AND chart_date = ? AND period = ?', (ticker, chart_date, period))
    else:
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
        conditions.append("UPPER(c.period) = UPPER(?)")
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
        
    # Grouping
    query += " GROUP BY c.id"
    
    if latest_per_ticker:
        # Use Window Function to filter for latest per ticker/period efficiently in SQL
        # Wrap the existing query as a subquery
        query = f"""
            SELECT * FROM (
                SELECT sub.*, 
                       ROW_NUMBER() OVER (PARTITION BY sub.ticker, sub.period ORDER BY sub.chart_date DESC, sub.id DESC) as rn
                FROM ({query}) sub
            )
            WHERE rn = 1
        """

    query += " ORDER BY chart_date DESC, id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    results = [dict(row) for row in rows]
    
    # Python-side filtering is no longer needed for latest_per_ticker
        
    return results

if __name__ == '__main__':
    init_db()
