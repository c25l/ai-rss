#!/usr/bin/env python3
"""
Configuration management for AIRSS Orchestrator using SQLite backend
Handles only coordination settings - no email credentials (those are in Server 2)
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from orchestrator_db import get_db

@dataclass
class ScheduleConfig:
    """Scheduling configuration"""
    enabled: bool = True
    default_cron: str = "0 6 * * *"  # Daily at 6am
    timezone: str = "UTC"
    max_concurrent_workflows: int = 1
    
@dataclass
class WorkflowConfig:
    """Workflow coordination settings"""
    default_hours_back: int = 24
    timeout_seconds: int = 600  # 10 minutes
    send_sse_events: bool = True
    
@dataclass
class SSEConfig:
    """Server-Sent Events configuration"""
    enabled: bool = True
    port: int = 8080
    max_clients: int = 100

@dataclass
class OrchestratorConfig:
    """Main orchestrator configuration - coordination only"""
    schedule: ScheduleConfig
    workflow: WorkflowConfig
    sse: SSEConfig
    debug: bool = False
    
    @classmethod
    def from_file(cls, config_path: str) -> 'OrchestratorConfig':
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            
            return cls(
                schedule=ScheduleConfig(**data.get('schedule', {})),
                workflow=WorkflowConfig(**data.get('workflow', {})),
                sse=SSEConfig(**data.get('sse', {})),
                debug=data.get('debug', False)
            )
        except FileNotFoundError:
            # Create default config if file doesn't exist
            config = cls.default()
            config.save_to_file(config_path)
            return config
        except Exception as e:
            raise ValueError(f"Failed to load configuration from {config_path}: {e}")
    
    @classmethod
    def from_env(cls) -> 'OrchestratorConfig':
        """Load configuration from environment variables"""
        return cls(
            schedule=ScheduleConfig(
                enabled=os.getenv('AIRSS_SCHEDULE_ENABLED', 'true').lower() == 'true',
                default_cron=os.getenv('AIRSS_DEFAULT_CRON', '0 6 * * *'),
                timezone=os.getenv('AIRSS_TIMEZONE', 'UTC'),
                max_concurrent_workflows=int(os.getenv('AIRSS_MAX_CONCURRENT', '1'))
            ),
            workflow=WorkflowConfig(
                default_hours_back=int(os.getenv('AIRSS_HOURS_BACK', '24')),
                timeout_seconds=int(os.getenv('AIRSS_TIMEOUT', '600')),
                send_sse_events=os.getenv('AIRSS_SEND_SSE', 'true').lower() == 'true'
            ),
            sse=SSEConfig(
                enabled=os.getenv('AIRSS_SSE_ENABLED', 'true').lower() == 'true',
                port=int(os.getenv('AIRSS_SSE_PORT', '8080')),
                max_clients=int(os.getenv('AIRSS_SSE_MAX_CLIENTS', '100'))
            ),
            debug=os.getenv('AIRSS_DEBUG', 'false').lower() == 'true'
        )
    
    @classmethod
    def default(cls) -> 'OrchestratorConfig':
        """Create default configuration"""
        return cls(
            schedule=ScheduleConfig(),
            workflow=WorkflowConfig(),
            sse=SSEConfig()
        )
    
    def save_to_file(self, config_path: str):
        """Save configuration to JSON file"""
        config_dict = asdict(self)
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)

# Global configuration instance
_config: Optional[OrchestratorConfig] = None

def get_config() -> OrchestratorConfig:
    """Get the global configuration instance from SQLite"""
    db = get_db()
    config_data = db.get_all_config()
    
    return OrchestratorConfig(
        schedule=ScheduleConfig(
            enabled=config_data.get('schedule', {}).get('enabled', True),
            default_cron=config_data.get('schedule', {}).get('default_cron', '0 6 * * *'),
            timezone=config_data.get('schedule', {}).get('timezone', 'UTC'),
            max_concurrent_workflows=config_data.get('schedule', {}).get('max_concurrent', 1)
        ),
        workflow=WorkflowConfig(
            default_hours_back=config_data.get('workflow', {}).get('default_hours_back', 24),
            timeout_seconds=config_data.get('workflow', {}).get('timeout_seconds', 600),
            send_sse_events=config_data.get('workflow', {}).get('send_sse_events', True)
        ),
        sse=SSEConfig(
            enabled=config_data.get('sse', {}).get('enabled', True),
            port=config_data.get('sse', {}).get('port', 8080),
            max_clients=config_data.get('sse', {}).get('max_clients', 100)
        ),
        debug=config_data.get('general', {}).get('debug', False)
    )

def set_config_value(key: str, value: Any, description: str = ""):
    """Set a configuration value in SQLite"""
    db = get_db()
    
    # Determine category from key
    category = key.split('.', 1)[0] if '.' in key else 'general'
    
    # Determine type
    if isinstance(value, bool):
        value_type = "bool"
    elif isinstance(value, int):
        value_type = "int"
    elif isinstance(value, float):
        value_type = "float"
    else:
        value_type = "string"
    
    db.set_config(key, value, value_type, category, description)

def reload_config():
    """Reload the global configuration (no-op for SQLite backend)"""
    return get_config()

if __name__ == "__main__":
    # CLI for configuration management
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python orchestrator_config.py [show|create-default]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "show":
        config = get_config()
        print(json.dumps(asdict(config), indent=2))
    
    elif command == "create-default":
        config = OrchestratorConfig.default()
        config_path = os.path.join(os.path.dirname(__file__), 'orchestrator_config.json')
        config.save_to_file(config_path)
        print(f"Default configuration created at: {config_path}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)