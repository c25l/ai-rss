"""
Simple ntfy.sh notification module for H3lPeR
"""
import os
import requests
from typing import Optional


class Notifier:
    """Simple notifier that sends plain text messages to ntfy.sh"""

    def __init__(self):
        """Initialize the notifier with topic from environment"""
        self.topic = os.getenv('NTFYSH_TOPIC')
        if not self.topic:
            raise ValueError("NTFYSH_TOPIC environment variable not set")
        self.url = f"https://ntfy.sh/{self.topic}"

    def send(self, message: str, timeout: int = 10) -> bool:
        """
        Send a plain text notification to ntfy.sh

        Args:
            message: The notification text to send
            timeout: Request timeout in seconds (default: 10)

        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            response = requests.post(
                self.url,
                data=message.encode('utf-8'),
                timeout=timeout
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to send notification: {e}")
            return False


if __name__ == "__main__":
    # Test the notifier
    from dotenv import load_dotenv
    import os
    from pathlib import Path

    # Load .env from the same directory as this file
    env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)

    notifier = Notifier()
    success = notifier.send("Test notification from H3lPeR notifier.py")
    print(f"Notification sent: {success}")
