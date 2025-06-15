from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.reminder import get_due_reminders, deactivate_reminder
from aiogram import Bot
import logging

async def send_due_reminders(bot: Bot):
    # Send reminders that are due
    try:
        reminders = get_due_reminders()
        for r in reminders:
            try:
                await bot.send_message(
                    r.user_id, 
                    f"🔔 Напоминание:\n\n{r.message}",
                    parse_mode=None
                )
                deactivate_reminder(r.id)
                logging.info(f"Reminder sent to user {r.user_id}: {r.message}")
            except Exception as e:
                logging.error(f"Failed to send reminder {r.id} to user {r.user_id}: {e}")
                # Deactivate reminder even if sending failed to avoid spam
                deactivate_reminder(r.id)
    except Exception as e:
        logging.error(f"Error in send_due_reminders: {e}")

scheduler = AsyncIOScheduler()

def setup_scheduler(bot: Bot):
    # Check for due reminders every minute
    scheduler.add_job(
        send_due_reminders, 
        'interval', 
        minutes=1, 
        args=[bot],
        id='reminder_job'
    )
    scheduler.start()
    logging.info("Scheduler started for reminders") 