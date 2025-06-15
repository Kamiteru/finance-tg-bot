from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, LargeBinary
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False, unique=True)
    preferred_currency = Column(String, nullable=False, default='RUB')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    # User settings and preferences

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, nullable=False)
    type = Column(String, nullable=False)  # 'income' or 'expense'
    # Category for transactions

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    amount = Column(LargeBinary, nullable=False)
    type = Column(String, nullable=False)  # income/expense
    category_id = Column(Integer, ForeignKey('categories.id'))
    date = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(String)
    currency = Column(String, nullable=True, default='USD')  # Currency at time of transaction
    # Transaction record (income or expense)
    category = relationship('Category')

class Goal(Base):
    __tablename__ = 'goals'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0)
    deadline = Column(DateTime)
    achieved = Column(Boolean, default=False)
    # Financial goal

class Reminder(Base):
    __tablename__ = 'reminders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    message = Column(String, nullable=False)
    remind_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    # Payment reminder

class UserCurrency(Base):
    __tablename__ = 'user_currencies'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    currency_code = Column(String, nullable=False)
    position = Column(Integer, nullable=False)  # Order position in converter menu
    # User's preferred currencies for converter 