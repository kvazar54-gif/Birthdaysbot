import asyncio
from aiogram import Dispatcher, Bot
from app.database.models import async_main
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import aiosqlite
from dotenv import load_dotenv
import os


from app.handlers import router

load_dotenv()
bot = Bot(os.getenv('TOKEN'))
dp = Dispatcher()


async def check_birthdays(bot):

    now = datetime.now()

    reminder_days = [0, 3]
    
    async with aiosqlite.connect('db.sqlite3') as db:
        for days_ahead in reminder_days:
            target_date = now + timedelta(days=days_ahead)
            target_str = target_date.strftime('%m-%d')
            
            # Основной запрос
            async with db.execute(
                "SELECT tg_id, name, event_date FROM celebrants WHERE strftime('%m-%d', event_date) = ?",
                (target_str,)
            ) as cursor:
                celebrants = await cursor.fetchall()
            

            if not is_leap_year(target_date.year) and target_str == '03-01':
                async with db.execute(
                    "SELECT tg_id, name, event_date FROM celebrants WHERE strftime('%m-%d', event_date) = '02-29'",
                ) as cursor:
                    leap_celebrants = await cursor.fetchall()
                    celebrants.extend(leap_celebrants)
            
            # Рассылаем уведомления
            for tg_id, name, event_date in celebrants:
                try:
                    message = generate_message(name, days_ahead, event_date, target_date)
                    await bot.send_message(tg_id, message)
                except Exception as e:
                    print(f"Ошибка отправки сообщения {tg_id}: {e}")


def is_leap_year(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def generate_message(name, days_ahead, event_date, target_date):
    if days_ahead == 0:
        # Сегодня день рождения
        if event_date.endswith('02-29') and not is_leap_year(target_date.year):
            return f"🎉 Сегодня день рождения у {name}! (29 февраля, отмечаем сегодня!)"
        else:
            return f"🎉 Сегодня день рождения у {name}!"
    elif days_ahead == 3:
        return f"🔔 Напоминание! Через 3 дня день рождения у {name}!"


async def main():
    await async_main()
    dp.include_router(router)
    
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    scheduler.add_job(check_birthdays, "cron", hour=9, minute=0, args=(bot,))
    scheduler.start()
    
    print("🤖 Бот запущен! Проверка дней рождения в 09:00 МСК.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
