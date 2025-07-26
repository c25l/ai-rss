#!/usr/bin/env python3
"""
Simple cron expression parser and evaluator
Supports basic cron expressions: minute hour day month weekday
"""

from datetime import datetime, timedelta
from typing import List, Union

class SimpleCron:
    """Simple cron expression parser and evaluator"""
    
    def __init__(self, cron_expression: str):
        self.expression = cron_expression.strip()
        self.parts = self.expression.split()
        
        if len(self.parts) != 5:
            raise ValueError("Cron expression must have 5 parts: minute hour day month weekday")
        
        self.minute, self.hour, self.day, self.month, self.weekday = self.parts
    
    def _matches_field(self, value: int, field: str, field_range: tuple) -> bool:
        """Check if a value matches a cron field"""
        if field == "*":
            return True
        
        if "/" in field:
            # Handle step values like */5 or 2-10/3
            base, step = field.split("/", 1)
            step = int(step)
            
            if base == "*":
                return value % step == 0
            elif "-" in base:
                start, end = map(int, base.split("-", 1))
                return start <= value <= end and (value - start) % step == 0
            else:
                start = int(base)
                return value >= start and (value - start) % step == 0
        
        if "-" in field:
            # Handle ranges like 2-5
            start, end = map(int, field.split("-", 1))
            return start <= value <= end
        
        if "," in field:
            # Handle lists like 1,3,5
            values = [int(x.strip()) for x in field.split(",")]
            return value in values
        
        # Single value
        return value == int(field)
    
    def matches(self, dt: datetime) -> bool:
        """Check if datetime matches this cron expression"""
        try:
            # Check minute (0-59)
            if not self._matches_field(dt.minute, self.minute, (0, 59)):
                return False
            
            # Check hour (0-23)  
            if not self._matches_field(dt.hour, self.hour, (0, 23)):
                return False
            
            # Check day of month (1-31)
            if not self._matches_field(dt.day, self.day, (1, 31)):
                return False
            
            # Check month (1-12)
            if not self._matches_field(dt.month, self.month, (1, 12)):
                return False
            
            # Check weekday (0-6, Sunday=0)
            weekday = dt.weekday()
            if weekday == 6:  # Python Sunday=6, cron Sunday=0
                weekday = 0
            else:
                weekday += 1  # Python Monday=0, cron Monday=1
            
            if not self._matches_field(weekday, self.weekday, (0, 6)):
                return False
            
            return True
            
        except (ValueError, IndexError):
            return False
    
    def next_run(self, from_time: datetime = None) -> datetime:
        """Get the next execution time after from_time"""
        if from_time is None:
            from_time = datetime.now()
        
        # Start from the next minute
        next_time = from_time.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # Check up to 4 years in the future to avoid infinite loops
        max_time = from_time + timedelta(days=365 * 4)
        
        while next_time < max_time:
            if self.matches(next_time):
                return next_time
            next_time += timedelta(minutes=1)
        
        raise ValueError("No valid next execution time found within 4 years")
    
    @staticmethod
    def is_valid(expression: str) -> bool:
        """Check if a cron expression is valid"""
        try:
            cron = SimpleCron(expression)
            # Try to get next run to validate
            cron.next_run()
            return True
        except:
            return False

# Common cron expressions
COMMON_EXPRESSIONS = {
    "hourly": "0 * * * *",
    "daily": "0 0 * * *", 
    "daily_6am": "0 6 * * *",
    "weekly": "0 0 * * 0",
    "monthly": "0 0 1 * *",
    "every_5_minutes": "*/5 * * * *",
    "every_30_minutes": "*/30 * * * *",
    "weekdays_9am": "0 9 * * 1-5",
    "weekend_10am": "0 10 * * 0,6"
}

def get_common_expression(name: str) -> str:
    """Get a common cron expression by name"""
    return COMMON_EXPRESSIONS.get(name, name)

if __name__ == "__main__":
    # Test the cron parser
    test_expressions = [
        "0 6 * * *",      # Daily at 6am
        "*/15 * * * *",   # Every 15 minutes
        "0 9 * * 1-5",    # Weekdays at 9am
        "0 0 1 * *",      # Monthly on 1st
    ]
    
    now = datetime.now()
    print(f"Current time: {now}")
    print()
    
    for expr in test_expressions:
        try:
            cron = SimpleCron(expr)
            next_run = cron.next_run(now)
            print(f"Expression: {expr}")
            print(f"Next run: {next_run}")
            print(f"Time until: {next_run - now}")
            print()
        except Exception as e:
            print(f"Error with {expr}: {e}")
            print()