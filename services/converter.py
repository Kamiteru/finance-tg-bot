import requests
import asyncio
import logging

API_URL = 'https://api.exchangerate-api.com/v4/latest/'

# Get exchange rate from API

def get_rate(base: str, target: str) -> float:
    try:
        resp = requests.get(f'{API_URL}{base}', timeout=10)
        resp.raise_for_status()
        data = resp.json()
        rate = data['rates'].get(target)
        if rate is None:
            raise ValueError(f'Currency {target} not found')
        return rate
    except requests.exceptions.RequestException:
        raise ValueError('Failed to get exchange rates. Check your internet connection.')
    except KeyError:
        raise ValueError('Error getting exchange rates')
    except Exception as e:
        logging.error(f"Error getting exchange rate: {e}")
        raise ValueError('Ошибка при получении курса валют')

def convert(amount: float, base: str, target: str) -> float:
    # Convert amount from base currency to target currency
    if base == target:
        return amount
    
    rate = get_rate(base, target)
    return amount * rate

async def get_popular_rates(user_currency: str = 'USD', converter_currencies: list = None) -> str:
    # Get popular exchange rates for display based on user's preferred currency and converter settings
    try:
        # Use asyncio to make requests non-blocking
        loop = asyncio.get_event_loop()
        
        # Get rates for user's preferred currency
        response = await loop.run_in_executor(
            None, 
            lambda: requests.get(f'{API_URL}{user_currency}', timeout=10)
        )
        data = response.json()
        
        # Currency symbols mapping
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
        
        base_symbol = currency_symbols.get(user_currency, user_currency)
        
        rates_text = f"📈 Current Rates (1 {user_currency}):\n\n"
        
        # Use user's converter currencies or default major currencies
        display_currencies = converter_currencies if converter_currencies else ['USD', 'EUR', 'RUB', 'GBP', 'CNY', 'JPY']
        
        for currency in display_currencies:
            if currency != user_currency and currency in data['rates']:
                rate = data['rates'][currency]
                symbol = currency_symbols.get(currency, currency)
                rates_text += f"💱 1 {base_symbol} = {rate:.2f} {symbol}\n"
        
        return rates_text
        
    except Exception as e:
        logging.error(f"Error getting popular rates: {e}")
        return "📈 Exchange rates temporarily unavailable" 