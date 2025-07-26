#!/usr/bin/env python3
"""
Standalone cron daemon for AIRSS
This runs independently and triggers workflows via MCP calls
"""

import time
import asyncio
from datetime import datetime
from orchestrator_config import get_config
from simple_cron import SimpleCron
from orchestrator_db import get_db

# Global state
last_run = None

def should_trigger(cron_expr: str) -> bool:
    """Check if we should trigger based on cron expression"""
    global last_run
    
    cron = SimpleCron(cron_expr)
    now = datetime.now()
    
    # Check if current time matches
    if not cron.matches(now):
        return False
    
    # Check cooldown (avoid duplicate triggers within same minute)
    if last_run and (now - last_run).total_seconds() < 60:
        return False
    
    return True

async def trigger_workflow():
    """Trigger workflow via MCP call"""
    global last_run
    
    try:
        # Import MCP client functionality  
        print(f"[CRON] Triggering workflow at {datetime.now()}")
        
        # We can't easily call MCP from here, so let's create a workflow trigger file
        # that the orchestrator can detect
        trigger_file = "/tmp/airss_cron_trigger"
        with open(trigger_file, "w") as f:
            f.write(datetime.now().isoformat())
        
        # Record in database
        db = get_db()
        workflow_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        workflow_run = db.start_workflow(workflow_id, "cron")
        db.update_workflow(workflow_run.run_id, 
                         stage="triggered", 
                         message="Cron triggered - trigger file created")
        
        last_run = datetime.now()
        print(f"[CRON] Workflow trigger created: {trigger_file}")
        
    except Exception as e:
        print(f"[CRON] Error triggering workflow: {e}")

def main():
    """Main cron daemon loop"""
    print(f"[CRON] AIRSS Cron Daemon started at {datetime.now()}")
    
    while True:
        try:
            config = get_config()
            
            if not config.schedule.enabled:
                print(f"[CRON] Scheduling disabled, sleeping...")
                time.sleep(300)  # Check every 5 minutes when disabled
                continue
            
            now = datetime.now()
            
            # Log status every 5 minutes
            if now.minute % 5 == 0 and now.second < 5:
                print(f"[CRON] Daemon alive at {now.strftime('%H:%M:%S')} - Schedule: {config.schedule.default_cron}")
            
            # Check if we should trigger
            if should_trigger(config.schedule.default_cron):
                print(f"[CRON] Cron match detected at {now}")
                asyncio.run(trigger_workflow())
            
            time.sleep(5)  # Check every 5 seconds for more precision
            
        except Exception as e:
            print(f"[CRON] Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"[CRON] Daemon stopped at {datetime.now()}")