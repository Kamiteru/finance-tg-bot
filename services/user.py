from database.db import SessionLocal
from database.models import User, UserCurrency
from services.converter import convert
import logging

SUPPORTED_CURRENCIES = ['RUB', 'USD', 'EUR', 'GBP', 'CNY', 'JPY', 'KZT', 'BYN']
DEFAULT_CONVERTER_CURRENCIES = ['USD', 'EUR', 'GBP', 'CNY', 'JPY']

def get_or_create_user(telegram_id: int) -> User:
    """Get existing user or create new one with default settings"""
    with SessionLocal() as session:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id, preferred_currency='USD')  # Default to USD
            session.add(user)
            session.commit()
            session.refresh(user)  # Refresh to get the committed state
            logging.info(f"Created new user: telegram_id={telegram_id}")
        # Return the user object within the session context
        return user

def create_or_get_user(telegram_id: int) -> dict:
    """Create or get user and return user data as dict to avoid session issues"""
    with SessionLocal() as session:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id, preferred_currency='USD')  # Default to USD
            session.add(user)
            session.commit()
            session.refresh(user)
            logging.info(f"Created new user: telegram_id={telegram_id}")
        
        # Return user data as dict to avoid DetachedInstanceError
        return {
            'id': user.id,
            'telegram_id': user.telegram_id,
            'preferred_currency': user.preferred_currency,
            'created_at': user.created_at
        }

def get_user_currency(user_id: int) -> str:
    """Get user's preferred currency"""
    with SessionLocal() as session:
        user = session.query(User).filter(User.telegram_id == user_id).first()
        if user:
            return user.preferred_currency
        return 'USD'  # Default currency

def set_user_currency(telegram_id: int, currency: str) -> bool:
    """Set user's preferred currency"""
    if currency.upper() not in SUPPORTED_CURRENCIES:
        return False
    
    with SessionLocal() as session:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id, preferred_currency=currency.upper())
            session.add(user)
        else:
            user.preferred_currency = currency.upper()
        session.commit()
        logging.info(f"Set currency {currency} for user {telegram_id}")
        return True

def convert_to_user_currency(amount: float, from_currency: str, telegram_id: int) -> float:
    """Convert amount to user's preferred currency"""
    user_currency = get_user_currency(telegram_id)
    if from_currency == user_currency:
        return amount
    try:
        return convert(amount, from_currency, user_currency)
    except Exception as e:
        logging.error(f"Currency conversion error: {e}")
        return amount  # Return original amount if conversion fails

def format_amount_with_currency(amount: float, telegram_id: int) -> str:
    """Format amount with user's preferred currency symbol"""
    currency = get_user_currency(telegram_id)
    currency_symbols = {
        'RUB': '₽',
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'CNY': '¥',
        'JPY': '¥',
        'KZT': '₸',
        'BYN': 'Br'
    }
    symbol = currency_symbols.get(currency, currency)
    return f"{amount:,.2f} {symbol}"

def get_user_converter_currencies(telegram_id: int) -> list:
    """Get user's preferred currencies for converter"""
    with SessionLocal() as session:
        currencies = (session.query(UserCurrency)
                     .filter(UserCurrency.user_id == telegram_id)
                     .order_by(UserCurrency.position)
                     .all())
        
        if not currencies:
            # Create default currencies for new user
            create_default_converter_currencies(telegram_id)
            # Get default currencies
            user_currency = get_user_currency(telegram_id)
            default_currencies = [c for c in DEFAULT_CONVERTER_CURRENCIES if c != user_currency]
            return default_currencies[:5]  # Return first 5
        
        return [c.currency_code for c in currencies]

def create_default_converter_currencies(telegram_id: int):
    """Create default converter currencies for user"""
    with SessionLocal() as session:
        user_currency = get_user_currency(telegram_id)
        # Use default currencies except user's main currency
        default_currencies = [c for c in DEFAULT_CONVERTER_CURRENCIES if c != user_currency]
        
        for i, currency in enumerate(default_currencies[:5]):  # Max 5 currencies
            user_curr = UserCurrency(
                user_id=telegram_id,
                currency_code=currency,
                position=i
            )
            session.add(user_curr)
        session.commit()
        logging.info(f"Created default converter currencies for user {telegram_id}")

def set_user_converter_currencies(telegram_id: int, currencies: list) -> bool:
    """Set user's preferred currencies for converter"""
    if len(currencies) > 5:
        return False
    
    # Validate all currencies
    for currency in currencies:
        if currency.upper() not in SUPPORTED_CURRENCIES:
            return False
    
    with SessionLocal() as session:
        # Remove existing currencies
        session.query(UserCurrency).filter(UserCurrency.user_id == telegram_id).delete()
        
        # Add new currencies
        for i, currency in enumerate(currencies):
            user_curr = UserCurrency(
                user_id=telegram_id,
                currency_code=currency.upper(),
                position=i
            )
            session.add(user_curr)
        
        session.commit()
        logging.info(f"Set converter currencies for user {telegram_id}: {currencies}")
        return True 