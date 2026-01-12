#!/usr/bin/env python3
"""
manual check: run anytime to see if journal is updated

usage:
    python3 ~/journal/reminders/check_journal.py
"""

import sys
from pathlib import Path
from datetime import datetime
import os


def main():
    journal_path = Path(os.path.expanduser("~/journal/journal1.md"))
    
    if not journal_path.exists():
        print(f"❌ journal not found at {journal_path}")
        return 1
    
    today = datetime.now().strftime("%B %d, %Y").lstrip("0").replace(" 0", " ")
    content = journal_path.read_text()
    
    print(f"checking journal for today's date: {today}\n")
    
    if f"## {today}" in content:
        print(f"✅ journal is updated for {today}")
        print(f"   keep it up! 📝\n")
        return 0
    else:
        print(f"⚠️  journal NOT updated for {today}")
        print(f"   go update it!\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
