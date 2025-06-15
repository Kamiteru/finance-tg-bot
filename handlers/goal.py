from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from handlers.base import main_menu
from services.goal import add_goal, get_goals, update_goal_progress, get_goals_with_progress
from services.user import get_user_currency, format_amount_with_currency
from datetime import datetime, timedelta
import logging

router = Router()

class GoalState(StatesGroup):
    waiting_for_name = State()
    waiting_for_amount = State()
    waiting_for_deadline = State()

@router.message(Command("create_goal"))
async def create_goal_start(message: types.Message, state: FSMContext):
    await state.set_state(GoalState.waiting_for_name)
    await message.answer("🎯 Enter goal name:")

@router.message(GoalState.waiting_for_name)
async def goal_name_handler(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("❌ Name cannot be empty. Try again:")
        return
    if len(name) > 100:
        await message.answer("❌ Name too long (max 100 characters). Try again:")
        return
    
    await state.update_data(name=name)
    await state.set_state(GoalState.waiting_for_amount)
    user_currency = get_user_currency(message.from_user.id)
    await message.answer(f"💰 Enter target amount (in {user_currency}):")

@router.message(GoalState.waiting_for_amount, F.text.regexp(r"^\d+(\.\d+)?$"))
async def goal_amount_handler(message: types.Message, state: FSMContext):
    amount = float(message.text)
    if amount <= 0:
        await message.answer("❌ Amount must be greater than 0. Try again:")
        return
    if amount > 1000000000:  # 1 billion limit
        await message.answer("❌ Amount is too large. Try again:")
        return
    
    await state.update_data(target_amount=amount)
    await state.set_state(GoalState.waiting_for_deadline)
    
    # Create keyboard for deadline options
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="1 month"), types.KeyboardButton(text="3 months")],
            [types.KeyboardButton(text="6 months"), types.KeyboardButton(text="1 year")],
            [types.KeyboardButton(text="Custom date"), types.KeyboardButton(text="No deadline")]
        ],
        resize_keyboard=True
    )
    await message.answer("📅 Select deadline:", reply_markup=kb)

@router.message(GoalState.waiting_for_amount)
async def goal_amount_invalid(message: types.Message):
    await message.answer("❌ Enter a valid amount (e.g., 100.50)")

@router.message(GoalState.waiting_for_deadline)
async def goal_deadline_handler(message: types.Message, state: FSMContext):
    deadline = None
    
    if message.text == "1 month":
        deadline = datetime.now() + timedelta(days=30)
    elif message.text == "3 months":
        deadline = datetime.now() + timedelta(days=90)
    elif message.text == "6 months":
        deadline = datetime.now() + timedelta(days=180)
    elif message.text == "1 year":
        deadline = datetime.now() + timedelta(days=365)
    elif message.text == "No deadline":
        deadline = None
    elif message.text == "Custom date":
        await message.answer(
            "📅 Enter deadline in format DD.MM.YYYY (e.g., 31.12.2024):",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return
    else:
        # Try to parse custom date
        try:
            deadline = datetime.strptime(message.text, "%d.%m.%Y")
            if deadline <= datetime.now():
                await message.answer("❌ Deadline must be in the future. Try again:")
                return
        except ValueError:
            await message.answer("❌ Invalid date format. Use DD.MM.YYYY (e.g., 31.12.2024):")
            return
    
    try:
        data = await state.get_data()
        goal = add_goal(
            user_id=message.from_user.id,
            name=data['name'],
            target_amount=data['target_amount'],
            deadline=deadline
        )
        
        deadline_text = deadline.strftime("%d.%m.%Y") if deadline else "No deadline"
        amount_str = format_amount_with_currency(data['target_amount'], message.from_user.id)
        
        await message.answer(
            f"✅ Goal created successfully!\n\n"
            f"🎯 {data['name']}\n"
            f"💰 Target: {amount_str}\n"
            f"📅 Deadline: {deadline_text}\n"
            f"📊 Progress will be calculated automatically based on your income",
            reply_markup=main_menu
        )
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error creating goal for user {message.from_user.id}: {e}")
        await message.answer("❌ Error creating goal. Try again.", reply_markup=main_menu)
        await state.clear()

@router.message(Command("goals"))
async def view_goals(message: types.Message):
    try:
        goals = get_goals_with_progress(message.from_user.id)
        if not goals:
            await message.answer("🎯 You don't have any goals yet.\nUse /create_goal to create one!")
            return
        
        text = "🎯 Your financial goals:\n\n"
        for i, goal in enumerate(goals, 1):
            progress = (goal.current_amount / goal.target_amount) * 100 if goal.target_amount > 0 else 0
            progress_bar = "█" * int(progress // 10) + "░" * (10 - int(progress // 10))
            
            status = "✅ Achieved" if goal.achieved else "🔄 In progress"
            deadline_text = goal.deadline.strftime("%d.%m.%Y") if goal.deadline else "No deadline"
            
            current_str = format_amount_with_currency(goal.current_amount, message.from_user.id)
            target_str = format_amount_with_currency(goal.target_amount, message.from_user.id)
            
            text += (
                f"{i}. {goal.name}\n"
                f"💰 {current_str} / {target_str}\n"
                f"📊 {progress_bar} {progress:.1f}%\n"
                f"📅 {deadline_text}\n"
                f"📈 {status}\n\n"
            )
        
        await message.answer(text)
        
    except Exception as e:
        logging.error(f"Error viewing goals for user {message.from_user.id}: {e}")
        await message.answer("❌ Error retrieving goals.")

@router.message(lambda m: m.text == "🎯 Goals")
async def goals_menu(message: types.Message):
    try:
        goals = get_goals(message.from_user.id)
        kb = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Create Goal")],
                [types.KeyboardButton(text="My Goals")],
                [types.KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )
        goals_count = len(goals) if goals else 0
        await message.answer(f"🎯 **Goal Management**\n📊 Active goals: {goals_count}", reply_markup=kb)
    except Exception as e:
        logging.error(f"Error showing goals menu for user {message.from_user.id}: {e}")
        await message.answer("❌ Error occurred.", reply_markup=main_menu)

@router.message(lambda m: m.text == "Create Goal")
async def create_goal_button(message: types.Message, state: FSMContext):
    await create_goal_start(message, state)

@router.message(lambda m: m.text == "My Goals")
async def view_goals_button(message: types.Message):
    await view_goals(message)

@router.message(lambda m: m.text == "Back")
async def back_to_main_goals(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Main Menu:", reply_markup=main_menu) 