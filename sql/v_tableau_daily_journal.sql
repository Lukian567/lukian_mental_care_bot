-- Analytics view for Tableau: one row = one day for one user.
-- Morning and evening check-ins are stored as separate rows in daily_checkins,
-- here they are joined into one wide row (FULL JOIN on user + date).
-- Sleep deprivation threshold: 7 hours. Distress score = resistance + anxiety (2 to 10).

CREATE OR REPLACE VIEW public.v_tableau_daily_journal AS
WITH morning AS (
         SELECT DISTINCT ON (daily_checkins.telegram_user_id, daily_checkins.checkin_date) daily_checkins.telegram_user_id,
            daily_checkins.checkin_date,
            daily_checkins.sleep_hours,
            daily_checkins.sleep_quality,
            daily_checkins.morning_mood,
            daily_checkins.morning_resistance,
            daily_checkins.morning_anxiety,
            daily_checkins.morning_thought,
            daily_checkins.morning_action_anchor,
            daily_checkins.created_at AS morning_created_at
           FROM daily_checkins
          WHERE daily_checkins.period::text = 'morning'::text
        ), evening AS (
         SELECT DISTINCT ON (daily_checkins.telegram_user_id, daily_checkins.checkin_date) daily_checkins.telegram_user_id,
            daily_checkins.checkin_date,
            array_to_string(daily_checkins.activity_domains, ', '::text) AS activity_domains,
            daily_checkins.evening_mood,
            daily_checkins.action_result,
            daily_checkins.social_state,
            daily_checkins.dominant_emotion,
            daily_checkins.emotion_intensity,
            daily_checkins.cognitive_closure,
            daily_checkins.created_at AS evening_created_at
           FROM daily_checkins
          WHERE daily_checkins.period::text = 'evening'::text
        )
 SELECT
        CASE
            WHEN m.telegram_user_id IS NOT NULL THEN m.telegram_user_id
            ELSE e.telegram_user_id
        END AS telegram_user_id,
    u.first_name,
    u.username,
    u.timezone,
        CASE
            WHEN m.checkin_date IS NOT NULL THEN m.checkin_date
            ELSE e.checkin_date
        END AS checkin_date,
    to_char(
        CASE
            WHEN m.checkin_date IS NOT NULL THEN m.checkin_date
            ELSE e.checkin_date
        END::timestamp with time zone, 'Dy'::text) AS day_name,
    EXTRACT(isodow FROM
        CASE
            WHEN m.checkin_date IS NOT NULL THEN m.checkin_date
            ELSE e.checkin_date
        END) = ANY (ARRAY[6::numeric, 7::numeric]) AS is_weekend,
    m.telegram_user_id IS NOT NULL AS has_morning,
    e.telegram_user_id IS NOT NULL AS has_evening,
    m.telegram_user_id IS NOT NULL AND e.telegram_user_id IS NOT NULL AS is_full_day,
    m.sleep_hours,
    m.sleep_quality,
    m.morning_mood,
    m.morning_resistance,
    m.morning_anxiety,
    m.morning_thought,
    m.morning_action_anchor,
    e.activity_domains,
    e.evening_mood,
    e.action_result,
    e.social_state,
    e.dominant_emotion,
    e.emotion_intensity,
    e.cognitive_closure,
    e.evening_mood - m.morning_mood AS mood_delta,
    m.sleep_hours < 7.0 AS is_sleep_deprived,
    round(m.sleep_hours * (m.sleep_quality::numeric / 5.0), 2) AS sleep_score,
    m.morning_resistance + m.morning_anxiety AS distress_score,
    e.action_result = 'DONE'::text AS is_action_done,
    m.morning_created_at,
    e.evening_created_at
   FROM morning m
     FULL JOIN evening e ON m.telegram_user_id = e.telegram_user_id AND m.checkin_date = e.checkin_date
     LEFT JOIN users u ON u.telegram_user_id =
        CASE
            WHEN m.telegram_user_id IS NOT NULL THEN m.telegram_user_id
            ELSE e.telegram_user_id
        END
  ORDER BY (
        CASE
            WHEN m.checkin_date IS NOT NULL THEN m.checkin_date
            ELSE e.checkin_date
        END), u.telegram_user_id DESC;
