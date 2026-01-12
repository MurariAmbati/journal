#!/usr/bin/env python3
"""
one-command setup for journal reminders

run this once:
    python3 ~/journal/reminders/quick_setup.py

it will set up daily 9 AM reminders automatically.
"""

import subprocess
import sys
import os
from pathlib import Path


def setup_launchd():
    """set up launchd agent"""
    reminder_script = Path(os.path.expanduser("~/journal/reminders/daily_reminder.py"))
    launch_agent_dir = Path(os.path.expanduser("~/Library/LaunchAgents"))
    launch_agent_file = launch_agent_dir / "com.murari.journal-reminder.plist"
    
    if not launch_agent_dir.exists():
        launch_agent_dir.mkdir(parents=True, exist_ok=True)
    
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.murari.journal-reminder</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{reminder_script}</string>
    </array>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>{os.path.expanduser('~/journal/reminders/reminder.log')}</string>
    
    <key>StandardErrorPath</key>
    <string>{os.path.expanduser('~/journal/reminders/reminder-error.log')}</string>
</dict>
</plist>
"""
    
    try:
        launch_agent_file.write_text(plist_content)
        print(f"✓ launch agent created")
        
        subprocess.run(
            ["launchctl", "load", str(launch_agent_file)],
            check=True
        )
        print("✓ launch agent loaded\n")
        
        print("✅ reminders set up successfully!")
        print(f"   you'll get a notification every day at 9 AM")
        print(f"   logs: {os.path.expanduser('~/journal/reminders/reminder.log')}\n")
        
        print("to disable reminders later:")
        print(f"   launchctl unload {launch_agent_file}")
        
        return 0
    
    except Exception as e:
        print(f"❌ error: {e}")
        return 1


def main():
    print("🚀 setting up journal reminders...\n")
    
    system = sys.platform
    if system != "darwin":
        print("⚠️  this script is optimized for macOS")
        print(f"   your system: {system}")
        return 1
    
    print("auto-selecting launchd (macOS recommended)...\n")
    return setup_launchd()


if __name__ == "__main__":
    sys.exit(main())
