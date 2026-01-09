#!/bin/bash

# AIRSS daily workflow - Simple Version
cd /home/chris/source/airss
source /home/chris/.bashrc
/home/chris/miniforge3/bin/python daily_workflow.py
# Log the check
echo "$(date): Daily Workflow completed" >> /home/chris/source/airss/logs/daily.log
