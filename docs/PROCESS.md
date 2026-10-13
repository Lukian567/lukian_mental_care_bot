# How I built mental care bot

This file is the story of the whole project, from the first idea to the dashboard, with the decisions I made and the problems I had on the way. It is my first end to end project, so I wrote down not only what works, but also what went wrong.

## The idea

I wanted one project where I use everything from my courses in a real situation. The plan was simple, collect my own data every day, store it in a database, clean it with SQL, and show it in a dashboard. A Telegram bot was the easiest way to collect data, because I always have Telegram open and I can answer with buttons in half a minute.

The full path of the data looks like this, Telegram bot, PostgreSQL, SQL view, Google Sheets, Tableau Public.

## Step 1, the bot

The bot is written in Python with aiogram 3, and the questions are a small state machine, so each answer moves the user to the next question. I used APScheduler for the reminders, one in the morning and one in the evening. I made only this Python part with the help of AI, as my coding assistant, and I tested and ran everything myself.

I tried to keep the check in short, around thirty or forty five seconds, with buttons and scales from one to five. I did it on purpose, because long forms are boring and then people stop filling them, and I wanted clean data that is easy to compare.

## Step 2, the database

The data is stored in PostgreSQL, and SQLAlchemy 2.0 talks to it with asyncpg. There are two tables, users and daily checkins. One check in is one row, and a column called period says if it is morning or evening. If I do the same check in again for the same day, the bot updates the old row, so there are no duplicates. This logic is in the application code, there is no unique constraint in the database, and I know it would be safer to add one later.

I also keep the raw answers in a JSON column, in case I want to change the structure later. The foreign key between the tables has ON DELETE CASCADE, so when a user is deleted, the check ins are deleted too. The SQL for the key and the indexes is in the sql folder.

## Step 3, fake data

I did not have real data yet, so I filled the database with synthetic data for the summer months, with a SQL script, and the AI helped to design the patterns. For example, short sleep gives more anxiety, and doing the morning action gives a better evening mood. It was good enough to build the dashboard, but the data is too simple, and it does not look like a real human, so I never treat it as a real result.

## Step 4, the SQL view

Tableau likes one wide table, so I wrote a view called v_tableau_daily_journal. It joins the morning and the evening check in with a full join by user and date, so one day is one row. It also adds calculated fields like mood change during the day, sleep score, distress score, and a flag for short sleep, less than seven hours.

A small detail that confused me, the same date can appear two times in the view. It was not a bug, these were two different users. Now I check the user column first when something looks strange.

## Step 5, the dashboard

I built the dashboard in Tableau, and later I changed the colors to a warm pastel style, yellow, orange and purple blue, so it feels softer and more personal. It has key numbers, donut charts, a comparison of workdays and weekends, the action gap chart, an emotion map, and the mood trajectory.

Filters took me more time than I expected. At one moment they just disappeared because of a bug in Tableau, so I had to set them again. Because of this I learned a few things. A filter must be set to all using related data sources, or it changes only one sheet. A date filter on an aggregated field gives strange results, so it must use the raw date. And a user filter with a search box is much better when there are many users, so I used a dropdown with search.

I also cut the October rows in Tableau, because they were my test data, and they were making the statistics worse.

## Step 6, the automatic sync

At the beginning I planned to update the data in Tableau by hand once a month. Then I decided that the bot should send the data to Google Sheets by itself. I chose Google Sheets because it is easy to sync, and it works well for a private user who wants to update a Tableau Public dashboard.

For this I made a Google service account and I shared the sheet with it. The module sheets_sync reads the view and writes everything to the sheet with gspread. It writes the new values first and then clears the old rows that are left, so the sheet never stays empty. A scheduler job runs it every night at five to midnight, and there is also an admin command, so I can start the sync by hand and see the result in the chat.

Tableau Public can refresh Google Sheets sources about once every day, but my workbook uses a different type of connection, so I did not check if the automatic refresh really works for it. For now I update the dashboard by hand.

## Step 7, cleaning the project

Before I wrote the description, I deleted the files and code I did not need, like old stubs and a test script for the database. I removed alembic from the requirements, because I never used it. The secrets, the token and the Google key, are in the env file and they are ignored by git, and the repository has a blank env example for other people.

## Problems I had

At one moment a placeholder was still in my env file, and the check said everything is fine. Now I check the real values, not only that the field is not empty.

I also published the dashboard before I thought about the data under it. Anyone can download the data from a Tableau Public dashboard, so this is something to remember. The data in this project is synthetic, so it is safe, but with real data I would filter it before publishing and hide the text columns.

## What is still not done

The bot is not on a server, it works only when it runs on my laptop, so the nightly sync also works only then. The questions and the answers are in Ukrainian for now, and I want to add English and Polish later. The filters on the dashboard work, but they do not look good yet. The written analysis of the dashboard is the last part, and I will write it myself.

## What I learned

The biggest lesson is that the data part is only half of the work, the other half is to make it clear for another person. I also learned to do one small step at a time, test it, and make a commit, because it is much easier to find a mistake in a small change.
