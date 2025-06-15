from database.models import Base, Reminder
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime

def test_add_and_get_reminder():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    r = Reminder(message="Test", remind_at=datetime.datetime.now())
    session.add(r)
    session.commit()
    rem = session.query(Reminder).first()
    assert rem.message == "Test"
    assert rem.is_active 