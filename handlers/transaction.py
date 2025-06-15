from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from services.transaction import get_categories, add_transaction, get_last_transactions, get_expense_stats_last_month, add_category
from services.user import get_user_currency, format_amount_with_currency, set_user_currency, SUPPORTED_CURRENCIES
from database.models import Category
from aiogram.filters import Command
from handlers.base import main_menu
from aiogram.types import BufferedInputFile
import logging

router = Router()

class TransactionState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_category = State()
    waiting_for_type = State()

class CategoryState(StatesGroup):
    waiting_for_name = State()
    waiting_for_type = State()

class CurrencyState(StatesGroup):
    waiting_for_currency = State()

@router.message(Command("add_income"))
async def add_income_start(message: types.Message, state: FSMContext):
    await state.set_state(TransactionState.waiting_for_amount)
    await state.update_data(type="income")
    await message.answer("💰 Enter the income amount:")

@router.message(Command("add_expense"))
async def add_expense_start(message: types.Message, state: FSMContext):
    await state.set_state(TransactionState.waiting_for_amount)
    await state.update_data(type="expense")
    await message.answer("💸 Enter the expense amount:")

@router.message(TransactionState.waiting_for_amount, F.text.regexp(r"^\d+(\.\d+)?$"))
async def process_amount(message: types.Message, state: FSMContext):
    amount = float(message.text)
    if amount <= 0:
        await message.answer("❌ Amount must be greater than 0. Try again:")
        return
    if amount > 1000000000:  # 1 billion limit
        await message.answer("❌ Amount is too large. Try again:")
        return
    
    await state.update_data(amount=amount)
    data = await state.get_data()
    transaction_type = data["type"]
    
    # Get categories by type
    categories = get_categories(message.from_user.id, transaction_type)
    if not categories:
        await message.answer(f"❌ No {transaction_type} categories found. Please create one first using /add_category", reply_markup=main_menu)
        await state.clear()
        return
    
    await state.set_state(TransactionState.waiting_for_category)
    category_names = [c.name for c in categories]
    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=name)] for name in category_names] + [[types.KeyboardButton(text="Cancel")]],
        resize_keyboard=True
    )
    emoji = "💰" if transaction_type == "income" else "💸"
    await message.answer(f"{emoji} Choose category:", reply_markup=kb)

@router.message(TransactionState.waiting_for_amount)
async def process_amount_invalid(message: types.Message):
    await message.answer("❌ Enter a valid amount (e.g., 100.50)")

@router.message(TransactionState.waiting_for_category)
async def process_category(message: types.Message, state: FSMContext):
    if message.text == "Cancel":
        await state.clear()
        await message.answer("❌ Transaction cancelled", reply_markup=main_menu)
        return
    
    try:
        data = await state.get_data()
        transaction_type = data["type"]
        categories = get_categories(message.from_user.id, transaction_type)
        category_names = [c.name for c in categories]
        
        if message.text not in category_names:
            await message.answer("Choose a category from the list.")
            return
        category_id = next(c.id for c in categories if c.name == message.text)
        
        add_transaction(
            user_id=message.from_user.id,
            amount=data["amount"], 
            type_=data["type"], 
            category_id=category_id
        )
        transaction_type_text = "income" if data["type"] == "income" else "expense"
        amount_str = format_amount_with_currency(data["amount"], message.from_user.id)
        await message.answer(f"✅ {transaction_type_text.capitalize()} {amount_str} in category '{message.text}' saved!", reply_markup=main_menu)
        await state.clear()
    except Exception as e:
        logging.error(f"Error processing transaction for user {message.from_user.id}: {e}")
        await message.answer("❌ Error saving transaction.", reply_markup=main_menu)
        await state.clear()

@router.message(Command("view_transactions"))
async def view_transactions(message: types.Message):
    try:
        transactions = get_last_transactions(message.from_user.id)
        if not transactions:
            await message.answer("📊 You have no transactions yet.")
            return
        lines = ["📊 Your recent transactions:\n"]
        for t in transactions:
            cat = t.category.name if t.category else "No category"
            emoji = "💰" if t.type == "income" else "💸"
            amount_str = format_amount_with_currency(t.amount, message.from_user.id)
            lines.append(f"{emoji} {t.date.strftime('%d.%m %H:%M')} | {cat} | {amount_str}")
        await message.answer("\n".join(lines))
    except Exception as e:
        logging.error(f"Error viewing transactions for user {message.from_user.id}: {e}")
        await message.answer("❌ Error retrieving transactions.")

@router.message(Command("stats"))
async def stats(message: types.Message):
    try:
        stats_data, buf = get_expense_stats_last_month(message.from_user.id)
        if stats_data is None:
            await message.answer("📊 No expenses in the last month.")
            return
        text = "📊 Monthly expense statistics by category:\n\n"
        total = sum(stats_data.values())
        for cat, amount in stats_data.items():
            percentage = (amount / total) * 100
            amount_str = format_amount_with_currency(amount, message.from_user.id)
            text += f"• {cat}: {amount_str} ({percentage:.1f}%)\n"
        total_str = format_amount_with_currency(total, message.from_user.id)
        text += f"\n💸 Total expenses: {total_str}"
        await message.answer_photo(
            photo=BufferedInputFile(buf.read(), filename="stats.png"), 
            caption=text
        )
    except Exception as e:
        logging.error(f"Error generating stats for user {message.from_user.id}: {e}")
        await message.answer("❌ Error creating statistics.")

@router.message(Command("set_currency"))
async def set_currency_start(message: types.Message, state: FSMContext):
    await state.set_state(CurrencyState.waiting_for_currency)
    
    # Create keyboard with supported currencies
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="USD ($)"), types.KeyboardButton(text="EUR (€)")],
            [types.KeyboardButton(text="RUB (₽)"), types.KeyboardButton(text="GBP (£)")],
            [types.KeyboardButton(text="CNY (¥)"), types.KeyboardButton(text="JPY (¥)")],
            [types.KeyboardButton(text="KZT (₸)"), types.KeyboardButton(text="BYN (Br)")],
            [types.KeyboardButton(text="Cancel")]
        ],
        resize_keyboard=True
    )
    current_currency = get_user_currency(message.from_user.id)
    await message.answer(f"💱 Current currency: {current_currency}\nSelect new preferred currency:", reply_markup=kb)

@router.message(CurrencyState.waiting_for_currency)
async def set_currency_process(message: types.Message, state: FSMContext):
    if message.text == "Cancel":
        await state.clear()
        await message.answer("❌ Currency change cancelled", reply_markup=main_menu)
        return
    
    # Extract currency code from button text
    currency_map = {
        "USD ($)": "USD",
        "EUR (€)": "EUR", 
        "RUB (₽)": "RUB",
        "GBP (£)": "GBP",
        "CNY (¥)": "CNY",
        "JPY (¥)": "JPY",
        "KZT (₸)": "KZT",
        "BYN (Br)": "BYN"
    }
    
    currency = currency_map.get(message.text)
    if not currency:
        await message.answer("❌ Select a currency from the list.")
        return
    
    try:
        success = set_user_currency(message.from_user.id, currency)
        if success:
            await message.answer(f"✅ Currency changed to {currency}!", reply_markup=main_menu)
        else:
            await message.answer("❌ Error changing currency.", reply_markup=main_menu)
        await state.clear()
    except Exception as e:
        logging.error(f"Error setting currency for user {message.from_user.id}: {e}")
        await message.answer("❌ Error changing currency.", reply_markup=main_menu)
        await state.clear()

@router.message(Command("add_category"))
async def add_category_start(message: types.Message, state: FSMContext):
    await state.set_state(CategoryState.waiting_for_type)
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="💰 Income"), types.KeyboardButton(text="💸 Expense")],
            [types.KeyboardButton(text="Cancel")]
        ],
        resize_keyboard=True
    )
    await message.answer("📝 Select category type:", reply_markup=kb)

@router.message(CategoryState.waiting_for_type)
async def add_category_type(message: types.Message, state: FSMContext):
    if message.text == "Cancel":
        await state.clear()
        await message.answer("❌ Category creation cancelled", reply_markup=main_menu)
        return
    
    if message.text == "💰 Income":
        category_type = "income"
    elif message.text == "💸 Expense":
        category_type = "expense"
    else:
        await message.answer("Please select a type from the buttons.")
        return
    
    await state.update_data(type=category_type)
    await state.set_state(CategoryState.waiting_for_name)
    await message.answer("📝 Enter category name:", reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Cancel")]], resize_keyboard=True
    ))

@router.message(CategoryState.waiting_for_name)
async def add_category_name(message: types.Message, state: FSMContext):
    if message.text == "Cancel":
        await state.clear()
        await message.answer("❌ Category creation cancelled", reply_markup=main_menu)
        return
    
    name = message.text.strip()
    if not name:
        await message.answer("Name cannot be empty. Try again:")
        return
    if len(name) > 50:
        await message.answer("Name too long (max 50 characters). Try again:")
        return
    
    try:
        data = await state.get_data()
        add_category(message.from_user.id, name, data["type"])
        type_emoji = "💰" if data["type"] == "income" else "💸"
        await message.answer(f"✅ {type_emoji} Category '{name}' added!", reply_markup=main_menu)
    except ValueError as e:
        if "already exists" in str(e):
            await message.answer("❌ This category already exists.")
        else:
            await message.answer("❌ Error adding category.")
    except Exception as e:
        logging.error(f"Error adding category for user {message.from_user.id}: {e}")
        await message.answer("❌ Error adding category.")
    await state.clear()

@router.message(lambda m: m.text == "➕ Income")
async def income_button(message: types.Message, state: FSMContext):
    await add_income_start(message, state)

@router.message(lambda m: m.text == "➖ Expense")
async def expense_button(message: types.Message, state: FSMContext):
    await add_expense_start(message, state)

@router.message(lambda m: m.text == "📊 Statistics")
async def stats_button(message: types.Message):
    await stats(message)

@router.message(lambda m: m.text == "📝 Categories")
async def categories_menu(message: types.Message):
    try:
        kb = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Add Category")],
                [types.KeyboardButton(text="My Categories")],
                [types.KeyboardButton(text="💱 Change Currency")],
                [types.KeyboardButton(text="Back")]
            ], 
            resize_keyboard=True
        )
        current_currency = get_user_currency(message.from_user.id)
        await message.answer(f"📝 Category Management\n💱 Current currency: {current_currency}", reply_markup=kb)
    except Exception as e:
        logging.error(f"Error showing categories menu for user {message.from_user.id}: {e}")
        await message.answer("❌ Error occurred.", reply_markup=main_menu)

@router.message(lambda m: m.text == "💱 Change Currency")
async def change_currency_button(message: types.Message, state: FSMContext):
    await set_currency_start(message, state)

@router.message(lambda m: m.text == "Add Category")
async def add_category_button(message: types.Message, state: FSMContext):
    await add_category_start(message, state)

@router.message(lambda m: m.text == "My Categories")
async def show_categories(message: types.Message):
    try:
        income_categories = get_categories(message.from_user.id, "income")
        expense_categories = get_categories(message.from_user.id, "expense")
        
        text = "📝 Your categories:\n\n"
        if income_categories:
            text += "💰 Income categories:\n"
            for i, cat in enumerate(income_categories, 1):
                text += f"{i}. {cat.name}\n"
            text += "\n"
        
        if expense_categories:
            text += "💸 Expense categories:\n"
            for i, cat in enumerate(expense_categories, 1):
                text += f"{i}. {cat.name}\n"
        
        if not income_categories and not expense_categories:
            text = "📝 You don't have any categories yet."
        
        await message.answer(text)
    except Exception as e:
        logging.error(f"Error showing categories for user {message.from_user.id}: {e}")
        await message.answer("❌ Error retrieving categories.")

@router.message(lambda m: m.text == "Back")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Main Menu:", reply_markup=main_menu) 