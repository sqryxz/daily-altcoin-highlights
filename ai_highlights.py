import requests
import json
import time
import os
from datetime import datetime, timedelta
from statistics import median

# --- Constants ---
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/coins/markets"
CRYPTORANK_API_URL = "https://api.cryptorank.io/v1/coins"
CACHE_FILE = "coingecko_cache.json"
CACHE_TTL_SECONDS = 23 * 3600 + 55 * 60 # 23 hours 55 minutes
TOP_N_COINS = 5
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1362469269769814238/-EyJ_fSmcjSYvIFgV7V0Nc5YeTSQ0QNVg8paMNpjUzTmEpMwCOEFowPbkAkEZvfVKOtT"

# Blacklist of coins that might be incorrectly categorized as AI
NON_AI_COINS_BLACKLIST = [
    "pudgy-penguins",
    "popcat",
    "pepe",
    "dogecoin",
    "shiba-inu",
    "floki",
    "bonk",
    "wojak",
    "memecoin"
    # Add more as needed
]

def get_market_data_from_api():
    """Fetches AI coin market data from CoinGecko API."""
    print("Fetching fresh market data from CoinGecko API (with AI category filter)...")
    params = {
        'vs_currency': 'usd',
        'category': 'artificial-intelligence',
        'order': 'market_cap_desc',
        'per_page': 250,
        'page': 1,
        'sparkline': 'false',
        'price_change_percentage': '24h'
    }
    try:
        response = requests.get(COINGECKO_API_URL, params=params)
        response.raise_for_status()
        print("Successfully fetched market data.")
        
        # Filter out non-AI coins from the response
        data = response.json()
        filtered_data = [coin for coin in data if coin.get('id') not in NON_AI_COINS_BLACKLIST]
        
        if len(data) != len(filtered_data):
            print(f"Filtered out {len(data) - len(filtered_data)} non-AI coins that were incorrectly categorized.")
        
        return filtered_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching market data from CoinGecko: {e}")
        print("Attempting fallback to CryptoRank...")
        return get_cryptorank_fallback()
    except json.JSONDecodeError:
        print("Error decoding JSON response from CoinGecko.")
        return get_cryptorank_fallback()

def get_cryptorank_fallback():
    """Fallback to CryptoRank API if CoinGecko fails."""
    print("Using CryptoRank API as fallback...")
    params = {
        'category': 'AI',
        'limit': 100,
        'sort': 'rank'
    }
    try:
        response = requests.get(CRYPTORANK_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Transform CryptoRank data to match CoinGecko format for our needs
        transformed_data = []
        if 'data' in data:
            for coin in data['data']:
                coin_id = coin.get('slug', '').lower()
                
                # Skip blacklisted coins
                if coin_id in NON_AI_COINS_BLACKLIST:
                    continue
                    
                transformed_coin = {
                    'id': coin_id,
                    'symbol': coin.get('symbol', ''),
                    'name': coin.get('name', ''),
                    'current_price': coin.get('price', {}).get('USD', 0),
                    'total_volume': coin.get('volume24h', {}).get('USD', 0),
                    'price_change_percentage_24h': coin.get('priceChange', {}).get('24h', 0)
                }
                transformed_data.append(transformed_coin)
            
            print(f"Successfully fetched {len(transformed_data)} coins from CryptoRank.")
            return transformed_data
        return None
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError) as e:
        print(f"Error with CryptoRank fallback: {e}")
        return None

def load_from_cache():
    """Loads data from cache file if it exists and is valid."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
            timestamp = cache_data.get('timestamp', 0)
            if time.time() - timestamp < CACHE_TTL_SECONDS:
                print("Loading market data from cache...")
                cached_data = cache_data.get('data')
                
                # Apply blacklist to cached data as well
                filtered_cached_data = [coin for coin in cached_data if coin.get('id') not in NON_AI_COINS_BLACKLIST]
                if len(cached_data) != len(filtered_cached_data):
                    print(f"Filtered out {len(cached_data) - len(filtered_cached_data)} non-AI coins from cache.")
                
                return filtered_cached_data
            else:
                print("Cache expired.")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading cache file: {e}. Fetching new data.")
    else:
        print("Cache file not found.")
    return None

def save_to_cache(data):
    """Saves data to the cache file with a timestamp."""
    try:
        with open(CACHE_FILE, 'w') as f:
            cache_content = {
                'timestamp': time.time(),
                'data': data
            }
            json.dump(cache_content, f)
        print("Market data saved to cache.")
    except IOError as e:
        print(f"Error writing to cache file: {e}")

def get_market_data():
    """
    Fetches AI market data, using cache if available and valid.
    """
    cached_data = load_from_cache()
    if cached_data:
        return cached_data

    api_data = get_market_data_from_api()
    if api_data:
        save_to_cache(api_data)
    return api_data

def generate_summary(ai_market_data):
    """
    Generates a summary string for AI coins, finding the top N movers.
    """
    if not ai_market_data:
        return "Could not retrieve market data for AI altcoin highlights."

    # Filter out coins with missing data needed for sorting/display
    valid_ai_coins = []
    for coin in ai_market_data:
        change_24h = coin.get('price_change_percentage_24h')
        price_usd = coin.get('current_price')
        volume_24h = coin.get('total_volume')
        if change_24h is not None and price_usd is not None and volume_24h is not None:
            valid_ai_coins.append(coin)
        else:
            missing = []
            if change_24h is None: missing.append('24h change')
            if price_usd is None: missing.append('price')
            if volume_24h is None: missing.append('volume')
            print(f"Warning: Missing {', '.join(missing)} for AI coin {coin.get('id', 'unknown')}. Skipping.")

    if not valid_ai_coins:
        return "No AI coins with required fields (price, 24h change, volume) found after filtering."

    # Sort the valid AI coins by 24h price change (descending)
    valid_ai_coins.sort(key=lambda x: x['price_change_percentage_24h'], reverse=True)

    top_ai_coins = valid_ai_coins[:TOP_N_COINS]

    summary_lines = [f"📈 Daily AI Altcoin Highlights ({datetime.now().strftime('%Y-%m-%d')}) 📉\n"]
    summary_lines.append(f"🚀 Top {len(top_ai_coins)} AI Movers (by 24h % Change):")

    changes_24h = [c['price_change_percentage_24h'] for c in valid_ai_coins]

    for coin in top_ai_coins:
        coin_id = coin.get('id', 'N/A')
        symbol = coin.get('symbol', 'N/A').upper()
        price_usd = coin['current_price']
        change_24h = coin['price_change_percentage_24h']
        volume_24h = coin['total_volume']

        formatted_price = f"${price_usd:,.4f}"
        formatted_change = f"{change_24h:.2f}%"
        formatted_volume = f"${volume_24h:,.0f}"

        summary_lines.append(
            f"- {symbol} ({coin_id.capitalize()}): Price: {formatted_price}, 24h Change: {formatted_change}, 24h Vol: {formatted_volume}"
        )

    # Add quick stats based on the valid AI coins
    if changes_24h:
         median_change = median(changes_24h)
         worst_performer = min(valid_ai_coins, key=lambda x: x['price_change_percentage_24h'])
         worst_change = worst_performer['price_change_percentage_24h']
         worst_symbol = worst_performer.get('symbol', 'N/A').upper()

         summary_lines.append("\n📊 Quick Stats (for AI coins):")
         summary_lines.append(f"- Median 24h Change: {median_change:.2f}%")
         summary_lines.append(f"- Worst Performer: {worst_symbol} ({worst_change:.2f}%)")
    else:
         summary_lines.append("\n📊 Quick Stats: Not available (no valid AI coins found).")

    return "\n".join(summary_lines)

def send_to_discord(summary):
    """
    Sends the generated summary to a Discord channel via webhook.
    """
    print("Sending summary to Discord...")
    
    # Prepare the payload
    payload = {
        "content": summary,
        "username": "AI Altcoin Highlights"
    }
    
    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload
        )
        response.raise_for_status()
        print("Successfully sent summary to Discord!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending to Discord: {e}")
        return False

if __name__ == "__main__":
    print("Fetching AI coin market data (using cache if available)...")
    market_data = get_market_data() # Fetches AI market data with category filter
    if market_data:
        summary = generate_summary(market_data)
        print("\n" + summary)
        
        # Send to Discord webhook
        send_to_discord(summary)
    else:
        print("Failed to generate summary due to market data fetch error or no valid data.") 