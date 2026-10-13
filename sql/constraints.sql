-- Constraints and indexes that exist in the database.
-- Tables themselves are created by SQLAlchemy (see bot/db/models.py),
-- the foreign key below was added separately.
-- Note: there is no unique constraint on (telegram_user_id, checkin_date, period),
-- repeated check-ins are merged in the bot code (upsert in bot/db/repository.py).

ALTER TABLE daily_checkins
    ADD CONSTRAINT fk_daily_checkins_users
    FOREIGN KEY (telegram_user_id) REFERENCES users (telegram_user_id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS ix_daily_checkins_checkin_date ON daily_checkins (checkin_date);
CREATE INDEX IF NOT EXISTS ix_daily_checkins_telegram_user_id ON daily_checkins (telegram_user_id);
