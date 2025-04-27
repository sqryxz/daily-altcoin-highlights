#!/usr/bin/env python3
"""
Utility script to prefetch historical data for top AI coins.
This helps avoid rate limits when running the main backtest.
"""

import sys
import os
import time
import random
import json
import requests
from datetime import datetime

# Add parent directory to path so we can import from ai_highlights
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_highlights import get_market_data

# Constants
CACHE_DIR = "Momentum Backtest/cache"
HISTORY_DAYS = 90
MAX_RETRIES = 5
MAX_COINS = 30  # Maximum number of coins to prefetch

def ensure_cache_dir():
    """Ensure cache directory exists"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_historical_prices_with_backoff(coin_id, days=HISTORY_DAYS, vs_currency="usd"):
    """
    Fetch historical price data with exponential backoff for rate limits
    """
    cache_file = f"{CACHE_DIR}/{coin_id}_history_{days}d.json"
    
    # Check if we already have cached data
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            cache_time = cache_data.get('timestamp', 0)
            
            # If cache is less than 24 hours old, skip
            if time.time() - cache_time < 24 * 3600:
                print(f"✅ {coin_id}: Cache is fresh (less than 24h old)")
                return True
                
            print(f"🔄 {coin_id}: Cache is stale, refreshing...")
        except Exception as e:
            print(f"⚠️ {coin_id}: Error reading cache: {e}")
    else:
        print(f"🆕 {coin_id}: No cache found, fetching new data...")
    
    # Fetch from API
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': vs_currency,
        'days': days,
        'interval': 'daily'
    }
    
    # Implement exponential backoff
    for retry in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params)
            
            # Handle rate limiting
            if response.status_code == 429:
                wait_time = 30 + 2 ** retry + random.random() * 10
                print(f"⏳ {coin_id}: Rate limited. Waiting {wait_time:.2f} seconds (retry {retry+1}/{MAX_RETRIES})...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            data = response.json()
            
            # Cache the results
            try:
                with open(cache_file, 'w') as f:
                    cache_content = {
                        'timestamp': time.time(),
                        'data': data
                    }
                    json.dump(cache_content, f)
                print(f"✅ {coin_id}: Data fetched and cached successfully")
                return True
            except Exception as e:
                print(f"⚠️ {coin_id}: Error caching data: {e}")
                return False
                
        except requests.exceptions.RequestException as e:
            if response.status_code == 429 and retry < MAX_RETRIES - 1:
                continue  # Already handled above
            elif retry < MAX_RETRIES - 1:
                wait_time = 10 + 2 ** retry + random.random() * 5
                print(f"⚠️ {coin_id}: Error: {e}. Retrying in {wait_time:.2f}s... ({retry+1}/{MAX_RETRIES})")
                time.sleep(wait_time)
            else:
                print(f"❌ {coin_id}: Failed after {MAX_RETRIES} retries: {e}")
                return False
        except Exception as e:
            print(f"❌ {coin_id}: Unexpected error: {e}")
            return False
    
    return False

def main():
    """Main function to prefetch data"""
    print(f"🔍 Prefetching historical data for top AI coins (started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    
    # Ensure cache directory exists
    ensure_cache_dir()
    
    # Get all AI coins
    market_data = get_market_data()
    if not market_data:
        print("❌ Failed to fetch AI coin market data. Exiting.")
        return
    
    # Sort by market cap
    market_data.sort(key=lambda x: x.get('market_cap', 0) if x.get('market_cap') else 0, reverse=True)
    
    # Take top N coins plus Bitcoin as benchmark
    top_coins = ["bitcoin"]  # Always include the benchmark
    
    # Add top coins by market cap
    for coin in market_data[:MAX_COINS]:
        coin_id = coin.get('id')
        if coin_id and coin_id not in top_coins:
            top_coins.append(coin_id)
    
    print(f"🎯 Selected {len(top_coins)} coins to prefetch, starting with Bitcoin as benchmark")
    
    # Fetch historical data for each coin
    success_count = 0
    for i, coin_id in enumerate(top_coins):
        print(f"[{i+1}/{len(top_coins)}] Fetching data for {coin_id}...")
        if get_historical_prices_with_backoff(coin_id):
            success_count += 1
        
        # Add a delay between requests to avoid rate limits
        if i < len(top_coins) - 1:
            delay = 2 + random.random() * 3
            print(f"⏳ Waiting {delay:.2f}s before next request...")
            time.sleep(delay)
    
    print(f"\n✅ Prefetch complete! Successfully cached data for {success_count}/{len(top_coins)} coins.")
    print(f"📊 Data ready for momentum backtest (finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")

if __name__ == "__main__":
    main() 