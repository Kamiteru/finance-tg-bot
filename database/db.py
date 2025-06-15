from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

DATABASE_URL = 'sqlite:///finance.db'

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    # Create all tables
    Base.metadata.create_all(bind=engine) 