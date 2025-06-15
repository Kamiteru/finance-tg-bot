# Entry point for the Telegram bot

from aiogram import Bot, Dispatcher
import asyncio
from config import BOT_TOKEN
from handlers import base_router, transaction_router, goal_router, reminder_router, converter_router, reports_router
from services.scheduler import setup_scheduler
from database.db import init_db
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

async def main():
    # Initialize database
    init_db()
    logging.info("Database initialized")
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(base_router)
    dp.include_router(transaction_router)
    dp.include_router(goal_router)
    dp.include_router(reminder_router)
    dp.include_router(converter_router)
    dp.include_router(reports_router)
    setup_scheduler(bot)
    
    logging.info("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 