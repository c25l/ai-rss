"""Load environment variables from .env file if it exists"""
import os
from pathlib import Path


def load_env():
    """Load environment variables from .env file in the current or parent directory"""
    # Look for .env file in current directory and up to parent
    current_dir = Path(__file__).parent
    env_file = current_dir / '.env'

    if not env_file.exists():
        # Try parent directory
        env_file = current_dir.parent / '.env'

    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    # Handle KEY=VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip().strip('"').strip("'")
                        os.environ[key.strip()] = value


# Load environment variables when module is imported
load_env()
