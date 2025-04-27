# OpenRouter Integration Testing

This README provides instructions for testing and updating the OpenRouter integration used in the Daily Altcoin Highlights project.

## Background

The project uses OpenRouter API to generate AI-powered analysis of the top 3 altcoins. The integration is implemented in the `send_to_discord.py` file, which needs a valid OpenRouter API key to function properly.

## Testing Scripts

We've created several scripts to test the OpenRouter integration:

1. **Simple Test**: `simple_openrouter_test.py`
2. **AI Analysis Test**: `test_ai_analysis.py`
3. **Original Test**: `test_openrouter.py`
4. **API Key Update**: `update_openrouter.py`

## Getting an OpenRouter API Key

1. Create an account at [OpenRouter.ai](https://openrouter.ai/)
2. Go to the "Keys" section in your account
3. Click "Create Key" and give your key a name
4. Copy the generated API key (starts with `sk-or-v1-`)

## Testing the OpenRouter Integration

### Basic API Test

```bash
python3 simple_openrouter_test.py YOUR_API_KEY
```

You can specify a different model by adding the model ID as the second parameter:

```bash
python3 simple_openrouter_test.py YOUR_API_KEY deepseek/deepseek-r1:free
```

### Testing AI Analysis

This test simulates the AI analysis functionality used in the actual application:

```bash
python3 test_ai_analysis.py YOUR_API_KEY
```

### More Options

For more detailed testing options:

```bash
python3 test_openrouter.py --api-key YOUR_API_KEY --model deepseek/deepseek-r1:free
```

## Updating the API Key

To update the API key in the `send_to_discord.py` file:

```bash
python3 update_openrouter.py YOUR_API_KEY
```

This script will:
1. Create a backup of the original file
2. Update the API key
3. Provide instructions for testing the updated integration

## Available Free Models

OpenRouter provides several free models you can use for testing:

- `deepseek/deepseek-r1:free` (Default)
- `anthropic/claude-3-haiku:free`
- `meta-llama/llama-3-8b-instruct:free`
- `mistralai/mistral-7b-instruct:free`

## Troubleshooting

If you encounter an "Unauthorized" error (401), your API key may be invalid or expired. Generate a new API key from the OpenRouter website.

If you see other errors, ensure:
1. Your API key is correctly formatted and valid
2. You have sufficient credits in your OpenRouter account
3. The model you're trying to use is available on OpenRouter 