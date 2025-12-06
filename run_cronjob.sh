#!/bin/bash

# AIRSS daily workflow - Simple Version
cd /Media/source/airss
/home/chris/miniforge3/bin/mamba activate
/home/chris/miniforge3/bin/python3 daily_workflow.py
# Log the check
echo "$(date): Daily Workflow completed" >> /home/chris/source/airss/logs/daily.log
