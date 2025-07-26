#!/usr/bin/env python3
"""
Check for scheduled workflow triggers and execute them
This can be run by Claude or called manually
"""

import json
import os
from datetime import datetime

def check_for_triggers():
    """Check for pending workflow triggers"""
    trigger_file = "/tmp/airss_scheduled_trigger.json"
    
    if not os.path.exists(trigger_file):
        return None
    
    try:
        with open(trigger_file, 'r') as f:
            trigger_data = json.load(f)
        
        print(f"Found trigger: {trigger_data['workflow_id']}")
        print(f"Triggered at: {trigger_data['triggered_at']}")
        print(f"Type: {trigger_data['trigger_type']}")
        
        return trigger_data
        
    except Exception as e:
        print(f"Error reading trigger file: {e}")
        return None

def clear_trigger():
    """Clear the trigger file after processing"""
    trigger_file = "/tmp/airss_scheduled_trigger.json"
    try:
        os.remove(trigger_file)
        print("Trigger file cleared")
    except:
        pass

def main():
    """Main function for manual testing"""
    trigger = check_for_triggers()
    
    if trigger:
        print("🎯 Found pending workflow trigger!")
        print("This is where Claude should execute the workflow using MCP tools")
        print()
        print("Claude should now:")
        print("1. Call mcp__rss-clustering__get_clustered_articles")
        print("2. Generate newsletter content")
        print("3. Call mcp__newsletter-generation__send_newsletter_email")
        print()
        
        # Don't clear trigger automatically - let Claude do it after execution
        
    else:
        print("No pending triggers found")

if __name__ == "__main__":
    main()