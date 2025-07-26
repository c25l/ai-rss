#!/bin/bash
# Script to run the AIRSS MCP servers

echo "Starting AIRSS MCP Servers..."

# Activate virtual environment and set PYTHONPATH
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Check if Python dependencies are installed in the virtual environment
python -c "import mcp, feedparser, sklearn, numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Missing dependencies in virtual environment. Installing..."
    pip install mcp feedparser scikit-learn numpy beautifulsoup4 requests
fi

# Function to run server with error handling
run_server() {
    local server_name=$1
    local server_file=$2
    
    echo "Starting $server_name..."
    
    # Check if it's a Python or Node.js server
    if [[ "$server_file" == *.py ]]; then
        # Python server
        ./venv/bin/python "$server_file" &
    else
        # Node.js server
        node "$server_file" &
    fi
    
    local pid=$!
    echo "$server_name started with PID $pid"
    
    # Store PID for cleanup
    echo $pid >> /tmp/airss_mcp_pids.txt
    
    # Give it a moment to start up
    sleep 0.5
}

# Clean up any existing PID file
rm -f /tmp/airss_mcp_pids.txt

# Start all servers (orchestration now via calendar)
run_server "RSS Fetch Service" "mcp_server_1.py"
run_server "Email Service" "mcp_server_2.py" 
# run_server "Orchestration Service" "mcp_server_3.py"  # DISABLED: Now using calendar events
run_server "Google Calendar Service" "google-calendar-mcp/build/index.js"
run_server "Playwright Browser Service" "playwright-mcp/cli.js"
# Set Bluesky environment variables and run server
echo "Starting Bluesky Service..."
export BLUESKY_IDENTIFIER="landgull.bsky.social"
export BLUESKY_APP_PASSWORD="zrxg-qxzg-6dkr-76mn"
export BLUESKY_SERVICE_URL="https://bsky.social"
node "bsky-mcp-server/build/src/index.js" &
pid=$!
echo "Bluesky Service started with PID $pid"
echo $pid >> /tmp/airss_mcp_pids.txt
sleep 0.5

echo "All AIRSS MCP servers started!"
echo "To stop all servers, run: ./stop_mcp_servers.sh"
