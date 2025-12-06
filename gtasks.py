from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth import get_google_credentials


class Tasks:
    def __init__(self):
        # Use shared OAuth credentials for Calendar, Gmail, and Tasks
        self.creds = get_google_credentials()
        self.service = build('tasks', 'v1', credentials=self.creds)

    def get_task_lists(self):
        """Get all task lists."""
        try:
            results = self.service.tasklists().list().execute()
            task_lists = results.get('items', [])

            parsed_lists = []
            for tlist in task_lists:
                parsed_lists.append({
                    'id': tlist['id'],
                    'title': tlist['title'],
                    '_tasklist_id': tlist['id']
                })

            return parsed_lists

        except HttpError as error:
            print(f'An error occurred: {error}')
            return []

    def get_tasks(self, tasklist_id: str = 'MDc5NTU2OTcwMzA2MTI0MDEwNzI6MDow', show_completed: bool = False,
                  show_hidden: bool = False, limit: int = 100):
        """
        Get tasks from a task list.

        Args:
            tasklist_id: ID of task list (default: 'MDc5NTU2OTcwMzA2MTI0MDEwNzI6MDow')
            show_completed: Include completed tasks
            show_hidden: Include hidden (deleted) tasks
            limit: Maximum number of tasks to return
        """
        try:
            results = self.service.tasks().list(
                tasklist=tasklist_id,
                maxResults=limit,
                showCompleted=show_completed,
                showHidden=show_hidden
            ).execute()

            tasks = results.get('items', [])

            parsed_tasks = []
            for task in tasks:
                parsed = self._parse_task(task, tasklist_id)
                if parsed:
                    parsed_tasks.append(parsed)

            return parsed_tasks

        except HttpError as error:
            print(f'An error occurred: {error}')
            return []

    def get_all_tasks(self, show_completed: bool = False, limit: int = 100):
        """Get tasks from all task lists."""
        all_tasks = []

        task_lists = self.get_task_lists()
        for tlist in task_lists:
            tasks = self.get_tasks(
                tasklist_id=tlist['id'],
                show_completed=show_completed,
                limit=limit
            )
            # Add task list name to each task
            for task in tasks:
                task['list_name'] = tlist['title']
            all_tasks.extend(tasks)

        return all_tasks

    def create_task(self, title: str, notes: str = "", due: datetime = None,
                   tasklist_id: str = 'MDc5NTU2OTcwMzA2MTI0MDEwNzI6MDow'):
        """
        Create a new task.

        Args:
            title: Task title
            notes: Task description/notes
            due: Due date (optional)
            tasklist_id: ID of task list (default: 'MDc5NTU2OTcwMzA2MTI0MDEwNzI6MDow')
        """
        try:
            task_body = {
                'title': title,
            }

            if notes:
                task_body['notes'] = notes

            if due:
                # Tasks API expects RFC 3339 timestamp
                task_body['due'] = due.isoformat() + 'Z' if due.tzinfo is None else due.isoformat()

            task = self.service.tasks().insert(
                tasklist=tasklist_id,
                body=task_body
            ).execute()

            return self._parse_task(task, tasklist_id)

        except HttpError as error:
            print(f'An error occurred: {error}')
            return None

    def update_task(self, task_dict: dict, title: str = None, notes: str = None,
                   due: datetime = None, status: str = None):
        """
        Update an existing task.

        Args:
            task_dict: Task dict from get_tasks or get_all_tasks methods
            title: New title (optional)
            notes: New notes (optional)
            due: New due date (optional)
            status: New status - 'completed' or 'needsAction' (optional)
        """
        try:
            if '_task_id' not in task_dict or '_tasklist_id' not in task_dict:
                raise ValueError("Task dict must come from get_tasks or get_all_tasks")

            task_id = task_dict['_task_id']
            tasklist_id = task_dict['_tasklist_id']

            # Fetch current task
            task = self.service.tasks().get(
                tasklist=tasklist_id,
                task=task_id
            ).execute()

            # Update fields
            if title is not None:
                task['title'] = title
            if notes is not None:
                task['notes'] = notes
            if due is not None:
                task['due'] = due.isoformat() + 'Z' if due.tzinfo is None else due.isoformat()
            if status is not None:
                task['status'] = status
                if status == 'completed':
                    task['completed'] = datetime.utcnow().isoformat() + 'Z'
                else:
                    # Remove completed timestamp if uncompleting
                    task.pop('completed', None)

            # Update the task
            updated_task = self.service.tasks().update(
                tasklist=tasklist_id,
                task=task_id,
                body=task
            ).execute()

            return self._parse_task(updated_task, tasklist_id)

        except HttpError as error:
            print(f'An error occurred: {error}')
            return None

    def complete_task(self, task_dict: dict):
        """Mark a task as completed."""
        return self.update_task(task_dict, status='completed')

    def uncomplete_task(self, task_dict: dict):
        """Mark a task as not completed."""
        return self.update_task(task_dict, status='needsAction')

    def delete_task(self, task_dict: dict):
        """Delete a task."""
        try:
            if '_task_id' not in task_dict or '_tasklist_id' not in task_dict:
                raise ValueError("Task dict must come from get_tasks or get_all_tasks")

            task_id = task_dict['_task_id']
            tasklist_id = task_dict['_tasklist_id']

            self.service.tasks().delete(
                tasklist=tasklist_id,
                task=task_id
            ).execute()

            return {"status": "deleted", "title": task_dict['title']}

        except HttpError as error:
            print(f'An error occurred: {error}')
            return None

    def _parse_task(self, task, tasklist_id):
        """Parse Google Task into consistent format."""
        try:
            title = task.get('title', 'No Title')
            notes = task.get('notes', '')
            status = task.get('status', 'needsAction')

            # Parse due date if present
            due = None
            if 'due' in task:
                try:
                    due = datetime.fromisoformat(task['due'].replace('Z', '+00:00'))
                except:
                    pass

            # Parse completed date if present
            completed = None
            if 'completed' in task:
                try:
                    completed = datetime.fromisoformat(task['completed'].replace('Z', '+00:00'))
                except:
                    pass

            task_id = task.get('id', '')

            return {
                "title": title,
                "notes": notes,
                "status": status,
                "due": due,
                "completed": completed,
                "is_completed": status == 'completed',
                "_task_id": task_id,
                "_tasklist_id": tasklist_id
            }
        except Exception as e:
            print(f"Error parsing task: {e}")
            return None


if __name__ == "__main__":
    # Test usage
    print("Initializing Google Tasks...")
    tasks = Tasks()

    print("\nTask Lists:")
    task_lists = tasks.get_task_lists()
    for i, tlist in enumerate(task_lists):
        print(f"{i+1}. {tlist['title']} (ID: {tlist['id']})")

    print("\n" + "="*60)
    print("All Tasks (incomplete only):")
    all_tasks = tasks.get_all_tasks()#show_completed=False)

    if not all_tasks:
        print("No tasks found!")
    else:
        for i, task in enumerate(all_tasks):
            print(f"\n{i+1}. {task['title']}")
            print(f"   List: {task.get('list_name', 'Unknown')}")
            if task['notes']:
                print(f"   Notes: {task['notes']}")
            if task['due']:
                print(f"   Due: {task['due']}")
            print(f"   Status: {task['status']}")
