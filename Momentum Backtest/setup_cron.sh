#!/bin/bash

# Script to set up a daily cron job for the momentum backtest

# Get the absolute path of the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_PATH="$PROJECT_DIR/Momentum Backtest/run.sh"

# Check if the script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: Could not locate the run.sh script at $SCRIPT_PATH"
    exit 1
fi

# Make sure the script is executable
chmod +x "$SCRIPT_PATH"

# Create a temporary file for the cron job
TEMP_CRON=$(mktemp)

# Backup existing crontab
crontab -l > "$TEMP_CRON" 2>/dev/null || echo "# New crontab" > "$TEMP_CRON"

# Check if the job already exists
if grep -q "Momentum Backtest/run.sh" "$TEMP_CRON"; then
    echo "The cron job for AI Coins Momentum Backtest already exists in your crontab."
    rm "$TEMP_CRON"
    exit 0
fi

# Add the new cron job to run every day at 1 AM
echo "# Daily AI Coins Momentum Backtest - runs at 1 AM" >> "$TEMP_CRON"
echo "0 1 * * * cd $PROJECT_DIR && $SCRIPT_PATH >> $PROJECT_DIR/Momentum\ Backtest/backtest.log 2>&1" >> "$TEMP_CRON"

# Install the new crontab
if crontab "$TEMP_CRON"; then
    echo "Success! Cron job has been set up to run the momentum backtest daily at 1 AM."
    echo "The output will be logged to: $PROJECT_DIR/Momentum Backtest/backtest.log"
else
    echo "Error: Failed to install cron job."
    exit 1
fi

# Clean up
rm "$TEMP_CRON"

echo
echo "To view your cron jobs, run: crontab -l"
echo "To edit your cron jobs, run: crontab -e"
echo
echo "The momentum backtest will now run automatically every day at 1 AM." 