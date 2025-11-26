#!/bin/bash

# Get absolute path to the plist
PLIST_SOURCE="$(pwd)/scripts/com.bear.stockcharts.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.bear.stockcharts.plist"

echo "Installing LaunchAgent..."
cp "$PLIST_SOURCE" "$PLIST_DEST"

# Update Python path in plist
# We assume the user has run 'uv venv' which creates .venv in the project root
PYTHON_PATH="$(pwd)/.venv/bin/python"

if [ ! -f "$PYTHON_PATH" ]; then
    echo "Error: Virtual environment not found at $PYTHON_PATH"
    echo "Please run 'uv venv' first."
    exit 1
fi

sed -i '' "s|/usr/bin/python3|$PYTHON_PATH|g" "$PLIST_DEST"

echo "Loading LaunchAgent..."
launchctl unload "$PLIST_DEST" 2>/dev/null
launchctl load "$PLIST_DEST"

echo "Done. The downloader will run daily at 6:00 PM."
