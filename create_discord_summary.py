import ai_highlights
import os
import sys

def generate_consolidated_discord_summary():
    """
    Generate a consolidated summary of both AI highlights and momentum strategy results
    for posting to Discord.
    """
    # Check if the momentum strategy results exist
    if not os.path.exists("ai_momentum_strategy_post.md"):
        print("Error: AI momentum strategy results not found. Run momentum_strategy.py first.")
        return False
        
    # Read the momentum strategy results
    with open("ai_momentum_strategy_post.md", "r") as f:
        momentum_content = f.read()
    
    # Generate the AI highlights summary
    market_data = ai_highlights.get_market_data()
    if not market_data:
        print("Failed to retrieve market data for AI highlights")
        return False
    
    ai_summary = ai_highlights.generate_summary(market_data)
    
    # Combine the summaries
    consolidated = f"{ai_summary}\n\n**AI ALTCOIN MOMENTUM STRATEGY**\n\n"
    
    # Extract only the key parts of the momentum strategy for Discord (to keep it concise)
    performance_start = momentum_content.find("## Performance Summary")
    insights_start = momentum_content.find("## Key Insights")
    notes_start = momentum_content.find("## Notes")
    
    if performance_start != -1 and insights_start != -1:
        performance_section = momentum_content[performance_start:insights_start].strip()
        insights_section = momentum_content[insights_start:notes_start].strip() if notes_start != -1 else momentum_content[insights_start:].strip()
        
        consolidated += f"{performance_section}\n\n{insights_section}\n\n"
    else:
        # Fallback if we couldn't parse the sections
        consolidated += "See the full strategy results in the attached image.\n\n"
    
    consolidated += "📊 Performance chart has been generated as 'ai_momentum_strategy_plot.png'."
    
    print("\n--- CONSOLIDATED SUMMARY ---\n")
    print(consolidated)
    print("\n--------------------------\n")
    
    # Save the consolidated summary
    with open("consolidated_discord_summary.txt", "w") as f:
        f.write(consolidated)
    print("Consolidated summary saved to consolidated_discord_summary.txt")
    
    # Send to Discord
    print("Sending consolidated summary to Discord...")
    success = ai_highlights.send_to_discord(consolidated)
    
    if success:
        print("Successfully sent to Discord!")
    else:
        print("Failed to send to Discord")
        
    return success

if __name__ == "__main__":
    # First make sure we run the momentum strategy
    print("Running momentum strategy...")
    os.system("python3 momentum_strategy.py")
    
    # Then generate and send the consolidated summary
    print("\nGenerating consolidated Discord summary...")
    generate_consolidated_discord_summary() 