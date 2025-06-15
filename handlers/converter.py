from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from services.converter import convert, get_popular_rates
from services.user import get_user_currency, get_user_converter_currencies, set_user_converter_currencies, SUPPORTED_CURRENCIES
from aiogram.filters import Command
from handlers.base import main_menu
import logging

router = Router()

class ConvertState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_base = State()
    waiting_for_target = State()

class CurrencySettingsState(StatesGroup):
    waiting_for_currencies = State()

POPULAR_CURRENCIES = ["USD", "EUR", "GBP", "CNY", "JPY", "KZT", "BYN"]

@router.message(Command("convert"))
async def convert_start(message: types.Message, state: FSMContext):
    await state.set_state(ConvertState.waiting_for_amount)
    await message.answer("💱 Enter amount to convert:")

@router.message(ConvertState.waiting_for_amount, F.text.regexp(r"^\d+(\.\d+)?$"))
async def convert_amount(message: types.Message, state: FSMContext):
    amount = float(message.text)
    if amount <= 0:
        await message.answer("❌ Amount must be greater than 0. Try again:")
        return
    if amount > 1000000000:  # 1 billion limit
        await message.answer("❌ Amount is too large. Try again:")
        return
    
    await state.update_data(amount=amount)
    await state.set_state(ConvertState.waiting_for_base)
    
    # Create keyboard with user's preferred currencies
    user_currency = get_user_currency(message.from_user.id)
    converter_currencies = get_user_converter_currencies(message.from_user.id)
    
    # Add user's main currency if not in converter currencies
    all_currencies = [user_currency] + [c for c in converter_currencies if c != user_currency]
    
    # Create buttons (max 6 currencies per row)
    keyboard = []
    for i in range(0, len(all_currencies), 3):
        row = [types.KeyboardButton(text=curr) for curr in all_currencies[i:i+3]]
        keyboard.append(row)
    
    keyboard.append([types.KeyboardButton(text="Other Currency"), types.KeyboardButton(text="Cancel")])
    
    kb = types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    await message.answer("💰 Select source currency:", reply_markup=kb)

@router.message(ConvertState.waiting_for_amount)
async def convert_amount_invalid(message: types.Message):
    await message.answer("❌ Enter a valid amount (e.g., 100.50)")

@router.message(ConvertState.waiting_for_base)
async def convert_base(message: types.Message, state: FSMContext):
    if message.text == "Cancel":
        await state.clear()
        await message.answer("❌ Conversion cancelled", reply_markup=main_menu)
        return
    
    if message.text == "Other Currency":
        await message.answer("Enter currency code (e.g.: KZT, BYN, CHF):")
        return
    
    base_currency = message.text.upper()
    if len(base_currency) != 3:
        await message.answer("❌ Currency code must be 3 characters (e.g.: USD, EUR)")
        return
    
    await state.update_data(base=base_currency)
    await state.set_state(ConvertState.waiting_for_target)
    
    # Create keyboard with user's preferred currencies (exclude source)
    user_currency = get_user_currency(message.from_user.id)
    converter_currencies = get_user_converter_currencies(message.from_user.id)
    
    all_currencies = [user_currency] + [c for c in converter_currencies if c != user_currency]
    currencies = [c for c in all_currencies if c != base_currency]
    
    # Create buttons
    keyboard = []
    for i in range(0, len(currencies), 3):
        row = [types.KeyboardButton(text=curr) for curr in currencies[i:i+3]]
        keyboard.append(row)
    
    keyboard.append([types.KeyboardButton(text="Other Currency"), types.KeyboardButton(text="Cancel")])
    
    kb = types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    await message.answer("🎯 Select target currency:", reply_markup=kb)

@router.message(ConvertState.waiting_for_target)
async def convert_target(message: types.Message, state: FSMContext):
    if message.text == "Cancel":
        await state.clear()
        await message.answer("❌ Conversion cancelled", reply_markup=main_menu)
        return
    
    if message.text == "Other Currency":
        await message.answer("Enter currency code (e.g.: KZT, BYN, CHF):")
        return
    
    try:
        data = await state.get_data()
        target = message.text.upper()
        
        if len(target) != 3:
            await message.answer("❌ Currency code must be 3 characters (e.g.: USD, EUR)")
            return
        
        if data['base'] == target:
            await message.answer("❌ Source and target currencies cannot be the same")
            return
        
        result = convert(data['amount'], data['base'], target)
        await message.answer(
            f"💱 Conversion result:\n\n"
            f"💰 {data['amount']:,.2f} {data['base']}\n"
            f"🔄\n"
            f"💰 {result:,.2f} {target}",
            reply_markup=main_menu
        )
        await state.clear()
        
    except ValueError as e:
        await message.answer(f"❌ Error: {str(e)}")
        await state.clear()
    except Exception as e:
        logging.error(f"Error in currency conversion: {e}")
        await message.answer("❌ Error converting currencies. Check currency codes.", reply_markup=main_menu)
        await state.clear()

@router.message(lambda m: m.text == "💸 Converter")
async def converter_menu(message: types.Message):
    try:
        # Show popular rates based on user's preferred currency and converter settings
        user_currency = get_user_currency(message.from_user.id)
        converter_currencies = get_user_converter_currencies(message.from_user.id)
        rates_text = await get_popular_rates(user_currency, converter_currencies)
        kb = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="💱 Convert")],
                [types.KeyboardButton(text="⚙️ Currency Settings")],
                [types.KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )
        await message.answer(f"💱 Currency Converter\n\n{rates_text}", reply_markup=kb)
    except Exception as e:
        logging.error(f"Error showing converter menu: {e}")
        await message.answer("💱 Currency Converter", reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="💱 Convert")], [types.KeyboardButton(text="⚙️ Currency Settings")], [types.KeyboardButton(text="Back")]],
            resize_keyboard=True
        ))

@router.message(lambda m: m.text == "💱 Convert")
async def converter_convert_button(message: types.Message, state: FSMContext):
    await convert_start(message, state)

@router.message(lambda m: m.text == "⚙️ Currency Settings")
async def currency_settings_menu(message: types.Message, state: FSMContext):
    """Show currency settings menu"""
    try:
        user_currency = get_user_currency(message.from_user.id)
        converter_currencies = get_user_converter_currencies(message.from_user.id)
        
        text = f"⚙️ Currency Settings\n\n"
        text += f"💰 Your main currency: {user_currency}\n"
        text += f"📊 Converter currencies: {', '.join(converter_currencies)}\n\n"
        text += f"You can customize up to 5 currencies for quick access in converter."
        
        kb = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="✏️ Edit Converter Currencies")],
                [types.KeyboardButton(text="💱 Change Main Currency")],
                [types.KeyboardButton(text="Back")]
            ],
            resize_keyboard=True
        )
        await message.answer(text, reply_markup=kb)
        
    except Exception as e:
        logging.error(f"Error showing currency settings: {e}")
        await message.answer("❌ Error showing settings", reply_markup=main_menu)

@router.message(lambda m: m.text == "✏️ Edit Converter Currencies")
async def edit_converter_currencies(message: types.Message, state: FSMContext):
    """Start editing converter currencies"""
    await state.set_state(CurrencySettingsState.waiting_for_currencies)
    
    current_currencies = get_user_converter_currencies(message.from_user.id)
    
    text = (
        f"✏️ Edit Converter Currencies\n\n"
        f"Current currencies: {', '.join(current_currencies)}\n\n"
        f"Send up to 5 currency codes separated by spaces.\n"
        f"Example: EUR GBP CNY JPY KZT\n\n"
        f"Available currencies: {', '.join(SUPPORTED_CURRENCIES)}"
    )
    
    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Cancel")]],
        resize_keyboard=True
    )
    await message.answer(text, reply_markup=kb)

@router.message(CurrencySettingsState.waiting_for_currencies)
async def process_converter_currencies(message: types.Message, state: FSMContext):
    """Process new converter currencies"""
    if message.text == "Cancel":
        await state.clear()
        await converter_menu(message)
        return
    
    try:
        # Parse currencies from message
        currencies = message.text.upper().split()
        
        if len(currencies) > 5:
            await message.answer("❌ Maximum 5 currencies allowed. Try again:")
            return
        
        if len(currencies) == 0:
            await message.answer("❌ Please enter at least one currency. Try again:")
            return
        
        # Validate currencies
        invalid_currencies = [c for c in currencies if c not in SUPPORTED_CURRENCIES]
        if invalid_currencies:
            await message.answer(f"❌ Invalid currencies: {', '.join(invalid_currencies)}\nTry again:")
            return
        
        # Remove user's main currency if present
        user_currency = get_user_currency(message.from_user.id)
        currencies = [c for c in currencies if c != user_currency]
        
        if not currencies:
            await message.answer("❌ Please enter currencies different from your main currency. Try again:")
            return
        
        # Save currencies
        success = set_user_converter_currencies(message.from_user.id, currencies)
        if success:
            await message.answer(
                f"✅ Converter currencies updated!\n"
                f"New currencies: {', '.join(currencies)}",
                reply_markup=main_menu
            )
        else:
            await message.answer("❌ Error saving currencies", reply_markup=main_menu)
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error processing converter currencies: {e}")
        await message.answer("❌ Error processing currencies", reply_markup=main_menu)
        await state.clear()

@router.message(lambda m: m.text == "💱 Change Main Currency")
async def change_main_currency_redirect(message: types.Message, state: FSMContext):
    """Redirect to main currency change (from transaction handler)"""
    from handlers.transaction import set_currency_start
    await set_currency_start(message, state)

@router.message(lambda m: m.text == "Back")
async def back_to_main_converter(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Main Menu:", reply_markup=main_menu) 