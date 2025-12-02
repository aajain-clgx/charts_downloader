#!/bin/bash

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Path to python in venv
PYTHON_PATH="$PROJECT_ROOT/.venv/bin/python"

# Check if venv exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "Error: Virtual environment not found at $PYTHON_PATH"
    echo "Please run 'uv venv' first."
    exit 1
fi

# Run the downloader
# Pass any arguments (like --force) to the python script
echo "Starting download process..."
"$PYTHON_PATH" "$PROJECT_ROOT/src/downloader.py" "$@"
