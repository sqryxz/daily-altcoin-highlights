# Daily AI Altcoin Highlights with Momentum Backtest

This project fetches daily data for AI-related cryptocurrencies, highlights the top performers, and performs a simple momentum backtesting strategy on the top 3 coins.

## Features

- Fetches AI cryptocurrency market data from CoinGecko (with fallback to CryptoRank)
- Generates a daily summary of top AI coins by 24-hour performance
- Sends the daily summary to a Discord channel via webhook
- Performs a momentum backtest on the top 3 performing AI coins
- Visualizes performance with a chart
- Compares performance against Bitcoin as a benchmark

## Setup

1. Install the required dependencies:

```
python3 -m pip install -r requirements.txt
```

2. Configure the Discord webhook URL in `ai_highlights.py` if needed.

## Usage

Run the main script to generate the daily AI altcoin highlights and perform momentum backtesting:

```
python3 momentum_backtest.py
```

This will:
1. Fetch the latest AI cryptocurrency data
2. Generate a summary of top performers
3. Send the summary to Discord (if configured)
4. Perform a 7-day momentum backtest on the top 3 coins
5. Generate a performance chart saved as `momentum_backtest_plot.png`

## Configuration

You can modify the following parameters:

- In `ai_highlights.py`:
  - `TOP_N_COINS`: Number of top coins to include in the highlights
  - `DISCORD_WEBHOOK_URL`: Your Discord webhook URL
  - `CACHE_TTL_SECONDS`: How long to cache API data

- In `momentum_backtest.py`:
  - `BACKTEST_DAYS`: How many days to include in the backtest
  - `INVESTMENT_PER_COIN`: Hypothetical amount to invest in each coin

## Notes

- The script uses CoinGecko's free API, which has rate limits. Sleep delays are added to avoid rate limiting issues.
- A caching mechanism is implemented to reduce API calls.

## Configuration

You can modify the following parameters in the respective script files:

**AI Highlights (`ai_highlights.py`):**
- `TOP_N_COINS`: Number of top coins to display (default: 5)
- `DISCORD_WEBHOOK_URL`: Discord webhook for sending summaries

**Momentum Backtest (`Momentum Backtest/momentum_backtest.py`):**
- `LOOKBACK_DAYS`: Momentum measurement period (default: 7 days)
- `HOLDING_PERIOD_DAYS`: Rebalancing frequency (default: 1 day)
- `TOP_N_COINS`: Number of coins to invest in (default: 3)
- `BENCHMARK_COIN`: Benchmark to compare against (default: "bitcoin")

## Disclaimer

This is for informational purposes only and not financial advice. Cryptocurrency markets are highly volatile, and past performance doesn't guarantee future results. 