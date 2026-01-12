#!/usr/bin/env python3
"""
cron-based reminder setup for macOS

adds a cron job to check the journal daily at 9 AM.
run this once to set up the reminder.
"""

import subprocess
import os
from pathlib import Path


def setup_cron():
    """set up a daily cron job for the reminder"""
    
    reminder_script = Path(os.path.expanduser("~/journal/reminders/daily_reminder.py"))
    
    if not reminder_script.exists():
        print(f"❌ reminder script not found at {reminder_script}")
        return False
    
    # cron job: run daily at 9 AM (adjust time as needed)
    # minute hour day month day-of-week command
    cron_job = f"0 9 * * * /usr/bin/python3 {reminder_script}\n"
    
    try:
        # get current crontab
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )
        current_crontab = result.stdout
    except subprocess.CalledProcessError:
        # no crontab exists yet
        current_crontab = ""
    
    # check if job already exists
    if str(reminder_script) in current_crontab:
        print("✓ cron job already exists")
        return True
    
    # add new job
    new_crontab = current_crontab + cron_job
    
    try:
        # set the new crontab
        process = subprocess.Popen(
            ["crontab", "-"],
            stdin=subprocess.PIPE,
            text=True
        )
        process.communicate(input=new_crontab)
        
        if process.returncode == 0:
            print("✅ cron job set up successfully!")
            print(f"   runs daily at 9 AM")
            print(f"   to edit: crontab -e")
            print(f"   to remove: crontab -r")
            return True
        else:
            print("❌ failed to set cron job")
            return False
    
    except Exception as e:
        print(f"❌ error setting cron job: {e}")
        return False


def setup_launch_agent():
    """
    alternative: set up a launchd agent for macOS (more robust than cron).
    this runs at login and checks periodically.
    """
    
    reminder_script = Path(os.path.expanduser("~/journal/reminders/daily_reminder.py"))
    launch_agent_dir = Path(os.path.expanduser("~/Library/LaunchAgents"))
    launch_agent_file = launch_agent_dir / "com.murari.journal-reminder.plist"
    
    if not launch_agent_dir.exists():
        print(f"creating {launch_agent_dir}")
        launch_agent_dir.mkdir(parents=True, exist_ok=True)
    
    # plist content for launchd
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
    
    <key>StartInterval</key>
    <integer>86400</integer>
    
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
        print(f"✅ launch agent created at {launch_agent_file}")
        
        # load the agent
        subprocess.run(
            ["launchctl", "load", str(launch_agent_file)],
            check=True
        )
        print("✅ launch agent loaded")
        print(f"   logs: {os.path.expanduser('~/journal/reminders/reminder.log')}")
        print(f"   to unload: launchctl unload {launch_agent_file}")
        return True
    
    except Exception as e:
        print(f"❌ error setting up launch agent: {e}")
        return False


def main():
    """choose setup method"""
    print("journal reminder setup\n")
    print("choose a method:")
    print("1. cron (traditional, simple)")
    print("2. launchd (macOS recommended)")
    
    choice = input("\nselect (1 or 2): ").strip()
    
    if choice == "1":
        if setup_cron():
            print("\n✓ setup complete!")
    elif choice == "2":
        if setup_launch_agent():
            print("\n✓ setup complete!")
    else:
        print("❌ invalid choice")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
