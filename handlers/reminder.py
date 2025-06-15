from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from handlers.base import main_menu
from services.reminder import add_reminder, get_active_reminders, delete_reminder
from datetime import datetime, timedelta
import logging

router = Router()

class ReminderState(StatesGroup):
    waiting_for_message = State()
    waiting_for_datetime = State()

@router.message(Command("add_reminder"))
async def add_reminder_start(message: types.Message, state: FSMContext):
    await state.set_state(ReminderState.waiting_for_message)
    await message.answer("⏰ Enter reminder message:")

@router.message(ReminderState.waiting_for_message)
async def reminder_message_handler(message: types.Message, state: FSMContext):
    message_text = message.text.strip()
    if not message_text:
        await message.answer("❌ Message cannot be empty. Try again:")
        return
    if len(message_text) > 200:
        await message.answer("❌ Message too long (max 200 characters). Try again:")
        return
    
    await state.update_data(reminder_message=message_text)
    await state.set_state(ReminderState.waiting_for_datetime)
    
    # Create keyboard for time options
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="In 1 hour"), types.KeyboardButton(text="In 3 hours")],
            [types.KeyboardButton(text="Tomorrow"), types.KeyboardButton(text="In 1 week")],
            [types.KeyboardButton(text="Custom date/time"), types.KeyboardButton(text="Cancel")]
        ],
        resize_keyboard=True
    )
    await message.answer("📅 When should I remind you?", reply_markup=kb)

@router.message(ReminderState.waiting_for_datetime)
async def reminder_datetime_handler(message: types.Message, state: FSMContext):
    if message.text == "Cancel":
        await state.clear()
        await message.answer("❌ Reminder creation cancelled", reply_markup=main_menu)
        return
    
    remind_at = None
    
    if message.text == "In 1 hour":
        remind_at = datetime.now() + timedelta(hours=1)
    elif message.text == "In 3 hours":
        remind_at = datetime.now() + timedelta(hours=3)
    elif message.text == "Tomorrow":
        remind_at = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
    elif message.text == "In 1 week":
        remind_at = datetime.now() + timedelta(weeks=1)
    elif message.text == "Custom date/time":
        await message.answer(
            "📅 Enter date and time in format DD.MM.YYYY HH:MM (e.g., 31.12.2024 15:30):",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return
    else:
        # Try to parse custom datetime
        try:
            remind_at = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
            if remind_at <= datetime.now():
                await message.answer("❌ Reminder time must be in the future. Try again:")
                return
        except ValueError:
            await message.answer("❌ Invalid format. Use DD.MM.YYYY HH:MM (e.g., 31.12.2024 15:30):")
            return
    
    try:
        data = await state.get_data()
        reminder = add_reminder(
            user_id=message.from_user.id,
            message=data['reminder_message'],
            remind_at=remind_at
        )
        
        time_str = remind_at.strftime("%d.%m.%Y at %H:%M")
        time_diff = remind_at - datetime.now()
        
        if time_diff.days > 0:
            time_until = f"in {time_diff.days} days"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            time_until = f"in {hours} hours"
        else:
            minutes = time_diff.seconds // 60
            time_until = f"in {minutes} minutes"
        
        await message.answer(
            f"✅ Reminder set successfully!\n\n"
            f"⏰ Message: {data['reminder_message']}\n"
            f"📅 Date: {time_str}\n"
            f"⏳ Time until reminder: {time_until}",
            reply_markup=main_menu
        )
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error creating reminder for user {message.from_user.id}: {e}")
        await message.answer("❌ Error creating reminder. Try again.", reply_markup=main_menu)
        await state.clear()

@router.message(Command("reminders"))
async def view_reminders(message: types.Message):
    try:
        reminders = get_active_reminders(message.from_user.id)
        if not reminders:
            await message.answer("⏰ You don't have any active reminders.\nUse /add_reminder to create one!")
            return
        
        text = "⏰ Your active reminders:\n\n"
        for i, reminder in enumerate(reminders, 1):
            # Calculate time until reminder
            now = datetime.datetime.now()
            time_until = reminder.remind_at - now
            
            if time_until.total_seconds() > 0:
                days = time_until.days
                hours, remainder = divmod(time_until.seconds, 3600)
                time_str = f"{days}d {hours}h" if days > 0 else f"{hours}h"  
            else:
                time_str = "Overdue"
            
            text += (
                f"{i}. {reminder.message}\n"
                f"📅 {reminder.remind_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"⏳ {time_str}\n\n"
            )
        
        await message.answer(text)
        
    except Exception as e:
        logging.error(f"Error viewing reminders for user {message.from_user.id}: {e}")
        await message.answer("❌ Error retrieving reminders.")

@router.message(lambda m: m.text == "⏰ Reminders")
async def reminders_menu(message: types.Message):
    try:
        reminders = get_active_reminders(message.from_user.id)
        kb = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Add Reminder")],
                [types.KeyboardButton(text="My Reminders")],
                [types.KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )
        active_count = len([r for r in reminders if r.is_active]) if reminders else 0
        await message.answer(f"⏰ Reminder Management\n📋 Active reminders: {active_count}", reply_markup=kb)
    except Exception as e:
        logging.error(f"Error showing reminders menu for user {message.from_user.id}: {e}")
        await message.answer("❌ Error occurred.", reply_markup=main_menu)

@router.message(lambda m: m.text == "Add Reminder")
async def add_reminder_button(message: types.Message, state: FSMContext):
    await add_reminder_start(message, state)

@router.message(lambda m: m.text == "My Reminders")
async def view_reminders_button(message: types.Message):
    await view_reminders(message)

@router.message(lambda m: m.text == "Back")
async def back_to_main_reminders(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Main Menu:", reply_markup=main_menu) 