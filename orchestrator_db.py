#!/usr/bin/env python3
"""
SQLite database management for AIRSS Orchestrator
Handles persistent storage of configuration, workflow history, and settings
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from contextlib import contextmanager

@dataclass
class ConfigEntry:
    """Represents a configuration entry"""
    key: str
    value: str
    value_type: str  # "string", "int", "float", "bool", "json"
    category: str    # "schedule", "workflow", "sse", "general"
    description: str = ""
    created_at: str = ""
    updated_at: str = ""
    
    def get_typed_value(self) -> Any:
        """Get the value converted to its proper type"""
        if self.value_type == "int":
            return int(self.value)
        elif self.value_type == "float":
            return float(self.value)
        elif self.value_type == "bool":
            return self.value.lower() in ("true", "1", "yes", "on")
        elif self.value_type == "json":
            return json.loads(self.value)
        else:
            return self.value

@dataclass
class WorkflowRun:
    """Represents a workflow execution record"""
    id: Optional[int] = None
    run_id: str = ""
    workflow_id: str = ""
    trigger_type: str = "manual"
    start_time: str = ""
    end_time: Optional[str] = None
    status: str = "running"
    stage: str = "starting"
    progress: float = 0.0
    message: str = ""
    error: Optional[str] = None
    articles_processed: Optional[int] = None
    groups_generated: Optional[int] = None
    email_sent: bool = False
    duration_seconds: Optional[float] = None
    metadata: str = "{}"  # JSON string for additional data
    created_at: Optional[str] = None

class OrchestratorDB:
    """SQLite database manager for orchestrator data"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'orchestrator.db')
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            # Configuration table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    value_type TEXT NOT NULL DEFAULT 'string',
                    category TEXT NOT NULL DEFAULT 'general',
                    description TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Workflow runs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT UNIQUE NOT NULL,
                    workflow_id TEXT NOT NULL,
                    trigger_type TEXT NOT NULL DEFAULT 'manual',
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    status TEXT NOT NULL DEFAULT 'running',
                    stage TEXT NOT NULL DEFAULT 'starting',
                    progress REAL NOT NULL DEFAULT 0.0,
                    message TEXT DEFAULT '',
                    error TEXT,
                    articles_processed INTEGER,
                    groups_generated INTEGER,
                    email_sent BOOLEAN NOT NULL DEFAULT 0,
                    duration_seconds REAL,
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_config_category ON config(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_runs_start_time ON workflow_runs(start_time)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_runs_status ON workflow_runs(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_runs_trigger_type ON workflow_runs(trigger_type)")
            
            conn.commit()
            
        # Set default configuration if empty
        self._set_default_config()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def _set_default_config(self):
        """Set default configuration values if they don't exist"""
        defaults = [
            # Schedule configuration
            ("schedule.enabled", "true", "bool", "schedule", "Enable/disable scheduled workflows"),
            ("schedule.default_cron", "0 6 * * *", "string", "schedule", "Default cron expression for scheduled runs"),
            ("schedule.timezone", "UTC", "string", "schedule", "Timezone for scheduling"),
            ("schedule.max_concurrent", "1", "int", "schedule", "Maximum concurrent workflows"),
            
            # Workflow configuration
            ("workflow.default_hours_back", "24", "int", "workflow", "Default hours to look back for articles"),
            ("workflow.timeout_seconds", "600", "int", "workflow", "Workflow timeout in seconds"),
            ("workflow.send_sse_events", "true", "bool", "workflow", "Send SSE events during workflow"),
            
            # SSE configuration
            ("sse.enabled", "true", "bool", "sse", "Enable SSE server"),
            ("sse.port", "8080", "int", "sse", "SSE server port"),
            ("sse.max_clients", "100", "int", "sse", "Maximum SSE clients"),
            
            # General configuration
            ("general.debug", "false", "bool", "general", "Enable debug mode"),
            ("general.history_retention_days", "90", "int", "general", "Days to keep workflow history"),
        ]
        
        for key, value, value_type, category, description in defaults:
            if not self.get_config(key):
                self.set_config(key, value, value_type, category, description)
    
    # Configuration management
    def get_config(self, key: str) -> Optional[ConfigEntry]:
        """Get a configuration value"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM config WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return ConfigEntry(**dict(row))
        return None
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with type conversion"""
        entry = self.get_config(key)
        if entry:
            return entry.get_typed_value()
        return default
    
    def set_config(self, key: str, value: Any, value_type: str = None, category: str = "general", description: str = ""):
        """Set a configuration value"""
        if value_type is None:
            if isinstance(value, bool):
                value_type = "bool"
            elif isinstance(value, int):
                value_type = "int"
            elif isinstance(value, float):
                value_type = "float"
            elif isinstance(value, (dict, list)):
                value_type = "json"
                value = json.dumps(value)
            else:
                value_type = "string"
        
        # Convert value to string for storage
        if value_type == "json" and not isinstance(value, str):
            value = json.dumps(value)
        else:
            value = str(value)
        
        now = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            # Check if key exists
            existing = self.get_config(key)
            
            if existing:
                conn.execute("""
                    UPDATE config 
                    SET value = ?, value_type = ?, category = ?, description = ?, updated_at = ?
                    WHERE key = ?
                """, (value, value_type, category, description, now, key))
            else:
                conn.execute("""
                    INSERT INTO config (key, value, value_type, category, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (key, value, value_type, category, description, now, now))
            
            conn.commit()
    
    def get_config_by_category(self, category: str) -> List[ConfigEntry]:
        """Get all configuration entries for a category"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM config WHERE category = ? ORDER BY key", (category,))
            return [ConfigEntry(**dict(row)) for row in cursor.fetchall()]
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration as a nested dictionary"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM config ORDER BY category, key")
            config = {}
            
            for row in cursor.fetchall():
                entry = ConfigEntry(**dict(row))
                category, key = entry.key.split('.', 1) if '.' in entry.key else ('general', entry.key)
                
                if category not in config:
                    config[category] = {}
                
                config[category][key] = entry.get_typed_value()
            
            return config
    
    # Workflow history management
    def start_workflow(self, workflow_id: str, trigger_type: str = "manual") -> WorkflowRun:
        """Start a new workflow run"""
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{workflow_id}"
        now = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO workflow_runs (
                    run_id, workflow_id, trigger_type, start_time, status, stage, message
                ) VALUES (?, ?, ?, ?, 'running', 'starting', 'Workflow started')
            """, (run_id, workflow_id, trigger_type, now))
            
            workflow_run = WorkflowRun(
                id=cursor.lastrowid,
                run_id=run_id,
                workflow_id=workflow_id,
                trigger_type=trigger_type,
                start_time=now,
                status="running",
                stage="starting",
                message="Workflow started",
                created_at=now
            )
            
            conn.commit()
            return workflow_run
    
    def update_workflow(self, run_id: str, **updates) -> Optional[WorkflowRun]:
        """Update an existing workflow run"""
        if not updates:
            return None
        
        # Build UPDATE query dynamically
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            if key in ['status', 'stage', 'message', 'error', 'progress', 'articles_processed', 
                      'groups_generated', 'email_sent', 'duration_seconds', 'end_time', 'metadata']:
                set_clauses.append(f"{key} = ?")
                if key == 'metadata' and isinstance(value, dict):
                    values.append(json.dumps(value))
                else:
                    values.append(value)
        
        if not set_clauses:
            return None
        
        values.append(run_id)
        query = f"UPDATE workflow_runs SET {', '.join(set_clauses)} WHERE run_id = ?"
        
        with self._get_connection() as conn:
            conn.execute(query, values)
            conn.commit()
            
            # Return updated workflow
            return self.get_workflow_by_run_id(run_id)
    
    def complete_workflow(self, run_id: str, status: str = "completed", **final_updates) -> Optional[WorkflowRun]:
        """Mark a workflow as completed"""
        updates = {
            "status": status,
            "end_time": datetime.now().isoformat(),
            "progress": 100.0,
            **final_updates
        }
        
        # Calculate duration
        workflow = self.get_workflow_by_run_id(run_id)
        if workflow and workflow.start_time:
            try:
                start = datetime.fromisoformat(workflow.start_time)
                end = datetime.fromisoformat(updates["end_time"])
                updates["duration_seconds"] = (end - start).total_seconds()
            except:
                pass
        
        return self.update_workflow(run_id, **updates)
    
    def get_workflow_by_run_id(self, run_id: str) -> Optional[WorkflowRun]:
        """Get a workflow run by run_id"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM workflow_runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            if row:
                row_dict = dict(row)
                # Convert SQLite integer to boolean
                if 'email_sent' in row_dict:
                    row_dict['email_sent'] = bool(row_dict['email_sent'])
                return WorkflowRun(**row_dict)
        return None
    
    def get_recent_workflows(self, limit: int = 10) -> List[WorkflowRun]:
        """Get recent workflow runs"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM workflow_runs 
                ORDER BY start_time DESC 
                LIMIT ?
            """, (limit,))
            results = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                # Convert SQLite integer to boolean
                if 'email_sent' in row_dict:
                    row_dict['email_sent'] = bool(row_dict['email_sent'])
                results.append(WorkflowRun(**row_dict))
            return results
    
    def get_workflow_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get workflow statistics for the last N days"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self._get_connection() as conn:
            # Total runs
            cursor = conn.execute("""
                SELECT COUNT(*) as total_runs,
                       SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                       SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                       AVG(CASE WHEN status = 'completed' AND duration_seconds IS NOT NULL 
                               THEN duration_seconds ELSE NULL END) as avg_duration
                FROM workflow_runs 
                WHERE start_time > ?
            """, (cutoff,))
            
            stats_row = cursor.fetchone()
            total_runs = stats_row['total_runs'] or 0
            completed = stats_row['completed'] or 0
            failed = stats_row['failed'] or 0
            avg_duration = stats_row['avg_duration']
            
            # Get last run
            cursor = conn.execute("""
                SELECT * FROM workflow_runs 
                WHERE start_time > ?
                ORDER BY start_time DESC 
                LIMIT 1
            """, (cutoff,))
            
            last_run_row = cursor.fetchone()
            last_run = dict(last_run_row) if last_run_row else None
            
            return {
                "period_days": days,
                "total_runs": total_runs,
                "completed": completed,
                "failed": failed,
                "success_rate": (completed / total_runs * 100) if total_runs > 0 else 0,
                "average_duration_seconds": avg_duration,
                "last_run": last_run
            }
    
    def cleanup_old_workflows(self, days: int = 90) -> int:
        """Remove workflow runs older than N days"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM workflow_runs WHERE start_time < ?", (cutoff,))
            deleted_count = cursor.rowcount
            conn.commit()
            
            return deleted_count

# Global database instance
_db: Optional[OrchestratorDB] = None

def get_db() -> OrchestratorDB:
    """Get the global database instance"""
    global _db
    if _db is None:
        _db = OrchestratorDB()
    return _db

if __name__ == "__main__":
    # CLI for database management
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python orchestrator_db.py [init|config|history|stats|cleanup]")
        sys.exit(1)
    
    command = sys.argv[1]
    db = get_db()
    
    if command == "init":
        print("Database initialized successfully")
        print(f"Database location: {db.db_path}")
    
    elif command == "config":
        if len(sys.argv) > 3:
            # Set config: python orchestrator_db.py config key value
            key, value = sys.argv[2], sys.argv[3]
            db.set_config(key, value)
            print(f"Set {key} = {value}")
        elif len(sys.argv) > 2:
            # Get config: python orchestrator_db.py config key
            key = sys.argv[2]
            entry = db.get_config(key)
            if entry:
                print(f"{key} = {entry.get_typed_value()} ({entry.value_type})")
            else:
                print(f"Configuration key '{key}' not found")
        else:
            # Show all config
            config = db.get_all_config()
            print(json.dumps(config, indent=2))
    
    elif command == "history":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        workflows = db.get_recent_workflows(limit)
        
        print(f"Recent {len(workflows)} workflow runs:")
        for wf in workflows:
            duration = f" ({wf.duration_seconds:.1f}s)" if wf.duration_seconds else ""
            print(f"  {wf.run_id}: {wf.status} - {wf.message}{duration}")
    
    elif command == "stats":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        stats = db.get_workflow_stats(days)
        print(f"Workflow statistics (last {days} days):")
        print(json.dumps(stats, indent=2, default=str))
    
    elif command == "cleanup":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
        deleted = db.cleanup_old_workflows(days)
        print(f"Cleaned up {deleted} workflow runs older than {days} days")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)