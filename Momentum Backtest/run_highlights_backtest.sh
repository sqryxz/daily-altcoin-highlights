#!/bin/bash

echo "Running AI Highlights-based Backtest..."
echo "---------------------------------------"

# Ensure the cache directory exists
CACHE_DIR="Momentum Backtest/cache"
mkdir -p "$CACHE_DIR"

# Execute the highlights-based backtest script
python3 "Momentum Backtest/highlights_based_backtest.py"

echo "---------------------------------------"
echo "Backtest complete!"
echo "Results are saved in the 'Momentum Backtest' folder." 