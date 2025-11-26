# Stock Charts Downloader & Viewer

A professional tool to automate downloading stock charts from StockCharts.com and viewing them in a modern dashboard.

## Setup

1.  **Prerequisites**: Python 3.8+, [uv](https://github.com/astral-sh/uv)
2.  **Setup Environment**:
    ```bash
    uv venv
    source .venv/bin/activate
    ```
3.  **Install Dependencies**:
    ```bash
    uv sync
    playwright install
    ```
4.  **Configuration**:
    *   Copy `.env.example` to `.env` and fill in your StockCharts credentials.
    *   Add URLs to `urls.txt`.

## Usage

### Running the Downloader manually

```bash
# Run normally (checks if market is open)
.venv/bin/python src/downloader.py

# Force run even if market is closed (weekend/holiday)
.venv/bin/python src/downloader.py --force
```

The script will:
1. Check if the US stock market (NYSE) is open.
2. Log in to StockCharts.com.
3. Iterate through tickers in `urls.txt`.
4. Download the chart image.
5. Save metadata to `data/charts.db`.

### Web Interface
To start the dashboard:
```bash
python src/app.py
```
Visit `http://localhost:5001` in your browser.

## Automation
To schedule the downloader to run daily (Mac only):
```bash
chmod +x scripts/setup_automation.sh
./scripts/setup_automation.sh
```

## Maintenance Scripts

The `scripts/` directory contains utilities for managing data:

**1. Full Reset (Wipe Everything)**
Deletes the database and all downloaded images.
```bash
.venv/bin/python scripts/full_reset.py
```

**2. Delete Specific Day**
Removes all charts and database entries for a specific date.
```bash
.venv/bin/python scripts/delete_day.py 2023-11-25
```
