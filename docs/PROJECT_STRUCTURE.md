# Project structure

This file explains what each file in the repository does, so it is easier to find your way around the code. The story of how the project was built is in [PROCESS.md](PROCESS.md).

## Root

| File | What it does |
| --- | --- |
| README.md | Short description of the project, the dashboard link and how to run the bot. |
| requirements.txt | Python packages the bot needs. |
| .env.example | Empty template of the settings. Copy it to .env and fill in your own values. |
| .gitignore | Keeps secrets like .env and the Google key out of git. |

## bot

The Python part. It was written with the help of AI and tested by me.

| File | What it does |
| --- | --- |
| bot/main.py | Entry point. Creates the database tables, sets the bot commands, starts the scheduler and starts polling. |
| bot/config.py | Reads the settings from .env, for example the bot token, the database address and the Google Sheet. |
| bot/scheduler.py | Runs the jobs in the background. It sends the reminders to users at the time they chose and runs the nightly Google Sheets sync. |
| bot/sheets_sync.py | Reads the SQL view and writes it to Google Sheets with gspread. Used by the nightly job and by the admin sync command. |

## bot/db

| File | What it does |
| --- | --- |
| bot/db/base.py | Database connection and the session helper. |
| bot/db/models.py | Tables as Python classes, users and daily_checkins, and the period type, morning or evening. |
| bot/db/repository.py | All database queries in one place. Saves the check ins, updates the old answer if the same check in is repeated, and counts the streak and the weekly stats. |

## bot/routers

Each router handles one part of the chat.

| File | What it does |
| --- | --- |
| bot/routers/common.py | Start, onboarding, settings, stats, the data reset, and the admin sync command. |
| bot/routers/morning.py | The morning check in, question by question. |
| bot/routers/evening.py | The evening check in, question by question. |

## bot/keyboards and bot/states

| File | What it does |
| --- | --- |
| bot/keyboards/checkin_kb.py | All the buttons for the menus and for the answers. |
| bot/states/checkin_states.py | The steps of each flow, onboarding, morning check in, evening check in and data reset. The bot uses them to remember where the user is. |

## sql

| File | What it does |
| --- | --- |
| sql/v_tableau_daily_journal.sql | The view that joins morning and evening into one row per day and adds the calculated fields. Tableau reads this data. |
| sql/constraints.sql | The foreign key between users and check ins, and two indexes. |

## docs

| File | What it does |
| --- | --- |
| docs/PROCESS.md | The story of the build, with decisions and problems. |
| docs/PROJECT_STRUCTURE.md | This file. |

## How the data moves

A user answers in Telegram, the routers save the answers through the repository into PostgreSQL, the SQL view reshapes them, the sync module sends the view to Google Sheets every night, and Tableau Public shows the sheet.
