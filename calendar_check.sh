#!/bin/bash

# AIRSS Calendar Orchestrator - Simple Version
cd /Users/chris/source/airss

# broken env variable setup but ok. 
export BLUESKY_IDENTIFIER="landgull.bsky.social"
export BLUESKY_APP_PASSWORD="zrxg-qxzg-6dkr-76mn"
export BLUESKY_SERVICE_URL="https://bsky.social"
export ZOTERO_API_KEY="c8Y51VNOrDLwcNCQehQtDwLP"
export ZOTERO_USER_ID="cpbonnell"
venv/bin/python3 mcp_client.py
# Log the check
echo "$(date): Calendar check completed" >> /Users/chris/source/airss/logs/calendar_orchestrator.log
