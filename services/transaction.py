from database.db import SessionLocal
from database.models import Transaction, Category
from sqlalchemy.exc import NoResultFound
import pandas as pd
import matplotlib.pyplot as plt
import io
import datetime
from services.crypto import encrypt_value, decrypt_value
from services.user import get_user_currency, format_amount_with_currency, convert_to_user_currency
import logging
from sqlalchemy.orm import joinedload

def copy_default_categories_for_user(user_id: int):
    """Copy system default categories (user_id=0) to new user"""
    with SessionLocal() as session:
        # Get default categories
        default_categories = session.query(Category).filter(Category.user_id == 0).all()
        
        # Check if user already has categories
        user_categories = session.query(Category).filter(Category.user_id == user_id).first()
        if user_categories:
            return  # User already has categories
        
        # Copy default categories to user
        for default_cat in default_categories:
            user_category = Category(
                user_id=user_id,
                name=default_cat.name,
                type=default_cat.type
            )
            session.add(user_category)
        
        session.commit()
        logging.info(f"Copied {len(default_categories)} default categories for user {user_id}")

def get_categories(user_id: int, category_type: str = None):
    """Get all categories from DB for specific user, optionally filtered by type"""
    with SessionLocal() as session:
        # First ensure user has default categories
        copy_default_categories_for_user(user_id)
        
        query = session.query(Category).filter(Category.user_id == user_id)
        if category_type:
            query = query.filter(Category.type == category_type)
        return query.all()

def add_transaction(user_id: int, amount, type_, category_id, description=None):
    """Add new transaction to DB (amount encrypted)"""
    with SessionLocal() as session:
        # Verify category belongs to user and matches transaction type
        category = session.query(Category).filter(
            Category.id == category_id, 
            Category.user_id == user_id,
            Category.type == type_
        ).first()
        if not category:
            raise ValueError("Category not found, doesn't belong to user, or type mismatch")
        
        # Get user's current currency and save transaction in that currency
        user_currency = get_user_currency(user_id)
        
        # Convert amount to user's preferred currency if needed
        if user_currency != 'RUB':  # Assume input is in RUB, convert to user currency
            try:
                amount = convert_to_user_currency(amount, 'RUB', user_id)
            except Exception as e:
                logging.warning(f"Currency conversion failed for user {user_id}: {e}")
        
        enc_amount = encrypt_value(amount)
        transaction = Transaction(
            user_id=user_id,
            amount=enc_amount, 
            type=type_, 
            category_id=category_id,
            description=description,
            currency=user_currency  # Save currency at time of transaction
        )
        session.add(transaction)
        session.commit()
        logging.info(f"Transaction added: user_id={user_id}, type={type_}, amount={amount}, category_id={category_id}")
        return transaction

def get_last_transactions(user_id: int, limit=10):
    # Get last N transactions from DB for specific user (amount decrypted and converted to current currency)
    with SessionLocal() as session:
        txs = (
            session.query(Transaction)
            .options(joinedload(Transaction.category))
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.date.desc())
            .limit(limit)
            .all()
        )
        
        # Get user's current currency for conversion
        current_currency = get_user_currency(user_id)
        
        for t in txs:
            decrypted_amount = decrypt_value(t.amount)
            
            # Convert amount to current user currency if transaction was in different currency
            transaction_currency = getattr(t, 'currency', current_currency)  # Default to current if no currency field
            if transaction_currency != current_currency:
                try:
                    converted_amount = convert_to_user_currency(decrypted_amount, transaction_currency, user_id)
                except Exception as e:
                    logging.warning(f"Currency conversion failed for transaction {t.id}: {e}")
                    converted_amount = decrypted_amount  # Use original amount if conversion fails
            else:
                converted_amount = decrypted_amount
            
            t.amount = converted_amount
        return txs

def get_expense_stats_last_month(user_id: int):
    """Get expense stats by category for the last month for specific user (amount decrypted and converted to current currency)"""
    with SessionLocal() as session:
        month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        q = (
            session.query(Transaction)
            .options(joinedload(Transaction.category))
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == 'expense', 
                Transaction.date >= month_ago
            )
            .all()
        )
        if not q:
            return None, None
        
        # Get user's current currency for conversion
        current_currency = get_user_currency(user_id)
        
        converted_data = []
        for t in q:
            decrypted_amount = decrypt_value(t.amount)
            
            # Convert amount to current user currency if transaction was in different currency
            transaction_currency = getattr(t, 'currency', current_currency)  # Default to current if no currency field
            if transaction_currency != current_currency:
                try:
                    converted_amount = convert_to_user_currency(decrypted_amount, transaction_currency, user_id)
                except Exception as e:
                    logging.warning(f"Currency conversion failed for transaction {t.id}: {e}")
                    converted_amount = decrypted_amount  # Use original amount if conversion fails
            else:
                converted_amount = decrypted_amount
            
            converted_data.append({
                'category': t.category.name if t.category else 'No category',
                'amount': converted_amount
            })
        
        df = pd.DataFrame(converted_data)
        stats_series = df.groupby('category')['amount'].sum()
        
        # Convert pandas Series to regular dict to avoid numpy issues
        stats_dict = stats_series.to_dict()
        
        # Prepare data for matplotlib
        categories = list(stats_dict.keys())
        amounts = list(stats_dict.values())
        
        # Generate pie chart with fixed matplotlib syntax
        fig, ax = plt.subplots(figsize=(10, 8))
        wedges, texts, autotexts = ax.pie(
            amounts, 
            labels=categories, 
            autopct='%1.1f%%', 
            startangle=90
        )
        user_currency_name = get_user_currency(user_id)
        ax.set_title(f'Monthly Expenses by Category ({user_currency_name})', fontsize=14, fontweight='bold')
        
        # Improve text readability
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return stats_dict, buf

def add_category(user_id: int, name: str, category_type: str):
    """Add new category to DB for specific user with type"""
    with SessionLocal() as session:
        # Check if category already exists for this user with same name and type
        existing = session.query(Category).filter(
            Category.user_id == user_id,
            Category.name == name,
            Category.type == category_type
        ).first()
        if existing:
            raise ValueError("Category already exists")
        
        if category_type not in ['income', 'expense']:
            raise ValueError("Category type must be 'income' or 'expense'")
        
        category = Category(user_id=user_id, name=name, type=category_type)
        session.add(category)
        session.commit()
        return category 