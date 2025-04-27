import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import datetime, timedelta
import json
import os
import random
import ai_highlights  # Import the AI highlights module

# Constants
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/markets"
COINGECKO_HISTORY_URL = "https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
CACHE_FILE = "coingecko_cache.json"
CACHE_DIR = "cache"
BACKTEST_DAYS = 90  # Backtest for 90 days
LOOK_BACK_WINDOW = 7  # 7-day return for entry
TRAILING_WINDOW = 14  # 14-day return for exit condition
REQUEST_DELAY = 3  # Seconds to wait between API requests

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_ai_top_coins():
    """Get the top AI coins from the ai_highlights module"""
    print("Fetching top AI coins from ai_highlights...")
    
    # Get market data from ai_highlights
    market_data = ai_highlights.get_market_data()
    
    if not market_data:
        print("Failed to retrieve AI market data. Exiting.")
        return None
    
    # Filter out coins with missing data needed for sorting
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
    
    # Take top 3 for the momentum backtest
    top_3_coins = valid_ai_coins[:3]
    top_3_symbols = [coin.get('symbol', '').upper() for coin in top_3_coins]
    
    print(f"Top 3 AI coins for momentum strategy: {', '.join(top_3_symbols)}")
    
    return top_3_coins

def get_historical_data(coin_id, days):
    """
    Fetch historical price data for a given coin from CoinGecko.
    Uses local caching to avoid excessive API calls.
    """
    cache_file = f"{CACHE_DIR}/{coin_id}_{days}_days.json"
    
    # Check if we have cached data
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            cached_time = cache_data.get('timestamp', 0)
            # Use cache if it's less than 24 hours old
            if time.time() - cached_time < 24 * 3600:
                print(f"Using cached data for {coin_id}")
                return pd.DataFrame(cache_data.get('data'))
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading cache for {coin_id}: {e}")
    
    print(f"Fetching {days} days of historical data for {coin_id}...")
    
    params = {
        'vs_currency': 'usd',
        'days': days,
        'interval': 'daily'
    }
    
    try:
        # Add a longer delay to respect rate limits
        time.sleep(REQUEST_DELAY + random.uniform(0.5, 1.5))
        
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
        
        # Save to cache
        try:
            with open(cache_file, 'w') as f:
                # Convert date to string to avoid JSON serialization issues
                df_to_save = df.copy()
                df_to_save['date'] = df_to_save['date'].astype(str)
                
                cache_content = {
                    'timestamp': time.time(),
                    'data': df_to_save.to_dict('records')
                }
                json.dump(cache_content, f)
            print(f"Cached data for {coin_id}")
        except IOError as e:
            print(f"Error writing cache for {coin_id}: {e}")
        
        return df
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching historical data for {coin_id}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error with {coin_id}: {e}")
        return None

def calculate_returns(price_df, window):
    """Calculate the rolling returns for a given window period."""
    if price_df is None or len(price_df) <= window:
        return None
    
    df = price_df.copy()
    df['return'] = df['price'].pct_change(window)
    return df

def run_momentum_strategy(total_days=BACKTEST_DAYS):
    """
    Implements the momentum strategy:
    - Entry: Go long on the top 3 AI coins by 24H performance
    - Exit: Close when either (a) the coin drops out of the daily top-three list by 24H performance 
           or (b) its trailing 14-day return turns negative
    
    Args:
        total_days: Number of days to backtest (default: 90)
    
    Returns:
        Tuple of (portfolio_performance, all_coin_performances, insights)
    """
    print(f"Backtesting momentum strategy for {total_days} days...")
    
    # We need to fetch more days of data to calculate returns properly
    fetch_days = total_days + TRAILING_WINDOW + 10  # Add buffer
    
    # Get current top AI coins to start with
    top_coins = get_ai_top_coins()
    
    if not top_coins:
        print("No top AI coins available. Exiting.")
        return None, None, None
    
    # Get historical data for all AI coins in the dataset to simulate daily rankings
    all_ai_coins = ai_highlights.get_market_data()
    if not all_ai_coins:
        print("Failed to get all AI coins data. Exiting.")
        return None, None, None
    
    # Filter valid coins
    valid_ai_coins = []
    for coin in all_ai_coins:
        if coin.get('price_change_percentage_24h') is not None and coin.get('current_price') is not None:
            valid_ai_coins.append(coin)
    
    # Get historical data for all valid AI coins
    all_historical_data = {}
    for coin in valid_ai_coins:
        coin_id = coin.get('id')
        symbol = coin.get('symbol', '').upper()
        
        hist_data = get_historical_data(coin_id, fetch_days)
        if hist_data is not None and len(hist_data) > TRAILING_WINDOW:
            # Convert date column back to datetime if it's a string
            if isinstance(hist_data['date'].iloc[0], str):
                hist_data['date'] = pd.to_datetime(hist_data['date'])
                
            all_historical_data[coin_id] = {
                'symbol': symbol,
                'data': hist_data
            }
    
    if not all_historical_data:
        print("No historical data available for any AI coins. Exiting.")
        return None, None, None
    
    # Start from the earliest date that allows for calculating the required returns
    start_date = datetime.now() - timedelta(days=total_days)
    dates = pd.date_range(start=start_date, periods=total_days)
    
    # Track portfolio performance
    portfolio = pd.DataFrame(index=dates)
    portfolio['value'] = 100.0  # Start with $100
    
    # Track individual coin performances
    coin_performances = {}
    for coin_id, coin_info in all_historical_data.items():
        symbol = coin_info['symbol']
        coin_performances[symbol] = pd.DataFrame(index=dates)
        coin_performances[symbol]['value'] = 100.0
        coin_performances[symbol]['in_portfolio'] = False
    
    # Active positions
    active_positions = {}  # {coin_id: entry_price}
    coins_in_portfolio = []  # List to keep track of which coins are in the portfolio
    
    # For each day in the backtest period
    for i, current_date in enumerate(dates):
        # Calculate daily returns for all coins to determine top 3 by 24H performance
        day_returns = {}
        for coin_id, coin_info in all_historical_data.items():
            symbol = coin_info['symbol']
            price_data = coin_info['data']
            
            # Filter data up to current date
            price_data_until_now = price_data[price_data['date'] <= current_date]
            
            if len(price_data_until_now) >= 2:  # Need at least 2 days for 24H return
                latest_price = price_data_until_now.iloc[-1]['price']
                prev_price = price_data_until_now.iloc[-2]['price']
                return_24h = (latest_price / prev_price) - 1
                
                # Calculate 14-day return for exit condition
                if len(price_data_until_now) > TRAILING_WINDOW:
                    price_14d_ago = price_data_until_now.iloc[-TRAILING_WINDOW-1]['price']
                    return_14d = (latest_price / price_14d_ago) - 1
                else:
                    return_14d = None
                
                # Only include coins with positive 24H returns for entry
                if return_24h > 0:
                    day_returns[coin_id] = {
                        'symbol': symbol,
                        'return_24h': return_24h,
                        'return_14d': return_14d,
                        'current_price': latest_price
                    }
        
        # Sort by 24H return to get top 3
        sorted_coins = sorted(
            day_returns.keys(),
            key=lambda x: day_returns[x]['return_24h'],
            reverse=True
        )
        
        # Top 3 coins for the day based on 24H return
        top_3_for_day = sorted_coins[:3] if len(sorted_coins) >= 3 else sorted_coins
        
        # Exit positions that are no longer in top 3 or have negative 14-day returns
        coins_to_exit = []
        for coin_id in active_positions:
            # Exit if coin drops out of top 3
            if coin_id not in top_3_for_day:
                coins_to_exit.append(coin_id)
            # Exit if 14-day return becomes negative
            elif coin_id in day_returns and day_returns[coin_id]['return_14d'] is not None:
                if day_returns[coin_id]['return_14d'] < 0:
                    coins_to_exit.append(coin_id)
        
        for coin_id in coins_to_exit:
            if coin_id in active_positions:
                entry_price = active_positions[coin_id]
                symbol = all_historical_data[coin_id]['symbol']
                print(f"Exiting position in {symbol} on {current_date.strftime('%Y-%m-%d')}")
                coin_performances[symbol].loc[current_date, 'in_portfolio'] = False
                coins_in_portfolio.remove(coin_id)
                del active_positions[coin_id]
        
        # Enter new positions for coins in top 3 that we don't already hold
        for coin_id in top_3_for_day:
            if coin_id not in active_positions and coin_id in day_returns:
                current_price = day_returns[coin_id]['current_price']
                symbol = all_historical_data[coin_id]['symbol']
                print(f"Entering position in {symbol} on {current_date.strftime('%Y-%m-%d')}")
                active_positions[coin_id] = current_price
                coins_in_portfolio.append(coin_id)
                coin_performances[symbol].loc[current_date, 'in_portfolio'] = True
        
        # Update performance for all coins we're tracking
        for coin_id, coin_info in all_historical_data.items():
            symbol = coin_info['symbol']
            price_data = coin_info['data']
            
            price_data_until_now = price_data[price_data['date'] <= current_date]
            if len(price_data_until_now) > 0:
                start_price = price_data.iloc[0]['price']
                current_price = price_data_until_now.iloc[-1]['price']
                coin_value = 100 * (current_price / start_price)
                coin_performances[symbol].loc[current_date, 'value'] = coin_value
        
        # Update portfolio value (equal weight)
        if active_positions:
            portfolio_coins_performance = 0
            for coin_id in active_positions:
                symbol = all_historical_data[coin_id]['symbol']
                portfolio_coins_performance += coin_performances[symbol].loc[current_date, 'value']
            
            # Average performance of active positions
            portfolio.loc[current_date, 'value'] = portfolio_coins_performance / len(active_positions)
        else:
            # If no positions, use previous value
            if i > 0:
                portfolio.loc[current_date, 'value'] = portfolio.iloc[i-1]['value']
    
    # Filter coin performances to only those that were actually in the portfolio at some point
    portfolio_coins = {}
    for coin_id, coin_info in all_historical_data.items():
        symbol = coin_info['symbol']
        if coin_performances[symbol]['in_portfolio'].any():
            portfolio_coins[symbol] = coin_performances[symbol]
    
    # Generate insights about volatility and sharp reversals
    insights = generate_insights(portfolio, portfolio_coins)
    
    return portfolio, portfolio_coins, insights

def generate_insights(portfolio, coin_performances):
    """
    Generate insights about volatility spikes and sharp reversals
    
    Args:
        portfolio: DataFrame with portfolio performance
        coin_performances: Dictionary of DataFrames with individual coin performances
    
    Returns:
        List of insight strings
    """
    insights = []
    
    # Calculate daily returns for portfolio
    portfolio['daily_return'] = portfolio['value'].pct_change()
    
    # Look for volatility spikes
    portfolio_volatility = portfolio['daily_return'].rolling(window=7).std() * np.sqrt(365)
    mean_vol = portfolio_volatility.mean()
    high_vol_days = portfolio_volatility[portfolio_volatility > 2 * mean_vol]
    
    if not high_vol_days.empty:
        highest_vol_date = high_vol_days.idxmax()
        insights.append(f"• Volatility spike detected around {highest_vol_date.strftime('%Y-%m-%d')} with volatility {high_vol_days.max():.2f}, which is {high_vol_days.max()/mean_vol:.1f}x the average. This may have been caused by significant market movements affecting multiple coins simultaneously.")
    
    # Look for sharp reversals
    for symbol, performance in coin_performances.items():
        performance['daily_return'] = performance['value'].pct_change()
        
        # Find consecutive days with opposite sign returns
        performance['prev_return'] = performance['daily_return'].shift(1)
        performance['reversal'] = (performance['daily_return'] * performance['prev_return']) < 0
        performance['reversal_size'] = abs(performance['daily_return']) + abs(performance['prev_return'])
        
        # Find significant reversals while in portfolio
        significant_reversals = performance[
            (performance['reversal']) & 
            (performance['reversal_size'] > 0.1) & 
            (performance['in_portfolio'])
        ]
        
        if not significant_reversals.empty:
            largest_reversal = significant_reversals['reversal_size'].idxmax()
            insights.append(f"• Sharp reversal detected in {symbol} on {largest_reversal.strftime('%Y-%m-%d')} with a swing of {significant_reversals.loc[largest_reversal, 'reversal_size']*100:.1f}%. This coincided with a drop in portfolio value of {portfolio.loc[largest_reversal:largest_reversal+timedelta(days=2), 'daily_return'].sum()*100:.1f}% over the next 48 hours.")
            break  # Just report one major reversal
    
    # If we don't have enough insights yet, look for strong market moves
    if len(insights) < 2:
        largest_daily_gains = portfolio['daily_return'].nlargest(1)
        if not largest_daily_gains.empty:
            best_day = largest_daily_gains.index[0]
            insights.append(f"• Strongest single-day gain occurred on {best_day.strftime('%Y-%m-%d')} with a {largest_daily_gains.iloc[0]*100:.1f}% increase in portfolio value. This represents the momentum strategy capturing a strong uptrend in the top-performing coins.")
    
    # If still not enough insights, add general observation
    if len(insights) < 2:
        max_drawdown = ((portfolio['value'] / portfolio['value'].cummax()) - 1).min() * 100
        insights.append(f"• The strategy experienced a maximum drawdown of {max_drawdown:.1f}%, demonstrating the risk of momentum-based approaches when market trends reverse quickly.")
        
    return insights[:3]  # Limit to top 3 insights

def plot_performance(portfolio, coin_performances):
    """
    Plot the performance of the portfolio and individual coins
    
    Args:
        portfolio: DataFrame with portfolio performance
        coin_performances: Dictionary of DataFrames with individual coin performances
    
    Returns:
        None (saves plot to file)
    """
    plt.figure(figsize=(12, 8))
    
    # Plot individual coin performances
    for symbol, performance in coin_performances.items():
        plt.plot(performance.index, performance['value'], alpha=0.5, linewidth=1, label=symbol)
    
    # Plot portfolio performance with thicker line
    plt.plot(portfolio.index, portfolio['value'], 'k-', linewidth=2.5, label='Equal-Weight Portfolio')
    
    plt.title('AI Altcoin Momentum Strategy Performance (Top 3 by 24H)')
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
    
    # Save the figure
    plt.savefig('ai_momentum_strategy_plot.png')
    print("Performance plot saved as 'ai_momentum_strategy_plot.png'")
    plt.close()

def prepare_forum_post(portfolio, coin_performances, insights):
    """
    Prepare a forum post with the strategy description, performance, and insights
    
    Args:
        portfolio: DataFrame with portfolio performance
        coin_performances: Dictionary of DataFrames with individual coin performances
        insights: List of insight strings
    
    Returns:
        String with the forum post content
    """
    start_value = 100
    end_value = portfolio['value'].iloc[-1]
    total_return = ((end_value / start_value) - 1) * 100
    
    # Prepare statistics for each coin
    coin_stats = []
    for symbol, performance in coin_performances.items():
        end_val = performance['value'].iloc[-1]
        coin_return = ((end_val / start_value) - 1) * 100
        max_val = performance['value'].max()
        max_drawdown = ((performance['value'] / performance['value'].cummax()) - 1).min() * 100
        
        coin_stats.append({
            'symbol': symbol,
            'return': coin_return,
            'max_value': max_val,
            'max_drawdown': max_drawdown
        })
    
    # Sort coins by return
    coin_stats.sort(key=lambda x: x['return'], reverse=True)
    
    # Generate post content
    post = "# 📈 AI Altcoin Momentum Strategy Backtest 📉\n\n"
    
    post += "## Strategy Description\n\n"
    post += "I've backtested a simple momentum strategy on the top AI altcoins with the following rules:\n\n"
    post += "- **Look-back window:** Daily rebalancing based on 24H performance\n"
    post += "- **Entry criteria:** Go long on the top three AI coins by 24-hour performance\n"
    post += "- **Exit criteria:** Close the position when either (a) the coin drops out of the daily top-three list or (b) its trailing 14-day return turns negative\n"
    post += f"- **Backtest period:** Past {BACKTEST_DAYS} days\n\n"
    
    post += "## Performance Summary\n\n"
    post += f"- **Equal-Weight Portfolio Return:** {total_return:.1f}%\n"
    post += "- **Individual Coin Performance:**\n"
    
    for stat in coin_stats:
        post += f"  - {stat['symbol']}: {stat['return']:.1f}% (Max Drawdown: {stat['max_drawdown']:.1f}%)\n"
    
    post += "\n## Key Insights\n\n"
    for insight in insights:
        post += f"{insight}\n\n"
    
    post += "## Notes\n\n"
    post += "- The strategy is fully systematic and requires daily rebalancing\n"
    post += "- This approach targets the most volatile AI altcoins with strong daily momentum\n" 
    post += "- No transaction costs or slippage were included in this backtest\n" 
    post += "- The strategy focuses exclusively on AI-related cryptocurrencies\n"
    post += "- Past performance is not indicative of future results\n\n"
    
    post += "If you found this analysis helpful, tips are appreciated! 🙏\n"
    
    return post

if __name__ == "__main__":
    # Run the momentum strategy on top AI coins
    portfolio_performance, coin_performances, insights = run_momentum_strategy()
    
    if portfolio_performance is None:
        print("Strategy backtest failed. Exiting.")
        exit(1)
    
    # Plot the results
    plot_performance(portfolio_performance, coin_performances)
    
    # Display insights
    print("\n🔍 Key Insights:")
    for insight in insights:
        print(insight)
    
    # Prepare forum post
    forum_post = prepare_forum_post(portfolio_performance, coin_performances, insights)
    
    # Save forum post to file
    with open("ai_momentum_strategy_post.md", "w") as f:
        f.write(forum_post)
    print("\nForum post saved to 'ai_momentum_strategy_post.md'") 