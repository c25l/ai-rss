import datetime
import os.path
import json 
from dateutil import parser,tz
import objc
from Foundation import NSDate, NSCalendar, NSDateComponents
from EventKit import EKEventStore, EKEntityTypeEvent
 

def get_calendar_events(days=7):
    """Get events from Apple Calendar using EventKit"""
        
    try:
        # Create event store
        store = EKEventStore.alloc().init()
        
        # Just try to access calendars directly - EventKit will handle permissions
        print("Attempting to access calendars...")
        
        # Set up date range
        now = NSDate.date()
        calendar = NSCalendar.currentCalendar()
        end_components = NSDateComponents.alloc().init()
        end_components.setDay_(days)
        end_date = calendar.dateByAddingComponents_toDate_options_(end_components, now, 0)
        
        # Create predicate for events in date range
        predicate = store.predicateForEventsWithStartDate_endDate_calendars_(now, end_date, None)
        
        # Fetch events
        events = store.eventsMatchingPredicate_(predicate)
        
        # Organize events by date
        events_by_date = {}
        for event in events:
            start_date = event.startDate()
            # Convert NSDate to Python datetime
            start_py = datetime.datetime.fromtimestamp(start_date.timeIntervalSince1970())
            date_key = start_py.date().isoformat()
            
            if date_key not in events_by_date:
                events_by_date[date_key] = []
                
            end_date = event.endDate()
            end_py = datetime.datetime.fromtimestamp(end_date.timeIntervalSince1970())
            
            events_by_date[date_key].append({
                'summary': str(event.title()),
                'start': start_py.isoformat(),
                'end': end_py.isoformat(),
                'calendar': str(event.calendar().title())
            })
        return events_by_date
        
    except Exception as e:
        print(f"Error querying calendar with EventKit: {e}")
        return {}

# AppleScript parsing function removed - using EventKit now

def query_calendar(calendar_name=None, days=7):
    """Query specific calendar or all calendars"""
    events = get_calendar_events(days)
    if calendar_name:
        # Filter by calendar name if specified
        filtered_events = {}
        for date, date_events in events.items():
            filtered_date_events = [e for e in date_events if e.get('calendar') == calendar_name]
            if filtered_date_events:
                filtered_events[date] = filtered_date_events
        return filtered_events
    return events


def upcoming():
    """Get upcoming calendar events from Apple Calendar"""
    try:
        all_events = get_calendar_events(7)
        
        # Separate events by calendar type (you'll need to specify your actual calendar names)
        personal_events = {}
        family_events = {}
        
        for date, events in all_events.items():
            for event in events:
                calendar_name = event.get('calendar', '')
                
                # Map actual calendar names to categories
                if calendar_name in ['Personal', 'Private']:  # Your personal calendars
                    if date not in personal_events:
                        personal_events[date] = []
                    personal_events[date].append(event)
                elif calendar_name in ['Shara Davis']:  # Family calendar
                    if date not in family_events:
                        family_events[date] = []
                    family_events[date].append(event)
                else:
                    # Default to personal if unknown
                    if date not in personal_events:
                        personal_events[date] = []
                    personal_events[date].append(event)
        
        return json.dumps({"Mine": personal_events, "Family": family_events})
    except Exception as e:
        print(f"Error getting upcoming events: {e}")
        return json.dumps({"Mine": {}, "Family": {}, "Error": str(e)})

# Note: align function removed - not supported with read-only Apple Calendar access


def main():
    """Test Apple Calendar integration"""
    print("Testing Apple Calendar integration...")
    events = upcoming()
    print(events)

if __name__ == "__main__":
    main()
