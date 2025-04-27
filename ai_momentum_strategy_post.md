# 📈 AI Altcoin Momentum Strategy Backtest 📉

## Strategy Description

I've backtested a simple momentum strategy on the top AI altcoins with the following rules:

- **Look-back window:** Daily rebalancing based on 24H performance
- **Entry criteria:** Go long on the top three AI coins by 24-hour performance
- **Exit criteria:** Close the position when either (a) the coin drops out of the daily top-three list or (b) its trailing 14-day return turns negative
- **Backtest period:** Past 90 days

## Performance Summary

- **Equal-Weight Portfolio Return:** -34.4%
- **Individual Coin Performance:**
  - PANDA: 317.7% (Max Drawdown: -82.6%)
  - ANON: 287.7% (Max Drawdown: -83.9%)
  - SINGULARRY: 213.4% (Max Drawdown: -50.9%)
  - FHE: 210.3% (Max Drawdown: -32.3%)
  - $BILLY: -19.1% (Max Drawdown: -81.1%)
  - TAO: -23.5% (Max Drawdown: -60.4%)
  - CLANKER: -27.6% (Max Drawdown: -67.8%)
  - FORT: -30.4% (Max Drawdown: -46.6%)
  - FROK: -30.6% (Max Drawdown: -72.3%)
  - SAMURAI: -31.2% (Max Drawdown: -74.0%)
  - PROMPT: -31.3% (Max Drawdown: -52.8%)
  - ASM: -31.5% (Max Drawdown: -73.3%)
  - KRL: -34.3% (Max Drawdown: -49.8%)
  - TAG: -37.4% (Max Drawdown: -72.6%)
  - QUBIC: -41.6% (Max Drawdown: -69.0%)
  - FAI: -42.8% (Max Drawdown: -77.2%)
  - HERA: -46.9% (Max Drawdown: -49.1%)
  - BOTIFY: -47.2% (Max Drawdown: -88.5%)
  - CUDOS: -48.1% (Max Drawdown: -76.9%)
  - CX: -50.9% (Max Drawdown: -71.4%)
  - TRIAS: -53.5% (Max Drawdown: -65.1%)
  - KIZUNA: -57.6% (Max Drawdown: -78.0%)
  - SYNT: -62.9% (Max Drawdown: -67.1%)
  - MARSH: -63.5% (Max Drawdown: -67.2%)
  - PALM: -64.0% (Max Drawdown: -78.8%)
  - GLQ: -64.4% (Max Drawdown: -68.2%)
  - VANA: -65.6% (Max Drawdown: -55.6%)
  - THT: -66.6% (Max Drawdown: -67.3%)
  - REX: -67.8% (Max Drawdown: -66.8%)
  - HMND: -68.4% (Max Drawdown: -60.4%)
  - LMR: -68.7% (Max Drawdown: -72.9%)
  - GPU: -69.0% (Max Drawdown: -78.1%)
  - SERV: -69.6% (Max Drawdown: -82.2%)
  - BOTTO: -69.9% (Max Drawdown: -74.3%)
  - AIUS: -70.4% (Max Drawdown: -77.3%)
  - ROKO: -70.7% (Max Drawdown: -68.2%)
  - SNS: -70.8% (Max Drawdown: -75.2%)
  - BERRY: -78.1% (Max Drawdown: -77.7%)
  - MAX: -78.3% (Max Drawdown: -96.0%)
  - DKING: -79.5% (Max Drawdown: -80.2%)
  - TANK: -79.6% (Max Drawdown: -92.1%)
  - HASHAI: -80.2% (Max Drawdown: -82.1%)
  - MASA: -81.6% (Max Drawdown: -88.9%)
  - LKI: -81.8% (Max Drawdown: -88.5%)
  - GTAI: -82.0% (Max Drawdown: -79.3%)
  - APY: -83.9% (Max Drawdown: -93.2%)
  - LUSH: -83.9% (Max Drawdown: -77.4%)
  - $DOGEAI: -84.6% (Max Drawdown: -90.6%)
  - DEAI: -88.2% (Max Drawdown: -84.2%)
  - TIG: -89.9% (Max Drawdown: -70.2%)
  - EAI: -90.9% (Max Drawdown: -86.0%)
  - LMT: -91.4% (Max Drawdown: -95.8%)
  - KEKE: -91.6% (Max Drawdown: -92.1%)
  - FOMO: -92.2% (Max Drawdown: -97.2%)
  - ⌘: -94.8% (Max Drawdown: -93.3%)
  - BULLY: -97.8% (Max Drawdown: -97.3%)

## Key Insights

• Volatility spike detected around 2025-02-03 with volatility 60.89, which is 2.3x the average. This may have been caused by significant market movements affecting multiple coins simultaneously.

• Sharp reversal detected in QUBIC on 2025-03-18 with a swing of 36.1%. This coincided with a drop in portfolio value of 157.7% over the next 48 hours.

## Notes

- The strategy is fully systematic and requires daily rebalancing
- This approach targets the most volatile AI altcoins with strong daily momentum
- No transaction costs or slippage were included in this backtest
- The strategy focuses exclusively on AI-related cryptocurrencies
- Past performance is not indicative of future results

If you found this analysis helpful, tips are appreciated! 🙏
