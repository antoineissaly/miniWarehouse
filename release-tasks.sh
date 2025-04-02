#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

echo "Running release tasks: Initializing Database..."
python init_db.py
echo "Release tasks finished successfully."