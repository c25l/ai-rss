#!/usr/bin/env python3
"""
Simple script to trigger AIRSS workflow
Can be called from system cron or manually
"""

import os
import sys
from datetime import datetime

def main():
    """Trigger AIRSS workflow by creating a trigger file"""
    
    # Create trigger file that Claude can detect
    trigger_file = "/tmp/airss_workflow_trigger"
    trigger_data = {
        "triggered_at": datetime.now().isoformat(),
        "trigger_type": "cron" if len(sys.argv) > 1 and sys.argv[1] == "cron" else "manual",
        "workflow_id": datetime.now().strftime('%Y%m%d_%H%M%S')
    }
    
    try:
        import json
        with open(trigger_file, "w") as f:
            json.dump(trigger_data, f, indent=2)
        
        print(f"Workflow trigger created: {trigger_file}")
        print(f"Triggered at: {trigger_data['triggered_at']}")
        print(f"Type: {trigger_data['trigger_type']}")
        
        # Also log to database if available
        try:
            from orchestrator_db import get_db
            db = get_db()
            workflow_run = db.start_workflow(
                trigger_data["workflow_id"], 
                trigger_data["trigger_type"]
            )
            db.update_workflow(workflow_run.run_id, 
                             stage="trigger_file_created",
                             message="Workflow trigger file created - waiting for Claude")
            print(f"Database entry created: {workflow_run.run_id}")
            
        except Exception as e:
            print(f"Note: Could not log to database: {e}")
        
    except Exception as e:
        print(f"Error creating trigger: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()