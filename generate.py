import subprocess
import json

def generate(prompt):
    """Generate text using Claude CLI"""
    try:
        # Use Claude CLI with print mode for direct output
        result = subprocess.run(
            ["/opt/homebrew/bin/claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=180  # Increased timeout for newsletter generation
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"Claude CLI error (code {result.returncode}): {result.stderr}")
            return ""
            
    except subprocess.TimeoutExpired:
        print("Claude CLI timed out")
        return ""
    except Exception as e:
        print(f"Generation error: {e}")
        return ""

def parse(response):
    lines = response.split("\n")
    if lines[0].startswith("```"):
        lines = lines[1]
    if lines[-1].endswith("```"):
        lines = lines[:-1]
    return json.reads("\n".join(lines))
