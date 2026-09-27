from aiogram.fsm.state import State, StatesGroup


class MorningCheckin(StatesGroup):
    sleep_duration = State()     # Скільки спав(-ла)
    sleep_quality = State()      # Якість сну (1-5)
    mood = State()               # Настрій зранку (1-5)
    resistance = State()         # Опір/важкість підйому (1-5)
    anxiety = State()            # Тривога зранку (1-5)
    thought = State()            # Перша автоматична думка (кнопка або текст)
    micro_action = State()       # Мікро-дія на день (кнопка або текст)


class EveningCheckin(StatesGroup):
    day_fact = State()           # Що відбулося (кнопка або текст)
    mood_score = State()         # Настрій дня (1-5)
    action_done = State()        # Чи вдалося зробити мікро-дію
    contact_quality = State()    # Якість контакту з людьми
    emotion = State()            # Переважна емоція
    emotion_intensity = State()  # Інтенсивність емоції (1-5)
    compassion = State()         # Самопідтримка / що сказав би другу