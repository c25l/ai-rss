#!/usr/bin/env /Users/chris/source/airss/venv/bin/python3
"""
MCP Server: Enhanced Outbox Service  
Provides accumulative document building with add/send_all functionality
"""

from datetime import datetime, timedelta, timezone  
from dateutil import parser,tz
import subprocess
from markdown import markdown
import feeds 
import aiohttp 
import numpy as np
import requests
import calendar_manually
import airss_base
import psycopg2
import smtplib
from email.message import EmailMessage
from modules import research, emailer,journal, news#, spaceweather

def main():
    # Note: Calendar alignment functionality removed as requested
    # (align functions won't work with read-only iCal access)
    out = []
    document = [news.News(), journal.Journal(), research.Research()]
    for xx in document:
        xx.pull_data()
        temp = xx.output()
        if xx:
            out.append(xx.section_title())
            out.append(temp)
            out.append("---")
    emailer.send_email("\n\n".join(out))


if __name__ == "__main__":
    main()
