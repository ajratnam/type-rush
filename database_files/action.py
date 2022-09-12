from sqlalchemy.orm import Session

from utils import get_user


def setup_database(session: Session) -> None:
    """
    It creates the database and tables if they don't exist, and adds a user named 'guest' with no password if it doesn't
    exist

    Args:
      session (Session): The session object that will be used to interact with the database.
    """
    if is_not_sql:
        engine.execute(f'create database if not exists {DATABASE_NAME}')
        engine.execute(f'use {DATABASE_NAME}')

    tables = engine.table_names()

    if 'users' not in tables:
        User.__table__.create(engine)
    if 'scores' not in tables:
        Score.__table__.create(engine)

    user = User(username='guest', password='')

    if not get_user(session, user):
        session.add(user)
        session.commit()


if True:
    from database_files.config import DATABASE_NAME
    from database_files.database import is_not_sql, engine, User, Score
