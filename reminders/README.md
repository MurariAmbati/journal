# journal reminders

python scripts for daily journal reminders.

## quick start

### one-command setup (macOS)

```bash
python3 ~/journal/reminders/quick_setup.py
```

you'll get a notification every day at 9 AM reminding you to update your journal.

---

## what's here

### `daily_reminder.py`
the main reminder script. checks if the journal was updated today and sends a notification.

```bash
python3 ~/journal/reminders/daily_reminder.py
```

### `setup_reminders.py`
interactive setup script. choose between cron or launchd.

```bash
python3 ~/journal/reminders/setup_reminders.py
```

### `quick_setup.py`
fastest setup for macOS. auto-configures launchd.

```bash
python3 ~/journal/reminders/quick_setup.py
```

### `check_journal.py`
manual check anytime. tells you if today's journal entry exists.

```bash
python3 ~/journal/reminders/check_journal.py
```

---

## options

### option 1: launchd (macOS, recommended)

automatically runs your reminder at 9 AM daily. survives reboots, integrates with macOS.

```bash
python3 quick_setup.py
```

**to disable:**
```bash
launchctl unload ~/Library/LaunchAgents/com.murari.journal-reminder.plist
```

**to re-enable:**
```bash
launchctl load ~/Library/LaunchAgents/com.murari.journal-reminder.plist
```

### option 2: cron (all unix systems)

```bash
python3 setup_reminders.py
# choose option 1
```

**to edit the time:**
```bash
crontab -e
```

**to remove:**
```bash
crontab -r
```

### option 3: manual check anytime

```bash
python3 check_journal.py
```

---

## what the reminder does

1. checks if `~/journal/CLIMATE_NETHERLANDS_JOURNAL.md` has an entry for today
2. if not, sends a native macOS or linux notification
3. optionally opens the journal in your default editor

---

## customization

### change the time (launchd)

edit `~/Library/LaunchAgents/com.murari.journal-reminder.plist`:

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>9</integer>    <!-- change this to your preferred hour (0-23) -->
    <key>Minute</key>
    <integer>0</integer>    <!-- change this to your preferred minute (0-59) -->
</dict>
```

then reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.murari.journal-reminder.plist
launchctl load ~/Library/LaunchAgents/com.murari.journal-reminder.plist
```

### change the time (cron)

```bash
crontab -e
```

find the line with `daily_reminder.py` and edit the time:
```
# minute hour day month day-of-week command
0      9    *   *     *           /usr/bin/python3 ~/journal/reminders/daily_reminder.py
```

---

## logs

if using launchd, check logs here:
- `~/journal/reminders/reminder.log` - standard output
- `~/journal/reminders/reminder-error.log` - errors
