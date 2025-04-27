import re
import sys
import os
import shutil
import time
from datetime import datetime

def update_openrouter_api_key(file_path, new_api_key):
    """
    Update the OpenRouter API key in the given file.
    
    Args:
        file_path: Path to the file containing the API key
        new_api_key: New API key to set
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return False
    
    # Create a backup of the original file
    backup_path = f"{file_path}.bak.{int(time.time())}"
    try:
        shutil.copy2(file_path, backup_path)
        print(f"Created backup at {backup_path}")
    except Exception as e:
        print(f"Warning: Failed to create backup: {e}")
    
    try:
        # Read the file content
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Looking for the pattern where the API key is set
        api_key_pattern = r'("Authorization":\s*"Bearer\s+)([^"]+)(")'
        
        # Check if pattern exists in the file
        if not re.search(api_key_pattern, content):
            print(f"Error: Could not find API key pattern in {file_path}")
            return False
        
        # Replace the API key
        modified_content = re.sub(api_key_pattern, f'\\1{new_api_key}\\3', content)
        
        # Write the modified content back to the file
        with open(file_path, 'w') as f:
            f.write(modified_content)
        
        print(f"Successfully updated OpenRouter API key in {file_path}")
        return True
    
    except Exception as e:
        print(f"Error updating API key: {e}")
        # Restore from backup if available
        if os.path.exists(backup_path):
            try:
                shutil.copy2(backup_path, file_path)
                print(f"Restored original file from backup")
            except Exception as restore_error:
                print(f"Error restoring backup: {restore_error}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 update_openrouter.py NEW_API_KEY [FILE_PATH]")
        print("Example: python3 update_openrouter.py sk-or-v1-abc123 send_to_discord.py")
        sys.exit(1)
    
    # Get parameters
    new_api_key = sys.argv[1]
    file_path = sys.argv[2] if len(sys.argv) > 2 else "send_to_discord.py"
    
    # Validate API key format
    if not new_api_key.startswith("sk-or-v1-"):
        print("Warning: API key doesn't match expected format (should start with 'sk-or-v1-')")
        confirm = input("Continue anyway? (y/n): ")
        if confirm.lower() != 'y':
            print("Operation canceled")
            sys.exit(0)
    
    # Update the API key
    if update_openrouter_api_key(file_path, new_api_key):
        print("\nAPI key updated successfully!")
        print("\nTo test the integration, run:")
        print(f"python3 test_ai_analysis.py {new_api_key}")
    else:
        print("\nFailed to update API key")
        sys.exit(1) 