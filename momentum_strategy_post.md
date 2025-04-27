# 📈 Cryptocurrency Momentum Strategy Backtest 📉

## Strategy Description

I've backtested a simple momentum strategy on cryptocurrencies with the following rules:

- **Look-back window:** 7 days
- **Entry criteria:** Go long on a coin if its 7-day return > 0 and it ranks in the top three performers for that day
- **Exit criteria:** Close the position when either (a) the coin drops out of the daily top-three list or (b) its trailing 14-day return turns negative
- **Backtest period:** Past 90 days

## Performance Summary

- **Equal-Weight Portfolio Return:** -34.4%
- **Individual Coin Performance:**
  - XRP: 6.8% (Max Drawdown: -42.8%)
  - BTC: 0.1% (Max Drawdown: -27.2%)
  - BNB: -12.0% (Max Drawdown: -23.7%)
  - ADA: -19.2% (Max Drawdown: -51.0%)
  - SOL: -21.5% (Max Drawdown: -59.0%)
  - LINK: -29.3% (Max Drawdown: -57.5%)
  - AVAX: -38.1% (Max Drawdown: -56.4%)
  - DOGE: -43.6% (Max Drawdown: -59.9%)
  - ETH: -47.3% (Max Drawdown: -55.8%)

## Key Insights

• Volatility spike detected around 2025-04-11 with volatility 6.68, which is 2.6x the average. This may have been caused by significant market movements affecting multiple coins simultaneously.

• Sharp reversal detected in XRP on 2025-03-04 with a swing of 53.0%. This coincided with a drop in portfolio value of -14.0% over the next 48 hours.

## Notes

- The strategy is fully systematic and requires daily rebalancing
- No transaction costs or slippage were included in this backtest
- Past performance is not indicative of future results

If you found this analysis helpful, tips are appreciated! 🙏
