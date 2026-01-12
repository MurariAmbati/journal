#!/usr/bin/env python3
"""
daily journal reminder

checks if the journal was updated today and sends a reminder if not.
works with macOS (uses osascript for notifications) and linux (uses notify-send).
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

JOURNAL_PATH = Path(os.path.expanduser("~/journal/journal1.md"))


def get_today_date():
    """return today's date in the format used in the journal"""
    return datetime.now().strftime("%B %d, %Y").lstrip("0").replace(" 0", " ")


def journal_updated_today():
    """check if the journal has been updated with today's date"""
    if not JOURNAL_PATH.exists():
        print(f"❌ journal not found at {JOURNAL_PATH}")
        return False

    today = get_today_date()
    content = JOURNAL_PATH.read_text()
    
    # check if today's date appears in the journal
    if f"## {today}" in content:
        return True
    
    return False


def send_macos_notification(title, message):
    """send a native macOS notification"""
    script = f'display notification "{message}" with title "{title}"'
    subprocess.run(["osascript", "-e", script])


def send_linux_notification(title, message):
    """send a native linux notification"""
    subprocess.run(["notify-send", title, message])


def send_notification(title, message):
    """send a notification (os-agnostic)"""
    system = sys.platform
    
    try:
        if system == "darwin":  # macOS
            send_macos_notification(title, message)
        elif system == "linux":
            send_linux_notification(title, message)
        else:
            print(f"⚠️  unsupported system: {system}. notification not sent.")
            return False
        return True
    except Exception as e:
        print(f"❌ notification failed: {e}")
        return False


def open_journal():
    """open the journal in the default editor"""
    system = sys.platform
    
    try:
        if system == "darwin":  # macOS
            subprocess.run(["open", str(JOURNAL_PATH)])
        elif system == "linux":
            subprocess.run(["xdg-open", str(JOURNAL_PATH)])
    except Exception as e:
        print(f"❌ could not open journal: {e}")


def main():
    """main reminder check"""
    today = get_today_date()
    
    if journal_updated_today():
        print(f"✅ journal updated today ({today}). nice work!")
        return 0
    
    print(f"⚠️  journal not updated today ({today})")
    
    # send notification
    title = "📓 journal reminder"
    message = f"don't forget to update your climate journal for {today}!"
    
    if send_notification(title, message):
        print("✓ notification sent")
    
    # ask if user wants to open the journal
    response = input("\nopen journal now? (y/n): ").strip().lower()
    if response == "y":
        open_journal()
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
