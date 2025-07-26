#!/usr/bin/env python3
"""
Configuration management CLI tool for AIRSS Orchestrator
Provides easy commands to manage persistent settings
"""

import sys
import json
from orchestrator_db import get_db
from orchestrator_config import get_config, set_config_value
from simple_cron import SimpleCron, COMMON_EXPRESSIONS

def show_config():
    """Show current configuration"""
    config = get_config()
    config_dict = {
        "schedule": {
            "enabled": config.schedule.enabled,
            "default_cron": config.schedule.default_cron,
            "timezone": config.schedule.timezone,
            "max_concurrent_workflows": config.schedule.max_concurrent_workflows
        },
        "workflow": {
            "default_hours_back": config.workflow.default_hours_back,
            "timeout_seconds": config.workflow.timeout_seconds,
            "send_sse_events": config.workflow.send_sse_events
        },
        "sse": {
            "enabled": config.sse.enabled,
            "port": config.sse.port,
            "max_clients": config.sse.max_clients
        },
        "debug": config.debug
    }
    print(json.dumps(config_dict, indent=2))

def set_schedule(cron_expr: str):
    """Set the workflow schedule"""
    if cron_expr in COMMON_EXPRESSIONS:
        cron_expr = COMMON_EXPRESSIONS[cron_expr]
        print(f"Using common expression: {cron_expr}")
    
    if not SimpleCron.is_valid(cron_expr):
        print(f"Error: Invalid cron expression: {cron_expr}")
        print("Examples:")
        print("  0 6 * * *     - Daily at 6am")
        print("  */30 * * * *  - Every 30 minutes")
        print("  0 9 * * 1-5   - Weekdays at 9am")
        return False
    
    set_config_value("schedule.default_cron", cron_expr, "Default cron expression for scheduled workflows")
    
    # Show next few run times
    from datetime import datetime
    cron = SimpleCron(cron_expr)
    next_run = cron.next_run()
    print(f"Schedule updated to: {cron_expr}")
    print(f"Next run: {next_run}")
    
    return True

def enable_schedule(enabled: bool = True):
    """Enable or disable scheduled workflows"""
    set_config_value("schedule.enabled", enabled, "Enable/disable scheduled workflows")
    status = "enabled" if enabled else "disabled"
    print(f"Scheduled workflows {status}")

def set_sse_port(port: int):
    """Set SSE server port"""
    if port < 1 or port > 65535:
        print("Error: Port must be between 1 and 65535")
        return False
    
    set_config_value("sse.port", port, "SSE server port")
    print(f"SSE port set to: {port}")
    return True

def set_timeout(seconds: int):
    """Set workflow timeout"""
    if seconds < 60:
        print("Error: Timeout must be at least 60 seconds")
        return False
    
    set_config_value("workflow.timeout_seconds", seconds, "Workflow timeout in seconds")
    print(f"Workflow timeout set to: {seconds} seconds")
    return True

def show_schedule_info():
    """Show schedule information and next run times"""
    config = get_config()
    print(f"Schedule enabled: {config.schedule.enabled}")
    print(f"Cron expression: {config.schedule.default_cron}")
    print(f"Timezone: {config.schedule.timezone}")
    
    if config.schedule.enabled:
        from datetime import datetime
        try:
            cron = SimpleCron(config.schedule.default_cron)
            next_run = cron.next_run()
            print(f"Next run: {next_run}")
            
            # Show next 5 runs
            print("\nNext 5 scheduled runs:")
            current = datetime.now()
            for i in range(5):
                next_time = cron.next_run(current)
                print(f"  {i+1}. {next_time}")
                current = next_time
                
        except Exception as e:
            print(f"Error calculating next run: {e}")

def show_common_schedules():
    """Show common cron schedule examples"""
    print("Common schedule expressions:")
    for name, expr in COMMON_EXPRESSIONS.items():
        print(f"  {name:20} - {expr}")
    
    print("\nCustom examples:")
    print("  0 6 * * *        - Daily at 6am")
    print("  0 */2 * * *      - Every 2 hours")
    print("  15 14 1 * *      - Monthly on 1st at 2:15pm")
    print("  0 22 * * 0       - Sundays at 10pm")
    print("  */15 9-17 * * 1-5 - Every 15 min, 9am-5pm, weekdays")

def show_status():
    """Show orchestrator status including recent workflows"""
    config = get_config()
    db = get_db()
    
    print("=== AIRSS Orchestrator Status ===")
    print(f"Schedule: {'Enabled' if config.schedule.enabled else 'Disabled'}")
    print(f"Cron: {config.schedule.default_cron}")
    print(f"SSE: {'Enabled' if config.sse.enabled else 'Disabled'} (port {config.sse.port})")
    print(f"Debug: {'On' if config.debug else 'Off'}")
    
    # Recent workflows
    recent = db.get_recent_workflows(5)
    print(f"\nRecent workflows ({len(recent)}):")
    for wf in recent:
        duration = f" ({wf.duration_seconds:.1f}s)" if wf.duration_seconds else ""
        print(f"  {wf.run_id}: {wf.status} - {wf.message}{duration}")
    
    # Stats
    stats = db.get_workflow_stats(7)
    print(f"\nStats (last 7 days):")
    print(f"  Total runs: {stats['total_runs']}")
    print(f"  Success rate: {stats['success_rate']:.1f}%")
    if stats['average_duration_seconds']:
        print(f"  Average duration: {stats['average_duration_seconds']:.1f}s")

def main():
    if len(sys.argv) < 2:
        print("AIRSS Orchestrator Configuration Manager")
        print("\nUsage:")
        print("  python config_manager.py show                   - Show current config")
        print("  python config_manager.py status                 - Show orchestrator status")
        print("  python config_manager.py schedule <cron>        - Set schedule (cron expression)")
        print("  python config_manager.py enable                 - Enable scheduled workflows")
        print("  python config_manager.py disable                - Disable scheduled workflows")
        print("  python config_manager.py schedule-info          - Show schedule information")
        print("  python config_manager.py common-schedules       - Show common schedule examples")
        print("  python config_manager.py sse-port <port>        - Set SSE server port")
        print("  python config_manager.py timeout <seconds>      - Set workflow timeout")
        print("\nExamples:")
        print("  python config_manager.py schedule daily_6am     - Use common daily 6am schedule")
        print("  python config_manager.py schedule '0 8 * * *'   - Daily at 8am")
        print("  python config_manager.py schedule '*/30 * * * *' - Every 30 minutes")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == "show":
            show_config()
        
        elif command == "status":
            show_status()
        
        elif command == "schedule":
            if len(sys.argv) < 3:
                print("Error: Schedule requires cron expression")
                print("Use 'common-schedules' to see examples")
                sys.exit(1)
            set_schedule(sys.argv[2])
        
        elif command == "enable":
            enable_schedule(True)
        
        elif command == "disable":
            enable_schedule(False)
        
        elif command == "schedule-info":
            show_schedule_info()
        
        elif command == "common-schedules":
            show_common_schedules()
        
        elif command == "sse-port":
            if len(sys.argv) < 3:
                print("Error: SSE port command requires port number")
                sys.exit(1)
            try:
                port = int(sys.argv[2])
                set_sse_port(port)
            except ValueError:
                print("Error: Port must be a number")
                sys.exit(1)
        
        elif command == "timeout":
            if len(sys.argv) < 3:
                print("Error: Timeout command requires seconds")
                sys.exit(1)
            try:
                seconds = int(sys.argv[2])
                set_timeout(seconds)
            except ValueError:
                print("Error: Timeout must be a number")
                sys.exit(1)
        
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()