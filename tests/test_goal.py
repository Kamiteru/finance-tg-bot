from database.models import Base, Goal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime

def test_add_and_get_goal():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    g = Goal(name="TestGoal", target_amount=1000, deadline=datetime.datetime.now())
    session.add(g)
    session.commit()
    goal = session.query(Goal).first()
    assert goal.name == "TestGoal"
    assert goal.target_amount == 1000 