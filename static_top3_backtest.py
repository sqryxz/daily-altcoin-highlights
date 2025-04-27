import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import datetime, timedelta
import json
import os
import ai_highlights
import glob

# Constants
CACHE_DIR = "cache"
BACKTEST_DAYS = 90

def get_current_top_coins():
    """Get the current top 3 AI coins by 24H performance"""
    print("Fetching current top 3 AI coins...")
    
    # Get market data from ai_highlights
    market_data = ai_highlights.get_market_data()
    
    if not market_data:
        print("Failed to retrieve AI market data. Exiting.")
        return None
    
    # Filter and sort by 24h change
    valid_ai_coins = []
    for coin in market_data:
        change_24h = coin.get('price_change_percentage_24h')
        price_usd = coin.get('current_price')
        if change_24h is not None and price_usd is not None:
            valid_ai_coins.append(coin)
    
    if not valid_ai_coins:
        print("No valid AI coins found after filtering.")
        return None
    
    # Sort the valid AI coins by 24h price change (descending)
    valid_ai_coins.sort(key=lambda x: x['price_change_percentage_24h'], reverse=True)
    
    # Take top 3
    top_3_coins = valid_ai_coins[:3]
    top_3_symbols = [coin.get('symbol', '').upper() for coin in top_3_coins]
    
    print(f"Current top 3 AI coins: {', '.join(top_3_symbols)}")
    
    return top_3_coins

def find_cached_data_for_coin(coin_id):
    """Try to find cached data for a coin with various potential filenames"""
    # First, try the exact ID
    pattern = f"{CACHE_DIR}/{coin_id}_*.json"
    matches = glob.glob(pattern)
    
    if matches:
        # Sort by days (highest first to get the longest history)
        matches.sort(key=lambda x: int(x.split('_')[-2]) if x.split('_')[-2].isdigit() else 0, reverse=True)
        return matches[0]
    
    # If no matches, try to normalize and look for any partial matches
    normalized_id = coin_id.lower().replace('-', '').replace('_', '')
    all_cache_files = glob.glob(f"{CACHE_DIR}/*.json")
    
    potential_matches = []
    for cache_file in all_cache_files:
        file_id = os.path.basename(cache_file).split('_')[0].lower()
        if normalized_id in file_id or file_id in normalized_id:
            potential_matches.append(cache_file)
    
    if potential_matches:
        # Sort by days (highest first)
        potential_matches.sort(key=lambda x: int(x.split('_')[-2]) if x.split('_')[-2].isdigit() else 0, reverse=True)
        print(f"Found potential match for {coin_id}: {os.path.basename(potential_matches[0])}")
        return potential_matches[0]
    
    # Special cases for known naming differences
    special_cases = {
        'fomo-3': 'fomo-3',
        'billy-bets-by-virtuals': 'billy-bets-by-virtuals',
        'nani': 'nani'
    }
    
    if coin_id in special_cases:
        # Try again with the special case
        alt_pattern = f"{CACHE_DIR}/{special_cases[coin_id]}_*.json"
        alt_matches = glob.glob(alt_pattern)
        if alt_matches:
            alt_matches.sort(key=lambda x: int(x.split('_')[-2]) if x.split('_')[-2].isdigit() else 0, reverse=True)
            print(f"Found special case match for {coin_id}: {os.path.basename(alt_matches[0])}")
            return alt_matches[0]
    
    print(f"No cached data found for {coin_id}")
    return None

def get_historical_data(coin_id, days):
    """Load historical price data from cache"""
    cache_file = find_cached_data_for_coin(coin_id)
    
    if cache_file and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            df = pd.DataFrame(cache_data.get('data'))
            
            # Convert date strings to datetime
            if isinstance(df['date'].iloc[0], str):
                df['date'] = pd.to_datetime(df['date'])
                
            return df
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading cache for {coin_id}: {e}")
    
    # If we're here, we couldn't find a valid cache file
    # List available cache files for debugging
    print(f"Available cache files:")
    for f in glob.glob(f"{CACHE_DIR}/*.json")[:10]:  # Show first 10
        print(f"  - {os.path.basename(f)}")
    
    if len(glob.glob(f"{CACHE_DIR}/*.json")) > 10:
        print(f"  - ... and {len(glob.glob(f'{CACHE_DIR}/*.json'))-10} more")
    
    return None

def run_static_backtest(total_days=BACKTEST_DAYS):
    """
    Run a backtest that just holds the current top 3 AI coins for the entire period.
    
    Args:
        total_days: Number of days to backtest (default: 90)
    
    Returns:
        Tuple of (portfolio_performance, coin_performances)
    """
    print(f"Backtesting static portfolio of current top 3 AI coins for {total_days} days...")
    
    # Get current top AI coins
    top_coins = get_current_top_coins()
    
    if not top_coins:
        print("No top AI coins available. Exiting.")
        return None, None
    
    # Get historical data for the top coins
    coin_data = {}
    
    for coin in top_coins:
        coin_id = coin.get('id')
        symbol = coin.get('symbol', '').upper()
        
        hist_data = get_historical_data(coin_id, total_days + 10)  # Add buffer
        
        if hist_data is not None and len(hist_data) > 7:  # Need at least a week of data
            # Convert date column back to datetime if needed
            if isinstance(hist_data['date'].iloc[0], str):
                hist_data['date'] = pd.to_datetime(hist_data['date'])
                
            coin_data[coin_id] = {
                'symbol': symbol,
                'data': hist_data
            }
    
    if not coin_data:
        print("No historical data available. Exiting.")
        return None, None
    
    # Set up date range for the backtest
    start_date = datetime.now() - timedelta(days=total_days)
    dates = pd.date_range(start=start_date, periods=total_days)
    
    # Set up portfolio and coin performance tracking
    portfolio = pd.DataFrame(index=dates)
    portfolio['value'] = 100.0  # Start with $100
    
    coin_performances = {}
    for coin_id, coin_info in coin_data.items():
        symbol = coin_info['symbol']
        coin_performances[symbol] = pd.DataFrame(index=dates)
        coin_performances[symbol]['value'] = 100.0
    
    # Calculate performance for each coin and portfolio over time
    for i, current_date in enumerate(dates):
        coin_values = []
        
        for coin_id, coin_info in coin_data.items():
            symbol = coin_info['symbol']
            price_data = coin_info['data']
            
            # Filter data up to current date
            price_data_until_now = price_data[price_data['date'] <= current_date]
            
            if len(price_data_until_now) > 0:
                start_price = price_data.iloc[0]['price']
                current_price = price_data_until_now.iloc[-1]['price']
                coin_value = 100 * (current_price / start_price)
                
                coin_performances[symbol].loc[current_date, 'value'] = coin_value
                coin_values.append(coin_value)
        
        # Portfolio is equal weight
        if coin_values:
            portfolio.loc[current_date, 'value'] = sum(coin_values) / len(coin_values)
    
    return portfolio, coin_performances

def plot_performance(portfolio, coin_performances):
    """Plot the performance of the static portfolio and individual coins"""
    plt.figure(figsize=(12, 8))
    
    # Plot individual coin performances
    for symbol, performance in coin_performances.items():
        plt.plot(performance.index, performance['value'], alpha=0.7, linewidth=1.5, label=symbol)
    
    # Plot portfolio performance with thicker line
    plt.plot(portfolio.index, portfolio['value'], 'k-', linewidth=2.5, label='Equal-Weight Portfolio')
    
    plt.title('Static Portfolio of Current Top 3 AI Altcoins')
    plt.xlabel('Date')
    plt.ylabel('Value ($)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Add annotations for key metrics
    start_value = 100
    end_value = portfolio['value'].iloc[-1]
    total_return = ((end_value / start_value) - 1) * 100
    
    plt.annotate(f'Total Return: {total_return:.1f}%', 
                 xy=(0.02, 0.95), xycoords='axes fraction',
                 fontsize=12, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
    
    # Calculate max drawdown
    max_drawdown = ((portfolio['value'] / portfolio['value'].cummax()) - 1).min() * 100
    plt.annotate(f'Max Drawdown: {max_drawdown:.1f}%', 
                 xy=(0.02, 0.89), xycoords='axes fraction',
                 fontsize=12, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
    
    # Save the figure
    plt.savefig('static_top3_performance.png')
    print("Performance plot saved as 'static_top3_performance.png'")
    plt.close()

def prepare_summary(portfolio, coin_performances):
    """Prepare a summary of the static portfolio performance"""
    start_value = 100
    end_value = portfolio['value'].iloc[-1]
    total_return = ((end_value / start_value) - 1) * 100
    max_drawdown = ((portfolio['value'] / portfolio['value'].cummax()) - 1).min() * 100
    
    # Calculate volatility (annualized)
    portfolio['daily_return'] = portfolio['value'].pct_change()
    volatility = portfolio['daily_return'].std() * np.sqrt(365) * 100
    
    # Coin stats
    coin_stats = []
    for symbol, performance in coin_performances.items():
        end_val = performance['value'].iloc[-1]
        coin_return = ((end_val / start_value) - 1) * 100
        max_dd = ((performance['value'] / performance['value'].cummax()) - 1).min() * 100
        
        coin_stats.append({
            'symbol': symbol,
            'return': coin_return,
            'max_drawdown': max_dd
        })
    
    # Generate summary
    summary = "\n===== STATIC TOP 3 AI COINS PORTFOLIO SUMMARY =====\n\n"
    summary += f"Portfolio of current top 3 AI coins by 24H performance\n"
    summary += f"Backtest period: Past {BACKTEST_DAYS} days\n\n"
    
    summary += "PERFORMANCE METRICS:\n"
    summary += f"- Equal-Weight Portfolio Return: {total_return:.1f}%\n"
    summary += f"- Maximum Drawdown: {max_drawdown:.1f}%\n"
    summary += f"- Annualized Volatility: {volatility:.1f}%\n\n"
    
    summary += "INDIVIDUAL COIN PERFORMANCE:\n"
    for stat in coin_stats:
        summary += f"- {stat['symbol']}: {stat['return']:.1f}% (Max Drawdown: {stat['max_drawdown']:.1f}%)\n"
    
    # Compare with dynamic strategy
    summary += "\nCOMPARISON WITH DYNAMIC STRATEGY:\n"
    summary += "- The static strategy holds the current top 3 coins for the entire period\n"
    summary += "- The dynamic strategy rebalances daily to the new top 3 coins\n"
    summary += "- The static approach has much lower transaction costs (only 3 trades)\n"
    summary += "- The static approach is more exposed to individual coin risks\n"
    
    summary += "\nPerformance chart saved as 'static_top3_performance.png'\n"
    
    return summary

if __name__ == "__main__":
    # First, let's look at what cache files we have
    print("Available cache files:")
    for f in sorted(glob.glob(f"{CACHE_DIR}/*.json"))[:10]:
        print(f"  - {os.path.basename(f)}")
    
    if len(glob.glob(f"{CACHE_DIR}/*.json")) > 10:
        print(f"  - ... and {len(glob.glob(f'{CACHE_DIR}/*.json'))-10} more")
    
    portfolio, coin_performances = run_static_backtest()
    
    if portfolio is None:
        print("Backtest failed. Exiting.")
        exit(1)
    
    # Plot the results
    plot_performance(portfolio, coin_performances)
    
    # Generate and display summary
    summary = prepare_summary(portfolio, coin_performances)
    print(summary)
    
    # Save summary to file
    with open("static_top3_summary.txt", "w") as f:
        f.write(summary)
    print("Summary saved to 'static_top3_summary.txt'") 