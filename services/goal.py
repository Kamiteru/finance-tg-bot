from database.db import SessionLocal
from database.models import Goal, Transaction
from services.crypto import decrypt_value
import datetime
import logging
from sqlalchemy import func

def add_goal(user_id: int, name: str, target_amount: float, deadline=None):
    # Add new financial goal for specific user
    with SessionLocal() as session:
        goal = Goal(
            user_id=user_id,
            name=name, 
            target_amount=target_amount, 
            deadline=deadline
        )
        session.add(goal)
        session.commit()
        logging.info(f"Goal added: user_id={user_id}, name={name}, target_amount={target_amount}, deadline={deadline}")
        return goal

def get_goals(user_id: int):
    # Get all financial goals for specific user
    with SessionLocal() as session:
        return session.query(Goal).filter(Goal.user_id == user_id).all()

def update_goal_progress(user_id: int, goal_id: int, amount: float):
    # Update progress for a specific goal
    with SessionLocal() as session:
        goal = session.query(Goal).filter(
            Goal.id == goal_id,
            Goal.user_id == user_id
        ).first()
        if goal:
            goal.current_amount += amount
            if goal.current_amount >= goal.target_amount:
                goal.achieved = True
            session.commit()
            return goal
        return None

def get_goals_with_progress(user_id: int):
    # Get goals with calculated progress based on income transactions
    with SessionLocal() as session:
        goals = session.query(Goal).filter(Goal.user_id == user_id).all()
        
        # Calculate total income for progress
        income_txs = session.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'income'
        ).all()
        
        total_income = 0
        for tx in income_txs:
            total_income += decrypt_value(tx.amount)
        
        # Update current amounts based on proportional income
        for goal in goals:
            if not goal.achieved:
                # Simple approach: divide total income among active goals
                active_goals = [g for g in goals if not g.achieved]
                if active_goals:
                    goal.current_amount = min(
                        total_income / len(active_goals),
                        goal.target_amount
                    )
                    if goal.current_amount >= goal.target_amount:
                        goal.achieved = True
        
        session.commit()
        return goals

def delete_goal(user_id: int, goal_id: int):
    # Delete a goal for specific user
    with SessionLocal() as session:
        goal = session.query(Goal).filter(
            Goal.id == goal_id,
            Goal.user_id == user_id
        ).first()
        if goal:
            session.delete(goal)
            session.commit()
            return True
        return False 