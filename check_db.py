import asyncio
from sqlalchemy import select
from bot.db.base import async_session
from bot.db.models import DailyCheckin


async def main():
    async with async_session() as session:
        result = await session.execute(select(DailyCheckin))
        rows = result.scalars().all()
        
        print(f"\n📊 Всього записів у базі: {len(rows)}")
        for r in rows:
            print("—" * 50)
            print(f"ID: {r.id} | Період: {r.period.value} | Дата: {r.checkin_date}")
            if r.period.value == "morning":
                print(f"  • Сон: {r.sleep_duration_minutes} хв | Якість сну: {r.sleep_quality}/5")
                print(f"  • Рівень опору: {r.resistance_level}/5 | Рівень тривоги: {r.anxiety_level}/5")
            else:
                print(f"  • Факт дня: {r.day_fact}")
                print(f"  • Настрій: {r.mood_score}/5 | Соціальний контакт: {'Так' if r.social_contact else 'Ні'}")
            print(f"  • Повний JSON: {r.raw_payload}")
        print("—" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())