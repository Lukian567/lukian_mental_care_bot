from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.content import stubs


def scale_kb(prefix: str) -> InlineKeyboardMarkup:
    """Універсальна шкала від 1 до 5."""
    buttons = [
        [
            InlineKeyboardButton(text=str(i), callback_data=f"{prefix}:{i}")
            for i in range(1, 6)
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def sleep_duration_kb() -> InlineKeyboardMarkup:
    """Клавіатура для вибору тривалості сну (зберігаємо у хвилинах)."""
    buttons = [
        [InlineKeyboardButton(text="< 4 год", callback_data="sleep_dur:210")],
        [InlineKeyboardButton(text="4–6 год", callback_data="sleep_dur:300")],
        [InlineKeyboardButton(text="6–8 год", callback_data="sleep_dur:420")],
        [InlineKeyboardButton(text="> 8 год", callback_data="sleep_dur:540")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def morning_thought_kb() -> InlineKeyboardMarkup:
    """Вибір автоматичної думки зранку."""
    buttons = [
        [InlineKeyboardButton(text=stubs.THOUGHT_AGAIN, callback_data="thought:again")],
        [InlineKeyboardButton(text=stubs.THOUGHT_NOTHING, callback_data="thought:nothing")],
        [InlineKeyboardButton(text=stubs.THOUGHT_BETTER, callback_data="thought:better")],
        [InlineKeyboardButton(text=stubs.THOUGHT_TASK, callback_data="thought:task")],
        [InlineKeyboardButton(text=stubs.THOUGHT_NEUTRAL, callback_data="thought:neutral")],
        [
            InlineKeyboardButton(text=stubs.BTN_WRITE_CUSTOM, callback_data="thought:custom"),
            InlineKeyboardButton(text=stubs.BTN_SKIP, callback_data="thought:skip"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def morning_action_kb() -> InlineKeyboardMarkup:
    """Вибір реалістичної мікро-дії на сьогодні."""
    buttons = [
        [InlineKeyboardButton(text=stubs.ACTION_SELF_CARE, callback_data="action:self_care")],
        [InlineKeyboardButton(text=stubs.ACTION_WALK, callback_data="action:walk")],
        [InlineKeyboardButton(text=stubs.ACTION_STUDY_WORK, callback_data="action:work")],
        [InlineKeyboardButton(text=stubs.ACTION_SURVIVE, callback_data="action:survive")],
        [
            InlineKeyboardButton(text=stubs.BTN_WRITE_CUSTOM, callback_data="action:custom"),
            InlineKeyboardButton(text=stubs.BTN_SKIP, callback_data="action:skip"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def evening_fact_kb() -> InlineKeyboardMarkup:
    """Вибір факту дня ввечері."""
    buttons = [
        [InlineKeyboardButton(text=stubs.FACT_BED, callback_data="fact:bed")],
        [InlineKeyboardButton(text=stubs.FACT_BASE, callback_data="fact:base")],
        [InlineKeyboardButton(text=stubs.FACT_OUT, callback_data="fact:out")],
        [InlineKeyboardButton(text=stubs.FACT_PRODUCTIVE, callback_data="fact:prod")],
        [InlineKeyboardButton(text=stubs.FACT_NOTHING, callback_data="fact:nothing")],
        [InlineKeyboardButton(text=stubs.BTN_WRITE_CUSTOM, callback_data="fact:custom")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def action_done_kb() -> InlineKeyboardMarkup:
    """Статус реалізації мікро-дії."""
    buttons = [
        [InlineKeyboardButton(text=stubs.STATUS_DONE, callback_data="done:yes")],
        [InlineKeyboardButton(text=stubs.STATUS_PARTIAL, callback_data="done:part")],
        [InlineKeyboardButton(text=stubs.STATUS_FAIL, callback_data="done:no")],
        [InlineKeyboardButton(text=stubs.STATUS_NO_PLAN, callback_data="done:none")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def contact_quality_kb() -> InlineKeyboardMarkup:
    """Якість соціального контакту."""
    buttons = [
        [InlineKeyboardButton(text=stubs.CONTACT_GOOD, callback_data="contact:good")],
        [InlineKeyboardButton(text=stubs.CONTACT_WORK, callback_data="contact:work")],
        [InlineKeyboardButton(text=stubs.CONTACT_ALONE_IN_CROWD, callback_data="contact:alone")],
        [InlineKeyboardButton(text=stubs.CONTACT_AVOIDED, callback_data="contact:avoid")],
        [
            InlineKeyboardButton(text=stubs.BTN_WRITE_CUSTOM, callback_data="contact:custom"),
            InlineKeyboardButton(text=stubs.BTN_SKIP, callback_data="contact:skip"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def emotion_kb() -> InlineKeyboardMarkup:
    """Переважна емоція дня."""
    buttons = [
        [InlineKeyboardButton(text=stubs.EMO_SADNESS, callback_data="emo:sadness")],
        [InlineKeyboardButton(text=stubs.EMO_ANXIETY, callback_data="emo:anxiety")],
        [InlineKeyboardButton(text=stubs.EMO_ANGER, callback_data="emo:anger")],
        [InlineKeyboardButton(text=stubs.EMO_GUILT, callback_data="emo:guilt")],
        [InlineKeyboardButton(text=stubs.EMO_EMPTINESS, callback_data="emo:emptiness")],
        [InlineKeyboardButton(text=stubs.EMO_CALM, callback_data="emo:calm")],
        [InlineKeyboardButton(text=stubs.BTN_SKIP, callback_data="emo:skip")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def compassion_kb() -> InlineKeyboardMarkup:
    """Слова самопідтримки."""
    buttons = [
        [InlineKeyboardButton(text=stubs.COMPASSION_BEST, callback_data="comp:best")],
        [InlineKeyboardButton(text=stubs.COMPASSION_NORMAL, callback_data="comp:normal")],
        [InlineKeyboardButton(text=stubs.COMPASSION_ENOUGH, callback_data="comp:enough")],
        [InlineKeyboardButton(text=stubs.COMPASSION_TOMORROW, callback_data="comp:tomorrow")],
        [
            InlineKeyboardButton(text=stubs.BTN_WRITE_CUSTOM, callback_data="comp:custom"),
            InlineKeyboardButton(text=stubs.BTN_SKIP, callback_data="comp:skip"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)