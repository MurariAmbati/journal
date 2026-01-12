# journal

personal research journal for the KINGDOM climate model (King Integrated Decision-Operand Generated Intelligence for Netherlands Operations & Mitigation)

## overview

this repo contains:
- **journal1.md** - daily research journal entries tracking work on the KINGDOM multi-hazard climate risk model
- **reminders/** - python scripts for automated daily journal reminders via launchd (macOS)

## quick start

### set up reminders
```bash
python3 reminders/quick_setup.py
```

you'll get daily notifications at:
- **5:10 PM CST** - first reminder
- **9:00 PM CST** - follow-up reminder (if not submitted)

### manual checks
```bash
# check if journal is updated today
python3 reminders/check_journal.py

# open journal in your default editor
open journal1.md
```

## reminder scripts

- **daily_reminder.py** - main script that checks if journal was updated today and sends a notification
- **quick_setup.py** - one-command setup for macOS (auto-configures launchd)
- **setup_reminders.py** - interactive setup menu (cron or launchd)
- **check_journal.py** - manual verification script

see `reminders/README.md` for detailed configuration options.

## journal format

entries follow this format:
```markdown
## [month date, year] - [hours spent] [location]

what got built:
- brief summary of work completed

what i learned today:
1. key insight or learning
2. another learning
3. etc

what's next:
- upcoming work or next steps
```

## about KINGDOM

KINGDOM is a multi-hazard, causal decision-support model for Dutch climate adaptation. it uses:
- structural causal models for multi-sector coupling
- multi-fidelity architecture (screening → emulation → escalation)
- uncertainty decomposition across scenario, parameter, model-form, and data sources
