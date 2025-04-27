#!/bin/bash

# Daily AI Coins Momentum Backtest Runner
# This script will run the prefetch and backtest operations in sequence

echo "==============================================="
echo "   AI Coins Momentum Backtest Pipeline"
echo "==============================================="
echo

# Create cache directory if it doesn't exist
mkdir -p "Momentum Backtest/cache"

# Step 1: Prefetch the data
echo "Step 1/2: Prefetching historical data for top AI coins..."
python3 "Momentum Backtest/prefetch_data.py"
echo

# Step 2: Run the momentum backtest
echo "Step 2/2: Running momentum backtest..."
python3 "Momentum Backtest/run_backtest.py"
echo

echo "==============================================="
echo "Pipeline complete! Check 'Momentum Backtest' folder for results:"
echo "- momentum_results.png: Chart of returns and drawdowns"
echo "- momentum_results.csv: Daily performance data"
echo "- portfolio_allocations.csv: History of portfolio holdings"
echo "===============================================" 