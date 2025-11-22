#!/bin/bash

# AIRSS daily workflow - Simple Version
cd /Users/chris/source/airss
source venv/bin/activate
python3 daily_workflow.py
# Log the check
echo "$(date): Daily Workflow completed" >> /Users/chris/source/airss/logs/daily.log
