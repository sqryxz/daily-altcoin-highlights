import ai_highlights
import requests
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import datetime, timedelta
import os

# Constants
COINGECKO_HISTORY_URL = "https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
BACKTEST_DAYS = 7  # Number of days to backtest
INVESTMENT_PER_COIN = 100  # Hypothetical $100 invested in each coin

def get_historical_data(coin_id, days):
    """
    Fetch historical price data for a given coin from CoinGecko.
    """
    print(f"Fetching {days} days of historical data for {coin_id}...")
    
    params = {
        'vs_currency': 'usd',
        'days': days,
        'interval': 'daily'
    }
    
    try:
        # Add a short delay to respect rate limits
        time.sleep(1.5)
        
        response = requests.get(COINGECKO_HISTORY_URL.format(coin_id=coin_id), params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract price data
        prices = data.get('prices', [])
        if not prices:
            print(f"No price data found for {coin_id}")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df[['date', 'price']]
        
        return df
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching historical data for {coin_id}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error with {coin_id}: {e}")
        return None

def perform_momentum_backtest(top_coins, days=BACKTEST_DAYS):
    """
    Performs a simple momentum backtest on the top performing coins.
    
    1. Get historical data for each coin
    2. Calculate returns if we had invested in these coins N days ago
    3. Plot performance and calculate metrics
    """
    # Start date for backtesting (days ago from now)
    today = datetime.now()
    
    # Need to get more days of data to perform the backtest
    fetch_days = days + 1
    
    results = []
    all_prices = {}
    
    for coin in top_coins:
        coin_id = coin.get('id')
        symbol = coin.get('symbol', '').upper()
        
        print(f"Backtesting momentum strategy for {symbol} ({coin_id})...")
        
        # Get historical price data
        hist_data = get_historical_data(coin_id, fetch_days)
        
        if hist_data is None or len(hist_data) < 2:
            print(f"Insufficient historical data for {symbol}. Skipping in backtest.")
            continue
            
        # Store the price data
        all_prices[symbol] = hist_data
        
        # Calculate the return if we had invested INVESTMENT_PER_COIN
        # at the beginning of the period
        start_price = hist_data.iloc[0]['price']
        end_price = hist_data.iloc[-1]['price']
        
        profit = INVESTMENT_PER_COIN * (end_price / start_price - 1)
        roi = (end_price / start_price - 1) * 100
        
        result = {
            'symbol': symbol,
            'coin_id': coin_id,
            'start_price': start_price,
            'end_price': end_price,
            'roi_percent': roi,
            'profit': profit
        }
        
        results.append(result)
    
    return results, all_prices

def calculate_volatility_insights(all_prices, top_symbols):
    """
    Analyze price data to identify volatility spikes and sharp reversals.
    Returns a list of insight strings.
    """
    insights = []
    
    # Create a DataFrame for the basket
    if not all_prices or not top_symbols:
        return ["Insufficient data to calculate volatility insights."]
    
    # Calculate daily returns for each coin
    symbol_returns = {}
    for symbol in top_symbols:
        if symbol in all_prices:
            df = all_prices[symbol]
            if len(df) >= 2:
                df['daily_return'] = df['price'].pct_change() * 100
                df = df.dropna()
                symbol_returns[symbol] = df
    
    # Find volatility spikes (days with returns more than 2 std dev)
    for symbol, df in symbol_returns.items():
        if len(df) >= 3:  # Need at least 3 days for meaningful std dev
            mean_return = df['daily_return'].mean()
            std_return = df['daily_return'].std()
            
            # Check for volatility spikes
            for i, row in df.iterrows():
                if abs(row['daily_return'] - mean_return) > 2 * std_return:
                    date_str = row['date'].strftime('%Y-%m-%d')
                    direction = "upward" if row['daily_return'] > 0 else "downward"
                    insights.append(f"• {symbol} experienced a significant {direction} volatility spike of {row['daily_return']:.2f}% on {date_str}")
                    break  # Just report one spike per coin
    
    # Look for sharp reversals (sign change in daily returns)
    for symbol, df in symbol_returns.items():
        if len(df) >= 3:
            for i in range(1, len(df)):
                prev_return = df.iloc[i-1]['daily_return']
                curr_return = df.iloc[i]['daily_return']
                
                # Check for significant sign change
                if prev_return * curr_return < 0 and abs(prev_return) > 5 and abs(curr_return) > 5:
                    date_str = df.iloc[i]['date'].strftime('%Y-%m-%d')
                    if prev_return > 0 and curr_return < 0:
                        insights.append(f"• {symbol} showed a sharp reversal from +{prev_return:.2f}% to {curr_return:.2f}% on {date_str}")
                    else:
                        insights.append(f"• {symbol} rebounded from {prev_return:.2f}% to +{curr_return:.2f}% on {date_str}")
                    break  # Just report one reversal per coin
    
    # Create an insight about the most volatile coin
    if symbol_returns:
        volatilities = {symbol: df['daily_return'].std() for symbol, df in symbol_returns.items()}
        most_volatile = max(volatilities.items(), key=lambda x: x[1])
        least_volatile = min(volatilities.items(), key=lambda x: x[1])
        
        insights.append(f"• {most_volatile[0]} showed the highest daily volatility ({most_volatile[1]:.2f}%), while {least_volatile[0]} was the most stable ({least_volatile[1]:.2f}%)")
    
    # Limit to 3 insights maximum
    return insights[:3]

def plot_individual_equity_curves(all_prices, top_symbols):
    """
    Create individual equity curves for each coin and an equal-weight basket curve.
    Saves the chart to a file.
    """
    if not all_prices or not top_symbols:
        print("Insufficient data to plot equity curves.")
        return
    
    plt.figure(figsize=(14, 10))
    
    # Create subplot for individual curves
    plt.subplot(2, 1, 1)
    
    # Process data for equal-weight basket
    basket_df = None
    normalized_dfs = {}
    
    for symbol in top_symbols:
        if symbol in all_prices:
            df = all_prices[symbol]
            if len(df) >= 2:
                # Normalize to start at $100 investment
                normalized = df.copy()
                normalized['equity'] = INVESTMENT_PER_COIN * (df['price'] / df['price'].iloc[0])
                plt.plot(normalized['date'], normalized['equity'], label=f"{symbol} (${normalized['equity'].iloc[-1]:.2f})")
                normalized_dfs[symbol] = normalized
    
    # Create the equal-weight basket
    if normalized_dfs:
        # Find common dates
        common_dates = None
        for df in normalized_dfs.values():
            if common_dates is None:
                common_dates = set(df['date'])
            else:
                common_dates = common_dates.intersection(set(df['date']))
        
        if common_dates:
            # Create basket dataframe
            basket_df = pd.DataFrame({'date': sorted(common_dates)})
            
            # Add equity values for each coin and calculate basket
            for symbol, df in normalized_dfs.items():
                basket_df = basket_df.merge(
                    df[['date', 'equity']].rename(columns={'equity': symbol}),
                    on='date'
                )
            
            basket_df['basket'] = basket_df[list(normalized_dfs.keys())].mean(axis=1)
    
    plt.title('Individual Equity Curves (Starting with $100 per coin)')
    plt.xlabel('Date')
    plt.ylabel('Equity Value ($)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Plot equal-weight basket
    if basket_df is not None:
        plt.subplot(2, 1, 2)
        plt.plot(basket_df['date'], basket_df['basket'], 'k-', linewidth=2, 
                 label=f"Equal-Weight Basket (${basket_df['basket'].iloc[-1]:.2f})")
        
        # Add benchmark if available
        btc_data = None
        try:
            btc_data = get_historical_data('bitcoin', BACKTEST_DAYS+1)
            if btc_data is not None and len(btc_data) >= 2:
                btc_normalized = btc_data.copy()
                btc_normalized['equity'] = INVESTMENT_PER_COIN * (btc_data['price'] / btc_data['price'].iloc[0])
                plt.plot(btc_normalized['date'], btc_normalized['equity'], 'r--', 
                         label=f"BTC (${btc_normalized['equity'].iloc[-1]:.2f})")
        except Exception as e:
            print(f"Error adding BTC to chart: {e}")
        
        plt.title('Equal-Weight Basket Performance vs. BTC Benchmark')
        plt.xlabel('Date')
        plt.ylabel('Equity Value ($)')
        plt.grid(True, alpha=0.3)
        plt.legend()
    
    plt.tight_layout()
    plt.savefig('equity_curves.png')
    print("Equity curves chart saved as 'equity_curves.png'")

def plot_performance(all_prices, top_symbols):
    """Plot the price performance of the top coins during the backtest period."""
    plt.figure(figsize=(12, 6))
    
    for symbol in top_symbols:
        if symbol in all_prices:
            df = all_prices[symbol]
            # Normalize prices to start at 100 for better comparison
            normalized = df.copy()
            normalized['price'] = 100 * (df['price'] / df['price'].iloc[0])
            plt.plot(normalized['date'], normalized['price'], label=symbol)
    
    plt.title('Price Performance of Top AI Momentum Coins')
    plt.xlabel('Date')
    plt.ylabel('Normalized Price (Start = 100)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('momentum_backtest_plot.png')
    print("Performance plot saved as 'momentum_backtest_plot.png'")

def get_backtest_summary_text(results):
    """Generate the backtest summary as a text string."""
    if not results:
        return "No valid backtest results available."
    
    summary_lines = ["\n🧪 MOMENTUM BACKTEST RESULTS 🧪"]
    summary_lines.append(f"Strategy: Investing ${INVESTMENT_PER_COIN} in each of the top {len(results)} AI coins by 24h performance")
    summary_lines.append(f"Backtest period: {BACKTEST_DAYS} days")
    summary_lines.append("----------------------------------------")
    
    total_investment = INVESTMENT_PER_COIN * len(results)
    total_profit = sum(r['profit'] for r in results)
    avg_roi = sum(r['roi_percent'] for r in results) / len(results)
    
    for r in results:
        summary_lines.append(f"• {r['symbol']}: ROI {r['roi_percent']:.2f}%, Profit: ${r['profit']:.2f}")
    
    summary_lines.append("----------------------------------------")
    summary_lines.append(f"Total investment: ${total_investment:.2f}")
    summary_lines.append(f"Total profit/loss: ${total_profit:.2f}")
    summary_lines.append(f"Portfolio ROI: {(total_profit/total_investment)*100:.2f}%")
    summary_lines.append(f"Average coin ROI: {avg_roi:.2f}%")
    
    # Compare to Bitcoin as benchmark
    try:
        btc_data = get_historical_data('bitcoin', BACKTEST_DAYS+1)
        if btc_data is not None and len(btc_data) >= 2:
            btc_start = btc_data.iloc[0]['price']
            btc_end = btc_data.iloc[-1]['price']
            btc_roi = (btc_end / btc_start - 1) * 100
            summary_lines.append(f"Bitcoin ROI in same period: {btc_roi:.2f}%")
            summary_lines.append(f"Relative performance: {avg_roi - btc_roi:.2f}%")
    except Exception as e:
        summary_lines.append(f"Could not compare to Bitcoin benchmark: {e}")
    
    return "\n".join(summary_lines)

def print_backtest_summary(results):
    """Print a summary of the backtest results."""
    summary_text = get_backtest_summary_text(results)
    print(summary_text)

def generate_consolidated_summary(ai_summary, backtest_results, all_prices, top_symbols):
    """
    Generates a consolidated summary containing both the AI highlights, momentum backtest,
    and additional metrics including volatility insights.
    
    Args:
        ai_summary: The summary text from ai_highlights.generate_summary()
        backtest_results: The results from perform_momentum_backtest()
        all_prices: Historical price data for each coin
        top_symbols: Symbols of the top coins
        
    Returns:
        A string with the consolidated summary
    """
    backtest_summary = get_backtest_summary_text(backtest_results)
    
    # Get volatility insights
    volatility_insights = calculate_volatility_insights(all_prices, top_symbols)
    
    # Combine the summaries
    consolidated = f"{ai_summary}\n\n{backtest_summary}\n\n📊 VOLATILITY & PRICE ACTION INSIGHTS:\n"
    
    for insight in volatility_insights:
        consolidated += f"{insight}\n"
    
    consolidated += "\n📈 Performance charts have been generated."
    
    return consolidated

if __name__ == "__main__":
    print("Running Daily AI Altcoins Highlight...")
    market_data = ai_highlights.get_market_data()
    
    if not market_data:
        print("Failed to retrieve market data. Exiting.")
        exit(1)
    
    # Generate the AI highlights summary
    ai_summary = ai_highlights.generate_summary(market_data)
    print("\n" + ai_summary)
    
    # For backtesting, we need valid coins with price data
    valid_coins = []
    for coin in market_data:
        change_24h = coin.get('price_change_percentage_24h')
        price_usd = coin.get('current_price')
        if change_24h is not None and price_usd is not None:
            valid_coins.append(coin)
    
    # Sort by 24h price change (descending)
    valid_coins.sort(key=lambda x: x['price_change_percentage_24h'], reverse=True)
    
    # Take top 3 for the momentum backtest
    top_3_coins = valid_coins[:3]
    top_3_symbols = [coin.get('symbol', '').upper() for coin in top_3_coins]
    
    print(f"\nPerforming momentum backtest on top 3 coins: {', '.join(top_3_symbols)}")
    
    # Run the backtest
    backtest_results, price_data = perform_momentum_backtest(top_3_coins)
    
    # Display results
    print_backtest_summary(backtest_results)
    
    # Plot the performance
    if price_data:
        # Standard performance plot
        plot_performance(price_data, top_3_symbols)
        
        # Create equity curves with equal-weight basket
        plot_individual_equity_curves(price_data, top_3_symbols)
    
    # Generate the consolidated summary with additional metrics
    consolidated_summary = generate_consolidated_summary(
        ai_summary, 
        backtest_results,
        price_data,
        top_3_symbols
    )
    
    # Save consolidated summary to file
    with open("consolidated_summary.txt", "w") as f:
        f.write(consolidated_summary)
    print("\nConsolidated summary saved to consolidated_summary.txt")
    
    # Send consolidated summary to Discord
    print("Sending consolidated summary to Discord...")
    
    # First send the text summary
    ai_highlights.send_to_discord(consolidated_summary)
    
    # Function to send images to Discord
    def send_image_to_discord(image_path, message=""):
        webhook_url = ai_highlights.DISCORD_WEBHOOK_URL
        
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            print(f"Sending image {image_path} to Discord...")
            
            files = {'file': (image_path, image_data)}
            payload = {"content": message}
            
            response = requests.post(
                webhook_url,
                data=payload,
                files=files
            )
            response.raise_for_status()
            print(f"Successfully sent {image_path} to Discord!")
            return True
        except Exception as e:
            print(f"Error sending image to Discord: {e}")
            return False
    
    # Send the charts to Discord
    time.sleep(1)  # Pause to avoid rate limiting
    send_image_to_discord('equity_curves.png', "📈 Equity curves for each coin and equal-weight basket:") 