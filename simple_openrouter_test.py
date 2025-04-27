import requests
import json
import sys

def test_openrouter(api_key, model="deepseek/deepseek-r1:free"):
    """
    Simple test of the OpenRouter API.
    
    Args:
        api_key: OpenRouter API key
        model: Model ID to use (default: deepseek/deepseek-r1:free)
    """
    if not api_key:
        print("Error: API key is required")
        return
    
    print(f"Testing OpenRouter API with model: {model}")
    
    # OpenRouter API endpoint
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    # Request headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "daily-altcoin-highlights",
        "Content-Type": "application/json"
    }
    
    # Request payload
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "What are the top 3 cryptocurrencies by market cap today? Keep it brief."
            }
        ]
    }
    
    try:
        # Make the API request
        print("Sending request to OpenRouter API...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            print("\nAPI response successful!")
            
            # Extract and display the response content
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"\nResponse content:\n{'-'*50}")
                print(content)
                print(f"{'-'*50}")
                
                # Show model and token usage info
                model_used = result.get('model', 'Unknown')
                tokens = result.get('usage', {})
                prompt_tokens = tokens.get('prompt_tokens', 'Unknown')
                completion_tokens = tokens.get('completion_tokens', 'Unknown')
                total_tokens = tokens.get('total_tokens', 'Unknown')
                
                print(f"\nModel used: {model_used}")
                print(f"Prompt tokens: {prompt_tokens}")
                print(f"Completion tokens: {completion_tokens}")
                print(f"Total tokens: {total_tokens}")
            else:
                print("No response content found")
                print(f"Raw response: {json.dumps(result, indent=2)}")
        else:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Error message: {response.text}")
    
    except Exception as e:
        print(f"Error testing OpenRouter API: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 simple_openrouter_test.py API_KEY [MODEL]")
        print("Example: python3 simple_openrouter_test.py sk-or-v1-abc123 deepseek/deepseek-r1:free")
        print("\nAvailable free models include:")
        print("- deepseek/deepseek-r1:free")
        print("- anthropic/claude-3-haiku:free")
        print("- meta-llama/llama-3-8b-instruct:free")
        print("- mistralai/mistral-7b-instruct:free")
        sys.exit(1)
    
    # Get API key and optional model from command line arguments
    api_key = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "deepseek/deepseek-r1:free"
    
    test_openrouter(api_key, model) 