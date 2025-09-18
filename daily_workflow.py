#!/usr/bin/env /Users/chris/source/airss/venv/bin/python3
import claude

def main():

    prompt="/utilities:Daily_Workflow (MCP)"
    claude.Claude().generate(prompt)

if __name__ == "__main__":
    main()
