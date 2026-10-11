from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    """Первинне налаштування графіку та зміна розкладу."""
    timezone = State()
    morning_time = State()
    morning_time_custom = State()
    evening_time = State()
    evening_time_custom = State()


class MorningCheckin(StatesGroup):
    """Ранковий протокол (6 кроків)."""
    sleep_hours = State()
    sleep_hours_custom = State()
    sleep_quality = State()
    morning_mood = State()
    morning_resistance = State()
    morning_anxiety = State()
    morning_thought = State()
    morning_thought_custom = State()
    morning_action = State()
    morning_action_custom = State()


class EveningCheckin(StatesGroup):
    """Вечірній протокол (6 кроків)."""
    activity_domains = State()
    activity_domains_custom = State()
    evening_mood = State()
    action_result = State()
    social_state = State()
    social_custom = State()
    dominant_emotion = State()
    dominant_emotion_custom = State()
    emotion_intensity = State()
    cognitive_closure = State()
    cognitive_closure_custom = State()


class ResetData(StatesGroup):
    """Підтвердження повного видалення даних."""
    confirm = State()

