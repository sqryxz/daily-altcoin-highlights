# AI Coins Momentum Backtest Strategy

This module implements a momentum trading strategy focused on AI-related cryptocurrencies. The strategy leverages the observation that assets which have recently outperformed their peers tend to continue outperforming in the short term.

## Strategy Overview

The momentum strategy implemented here:

1. Identifies a universe of AI-related cryptocurrencies using the existing `ai_highlights.py` module
2. Calculates momentum over a 7-day lookback period
3. Ranks all coins based on their momentum (recent price change)
4. Invests in the top 3 coins with the highest momentum
5. Rebalances the portfolio daily
6. Compares performance against Bitcoin as a benchmark

## Performance Metrics

The backtest calculates and reports the following metrics:

- **Cumulative return**: Total return of the strategy compared to the benchmark
- **Annualized volatility**: Measure of price fluctuation, annualized
- **Sharpe ratio**: Risk-adjusted return metric (using a 2% risk-free rate)
- **Maximum drawdown**: Largest peak-to-trough decline
- **Win rate**: Percentage of rebalances that outperform the benchmark
- **Spike capture count**: Number of times the strategy captured daily price moves of 10% or more

## Usage

To run the backtest:

```bash
# Navigate to the project root
cd /path/to/daily-altcoin-highlights

# Run the backtest
python3 Momentum\ Backtest/run_backtest.py
```

The results will be saved in the `Momentum Backtest` directory:
- `momentum_results.png`: Visual chart of the backtest performance
- `momentum_results.csv`: Detailed daily performance data

## Configuration

You can modify the following parameters in `momentum_backtest.py` to adjust the strategy:

- `LOOKBACK_DAYS`: Momentum measurement period (default: 7 days)
- `HOLDING_PERIOD_DAYS`: Rebalancing frequency (default: 1 day)
- `TOP_N_COINS`: Number of coins to invest in (default: 3)
- `HISTORY_DAYS`: Historical data period for backtest (default: 90 days)
- `BENCHMARK_COIN`: Benchmark to compare against (default: "bitcoin")
- `INITIAL_CAPITAL`: Starting capital for the backtest (default: $10,000)

## Dependencies

This module requires the following Python packages:
- pandas
- numpy
- matplotlib
- requests

These should be installed in your environment to run the backtest. 