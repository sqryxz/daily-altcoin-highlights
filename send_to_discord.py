import ai_highlights
import os

def send_insights_to_discord():
    """Send the momentum strategy insights to Discord using webhook"""
    
    # Check if the file exists
    if not os.path.exists("discord_momentum_insights.md"):
        print("Error: discord_momentum_insights.md not found!")
        return False
    
    # Read the content
    with open("discord_momentum_insights.md", "r") as f:
        content = f.read()
    
    print("Sending momentum strategy insights to Discord...")
    
    # Use the existing send_to_discord function from ai_highlights
    success = ai_highlights.send_to_discord(content)
    
    if success:
        print("Successfully sent insights to Discord!")
    else:
        print("Failed to send insights to Discord.")
    
    return success

if __name__ == "__main__":
    send_insights_to_discord() 