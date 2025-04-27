import requests
import json
import sys
import time
import random

def retry_with_exponential_backoff(func, max_retries=3, base_delay=1, max_delay=16, jitter=0.1):
    """
    Retry a function with exponential backoff
    
    Args:
        func: The function to retry
        max_retries: Maximum number of retries
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        jitter: Random jitter factor to add to delay
        
    Returns:
        The result of the function call, or None if all retries failed
    """
    retries = 0
    delay = base_delay
    
    while retries <= max_retries:
        try:
            return func()
        except requests.exceptions.RequestException as e:
            retries += 1
            
            # If we've exhausted all retries or it's a 4xx error (except 429), don't retry
            if retries > max_retries or (hasattr(e, 'response') and 400 <= e.response.status_code < 500 and e.response.status_code != 429):
                print(f"Error after {retries} retries: {e}")
                return None
            
            # Add random jitter to avoid thundering herd problem
            jitter_amount = random.uniform(-jitter, jitter)
            actual_delay = min(delay * (1 + jitter_amount), max_delay)
            
            print(f"Request failed with error: {e}. Retrying in {actual_delay:.2f} seconds (retry {retries}/{max_retries})")
            time.sleep(actual_delay)
            
            # Exponential backoff
            delay = min(delay * 2, max_delay)
    
    return None

def get_ai_analysis(api_key, model="deepseek/deepseek-r1:free"):
    """Test the AI analysis function with sample coin data"""
    
    if not api_key:
        print("Error: API key is required")
        return
    
    # Sample coin data for testing
    sample_coins = [
        {
            "symbol": "btc",
            "name": "Bitcoin",
            "current_price": 67384.32,
            "price_change_percentage_24h": 2.45
        },
        {
            "symbol": "eth",
            "name": "Ethereum",
            "current_price": 3521.76,
            "price_change_percentage_24h": 1.23
        },
        {
            "symbol": "sol",
            "name": "Solana",
            "current_price": 157.89,
            "price_change_percentage_24h": 5.67
        }
    ]
    
    # Format the data for AI analysis (copied from send_to_discord.py)
    prompt = "Analyze the following cryptocurrency data and provide a brief investment outlook and sentiment analysis for each coin:\n\n"
    
    # Only analyze the top 3 coins
    for i, coin in enumerate(sample_coins[:3]):
        symbol = coin.get('symbol', '').upper()
        name = coin.get('name', '')
        price = coin.get('current_price', 0)
        change_24h = coin.get('price_change_percentage_24h', 0)
        
        prompt += f"{i+1}. {name} ({symbol}):\n"
        prompt += f"   - Current Price: ${price:,.6f}\n"
        prompt += f"   - 24h Change: {change_24h:.2f}%\n\n"
    
    prompt += "For each coin, provide: 1) Technical outlook (1-2 sentences), 2) Market sentiment (bullish/neutral/bearish), and 3) Key factors to watch."
    
    print(f"Generated prompt for AI analysis:\n{prompt}")
    
    # Call OpenRouter API
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "daily-altcoin-highlights",
        "X-Title": "Altcoin Analysis",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    # Define the API call function to use with retry mechanism
    def call_openrouter_api():
        print("Sending request to OpenRouter API...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30  # Add a timeout to prevent hanging
        )
        response.raise_for_status()  # This will raise an exception for HTTP errors
        return response.json()
    
    try:
        # Use the retry mechanism
        result = retry_with_exponential_backoff(call_openrouter_api)
        
        if not result:
            print("All API retry attempts failed")
            return "AI analysis unavailable after multiple retry attempts."
        
        print("API response successful!")
        
        if 'choices' in result and len(result['choices']) > 0:
            analysis = result['choices'][0]['message']['content']
            print(f"\nAI analysis received (length: {len(analysis)} chars)")
            print(f"\nAnalysis content:\n{'-'*50}")
            print(analysis)
            print(f"{'-'*50}")
            
            # Print additional API response information
            model_used = result.get('model', 'Unknown')
            tokens = result.get('usage', {})
            prompt_tokens = tokens.get('prompt_tokens', 'Unknown')
            completion_tokens = tokens.get('completion_tokens', 'Unknown')
            total_tokens = tokens.get('total_tokens', 'Unknown')
            
            print(f"\nModel used: {model_used}")
            print(f"Prompt tokens: {prompt_tokens}")
            print(f"Completion tokens: {completion_tokens}")
            print(f"Total tokens: {total_tokens}")
            
            return analysis
        else:
            print("No choices found in API response")
            print(f"Raw response: {json.dumps(result, indent=2)}")
            return "AI analysis unavailable due to invalid API response format."
    except Exception as e:
        print(f"Error getting AI analysis: {e}")
        return "AI analysis unavailable due to API error."

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_ai_analysis.py API_KEY [MODEL]")
        print("Example: python3 test_ai_analysis.py sk-or-v1-abc123 deepseek/deepseek-r1:free")
        print("\nAvailable free models include:")
        print("- deepseek/deepseek-r1:free")
        print("- anthropic/claude-3-haiku:free")
        print("- meta-llama/llama-3-8b-instruct:free")
        print("- mistralai/mistral-7b-instruct:free")
        sys.exit(1)
    
    # Get API key and optional model from command line arguments
    api_key = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "deepseek/deepseek-r1:free"
    
    get_ai_analysis(api_key, model) 