from database.models import Base, Transaction, Category
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime

def test_add_and_get_transaction():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    cat = Category(name="TestCat")
    session.add(cat)
    session.commit()
    t = Transaction(amount=b"123", type="income", category_id=cat.id, date=datetime.datetime.now())
    session.add(t)
    session.commit()
    tx = session.query(Transaction).first()
    assert tx.type == "income"
    assert tx.category_id == cat.id 