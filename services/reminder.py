from database.db import SessionLocal
from database.models import Reminder
import datetime
import logging

def add_reminder(user_id: int, message: str, remind_at: datetime.datetime):
    # Add new reminder for specific user
    with SessionLocal() as session:
        reminder = Reminder(
            user_id=user_id,
            message=message, 
            remind_at=remind_at
        )
        session.add(reminder)
        session.commit()
        logging.info(f"Reminder added: user_id={user_id}, message={message}, remind_at={remind_at}")
        return reminder

def get_active_reminders(user_id: int):
    # Get all active reminders for specific user
    with SessionLocal() as session:
        return session.query(Reminder).filter(
            Reminder.user_id == user_id,
            Reminder.is_active == True
        ).all()

def get_due_reminders():
    # Get reminders that should be sent now (for all users)
    now = datetime.datetime.now()
    with SessionLocal() as session:
        return session.query(Reminder).filter(
            Reminder.is_active == True, 
            Reminder.remind_at <= now
        ).all()

def deactivate_reminder(reminder_id: int):
    # Deactivate reminder after sending
    with SessionLocal() as session:
        reminder = session.query(Reminder).get(reminder_id)
        if reminder:
            reminder.is_active = False
            session.commit()
            logging.info(f"Reminder deactivated: id={reminder_id}")
            return True
        return False

def delete_reminder(user_id: int, reminder_id: int):
    # Delete reminder for specific user
    with SessionLocal() as session:
        reminder = session.query(Reminder).filter(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id
        ).first()
        if reminder:
            session.delete(reminder)
            session.commit()
            return True
        return False 