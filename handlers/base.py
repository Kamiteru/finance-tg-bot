from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from services.user import create_or_get_user
import logging

router = Router()

# Main menu keyboard with English labels
main_menu = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="➕ Income"), types.KeyboardButton(text="➖ Expense")],
        [types.KeyboardButton(text="📊 Statistics"), types.KeyboardButton(text="📝 Categories")],
        [types.KeyboardButton(text="🎯 Goals"), types.KeyboardButton(text="⏰ Reminders")],
        [types.KeyboardButton(text="💸 Converter"), types.KeyboardButton(text="📋 Reports")]
    ],
    resize_keyboard=True
)

@router.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    """Handle /start command"""
    await state.clear()
    try:
        user_data = create_or_get_user(message.from_user.id)
        user_name = message.from_user.first_name or "User"
        await message.answer(
            f"👋 Welcome to Financial Bot, {user_name}!\n\n"
            f"💰 Track your income and expenses\n"
            f"📊 View statistics and analytics\n"
            f"🎯 Set and track financial goals\n"
            f"⏰ Set reminders for payments\n"
            f"💸 Convert currencies\n"
            f"📋 Generate reports\n\n"
            f"🔒 All data is encrypted and stored securely!\n\n"
            f"Choose an option from the menu below:",
            reply_markup=main_menu
        )
    except Exception as e:
        logging.error(f"Error in start handler for user {message.from_user.id}: {e}")
        await message.answer("❌ An error occurred. Please try again.", reply_markup=main_menu)

@router.message(Command("help"))
async def help_handler(message: types.Message):
    """Handle /help command"""
    help_text = """
🤖 Financial Bot Help

Commands:
• /start - Start the bot and show main menu
• /help - Show this help message
• /add_income - Add income transaction
• /add_expense - Add expense transaction
• /view_transactions - View recent transactions
• /stats - Show expense statistics
• /set_currency - Change preferred currency
• /add_category - Add new category
• /convert - Currency converter

Features:
💰 Transactions - Track income and expenses with categories
📊 Statistics - View charts and analytics of your spending
🎯 Goals - Set and track financial goals
⏰ Reminders - Set payment reminders
💸 Converter - Convert between currencies
📋 Reports - Generate PDF/Excel reports

Currency Support:
The bot supports multiple currencies: USD, EUR, RUB, GBP, CNY, JPY, KZT, BYN
You can set your preferred currency and all amounts will be displayed in it.

Use the menu buttons below to navigate! 👇
    """
    await message.answer(help_text, reply_markup=main_menu)

@router.message(Command("menu"))
async def menu_handler(message: types.Message, state: FSMContext):
    """Handle /menu command"""
    await state.clear()
    await message.answer("🏠 Main Menu:", reply_markup=main_menu)

 