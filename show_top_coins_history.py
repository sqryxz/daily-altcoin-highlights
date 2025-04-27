import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
import ai_highlights

# Directory containing cached price data
CACHE_DIR = "cache"

def load_historical_data(coin_id):
    """Load historical price data from cache"""
    cache_file = f"{CACHE_DIR}/{coin_id}_114_days.json"
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            df = pd.DataFrame(cache_data.get('data'))
            
            # Convert date strings to datetime
            if 'date' in df.columns and isinstance(df['date'].iloc[0], str):
                df['date'] = pd.to_datetime(df['date'])
                
            return df
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading cache for {coin_id}: {e}")
    
    return None

def get_top_coins_by_day(days=14):
    """Get the top 3 performing AI coins for each of the past X days"""
    print(f"Analyzing top AI coins for the past {days} days...")
    
    # Get all AI coins from the module
    all_ai_coins = ai_highlights.get_market_data()
    if not all_ai_coins:
        print("Failed to get AI coins data. Exiting.")
        return None
    
    # End date is yesterday
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    start_date = end_date - timedelta(days=days-1)
    date_range = pd.date_range(start=start_date, end=end_date)
    
    # Dictionary to store top coins for each day
    top_coins_by_day = {date: [] for date in date_range}
    
    # Process each coin
    for coin in all_ai_coins:
        coin_id = coin.get('id')
        symbol = coin.get('symbol', '').upper()
        name = coin.get('name', '')
        
        # Load historical data
        hist_data = load_historical_data(coin_id)
        
        if hist_data is not None and len(hist_data) > 0:
            # Filter to the date range we want
            hist_data = hist_data[(hist_data['date'] >= start_date) & (hist_data['date'] <= end_date)]
            
            # Calculate daily returns
            hist_data['prev_price'] = hist_data['price'].shift(1)
            hist_data['return_24h'] = (hist_data['price'] / hist_data['prev_price']) - 1
            
            # Remove the first row which has NaN for return
            hist_data = hist_data.dropna()
            
            # Add each day's return to our dictionary
            for date, row in hist_data.iterrows():
                # Convert to datetime for comparison
                row_date = pd.to_datetime(row['date']).replace(hour=0, minute=0, second=0, microsecond=0)
                
                # Check if the date exists in our range
                if row_date in top_coins_by_day:
                    # Add coin with its return for this day
                    top_coins_by_day[row_date].append({
                        'id': coin_id,
                        'symbol': symbol,
                        'name': name,
                        'return_24h': row['return_24h']
                    })
    
    # For each day, sort coins by return and keep top 3
    for date in date_range:
        coins_for_day = top_coins_by_day[date]
        coins_for_day.sort(key=lambda x: x.get('return_24h', 0), reverse=True)
        top_coins_by_day[date] = coins_for_day[:3]  # Keep only top 3
    
    return top_coins_by_day

def print_top_coins_history(top_coins_by_day):
    """Print a formatted table of the top 3 coins for each day"""
    if not top_coins_by_day:
        print("No data available")
        return
    
    print("\n📅 HISTORICAL TOP 3 AI ALTCOINS BY DAILY PERFORMANCE 📅")
    print("=" * 80)
    print(f"{'Date':<12} | {'1st':<15} | {'2nd':<15} | {'3rd':<15}")
    print("-" * 80)
    
    for date in sorted(top_coins_by_day.keys()):
        coins = top_coins_by_day[date]
        date_str = date.strftime('%Y-%m-%d')
        
        # Format each coin as "SYMBOL (+XX.XX%)"
        coin_strings = []
        for i in range(3):
            if i < len(coins):
                coin = coins[i]
                coin_str = f"{coin['symbol']} ({coin['return_24h']*100:+.2f}%)"
                coin_strings.append(coin_str)
            else:
                coin_strings.append("N/A")
        
        print(f"{date_str:<12} | {coin_strings[0]:<15} | {coin_strings[1]:<15} | {coin_strings[2]:<15}")
    
    print("=" * 80)
    print("Note: Historical data is based on cached prices and may not be 100% accurate.")

if __name__ == "__main__":
    top_coins_by_day = get_top_coins_by_day(14)
    print_top_coins_history(top_coins_by_day) 