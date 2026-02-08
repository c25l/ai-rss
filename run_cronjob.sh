#!/bin/bash

# H3lPeR daily workflow - Simple Version
cd /home/chris/source/H3lPeR
source /home/chris/.bashrc
/home/chris/miniforge3/bin/python daily_workflow_agent.py
# Log the check
echo "$(date): Daily Workflow completed" >> /home/chris/source/H3lPeR/logs/daily.log
