import requests
import json
import time
import random
import sys
import argparse

def retry_with_exponential_backoff(func, max_retries=5, base_delay=1, max_delay=32, jitter=0.1):
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
            if retries > max_retries or (400 <= e.response.status_code < 500 and e.response.status_code != 429):
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

def test_openrouter_api(api_key, model="tngtech/deepseek-r1t-chimera:free"):
    """Test the OpenRouter API integration with a simple prompt"""
    
    if not api_key:
        print("Error: API key is required")
        return
    
    print(f"Testing OpenRouter API with model: {model}")
    
    # Simple test prompt
    prompt = "What are the top 3 cryptocurrencies by market cap today? Please provide a very brief description of each."
    
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
    
    # Define the API call function
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
            return
        
        print(f"API response status: Success")
        
        if 'choices' in result and len(result['choices']) > 0:
            analysis = result['choices'][0]['message']['content']
            print(f"\nAPI response content:\n{'-'*30}\n{analysis}\n{'-'*30}")
            print(f"\nResponse length: {len(analysis)} chars")
            
            # Print additional API response information
            model_used = result.get('model', 'Unknown')
            tokens_used = result.get('usage', {}).get('total_tokens', 'Unknown')
            print(f"Model used: {model_used}")
            print(f"Tokens used: {tokens_used}")
        else:
            print("No choices found in API response")
            print(f"Raw response: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Error testing OpenRouter API: {e}")

def main():
    parser = argparse.ArgumentParser(description="Test OpenRouter API integration")
    parser.add_argument("--api-key", required=True, help="OpenRouter API key")
    parser.add_argument("--model", default="tngtech/deepseek-r1t-chimera:free", 
                       help="Model to use (default: tngtech/deepseek-r1t-chimera:free)")
    
    args = parser.parse_args()
    test_openrouter_api(args.api_key, args.model)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_openrouter.py --api-key YOUR_API_KEY [--model MODEL_NAME]")
        print("Example: python3 test_openrouter.py --api-key sk-or-v1-abc123 --model openai/gpt-3.5-turbo")
        sys.exit(1)
    
    main() 