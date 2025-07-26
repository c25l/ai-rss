#!/usr/bin/env python3
"""
AIRSS Scheduler Daemon
Runs independently of MCP servers and triggers workflows when scheduled.
"""

import time
import json
import os
from datetime import datetime, timedelta
from orchestrator_config import get_config
from simple_cron import SimpleCron
from orchestrator_db import get_db

class AIRSSScheduler:
    def __init__(self):
        self.last_trigger = None
        self.trigger_file = "/tmp/airss_scheduled_trigger.json"
        
    def should_trigger(self, cron_expr: str) -> bool:
        """Check if we should trigger based on cron expression"""
        cron = SimpleCron(cron_expr)
        now = datetime.now()
        
        # Check if current time matches cron
        if not cron.matches(now):
            return False
        
        # Avoid duplicate triggers within same minute
        if self.last_trigger and (now - self.last_trigger).total_seconds() < 60:
            return False
        
        return True
    
    def create_trigger(self) -> str:
        """Create a trigger file for Claude to detect"""
        now = datetime.now()
        workflow_id = now.strftime('%Y%m%d_%H%M%S')
        
        trigger_data = {
            "workflow_id": workflow_id,
            "triggered_at": now.isoformat(),
            "trigger_type": "scheduled",
            "status": "pending",
            "cron_expression": get_config().schedule.default_cron
        }
        
        # Write trigger file
        with open(self.trigger_file, 'w') as f:
            json.dump(trigger_data, f, indent=2)
        
        # Log to database
        try:
            db = get_db()
            workflow_run = db.start_workflow(workflow_id, "scheduled")
            db.update_workflow(workflow_run.run_id,
                             stage="scheduled_trigger_created",
                             message="Scheduled trigger created - waiting for Claude to execute")
        except Exception as e:
            print(f"[SCHEDULER] Database logging failed: {e}")
        
        self.last_trigger = now
        return self.trigger_file
    
    def check_trigger_file(self) -> dict:
        """Check if there's a pending trigger file"""
        if os.path.exists(self.trigger_file):
            try:
                with open(self.trigger_file, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def run(self):
        """Main scheduler loop"""
        print(f"[SCHEDULER] AIRSS Scheduler started at {datetime.now()}")
        print(f"[SCHEDULER] Trigger file: {self.trigger_file}")
        
        while True:
            try:
                config = get_config()
                now = datetime.now()
                
                # Show status every 10 minutes
                if now.minute % 10 == 0 and now.second < 10:
                    status = "enabled" if config.schedule.enabled else "disabled"
                    print(f"[SCHEDULER] {now.strftime('%H:%M')} - Status: {status}, Schedule: {config.schedule.default_cron}")
                
                # Check if scheduling is enabled
                if not config.schedule.enabled:
                    time.sleep(60)
                    continue
                
                # Check if we should trigger
                if self.should_trigger(config.schedule.default_cron):
                    print(f"[SCHEDULER] ⏰ Schedule match at {now}")
                    trigger_file = self.create_trigger()
                    print(f"[SCHEDULER] Created trigger file: {trigger_file}")
                    print(f"[SCHEDULER] Next Claude session should detect and execute workflow")
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"[SCHEDULER] Error: {e}")
                time.sleep(60)

def main():
    """Main entry point"""
    scheduler = AIRSSScheduler()
    
    try:
        scheduler.run()
    except KeyboardInterrupt:
        print(f"\n[SCHEDULER] Stopped at {datetime.now()}")

if __name__ == "__main__":
    main()