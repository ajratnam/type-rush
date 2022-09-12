from sqlalchemy import Column, Integer, DateTime, CHAR, VARCHAR, ForeignKey, VARBINARY
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from database_files.config import MYSQL_CONNECT_COMMAND, SQLITE3_CONNECT_COMMAND
from utils import try_connect, encrypt_password, make_user_id, set_value

engine = try_connect(MYSQL_CONNECT_COMMAND) or try_connect(SQLITE3_CONNECT_COMMAND)
Session = sessionmaker(bind=engine)
Base = declarative_base()

is_not_sql = engine.url.drivername != 'sqlite'


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True, unique=True)
    username = Column(VARCHAR(20), default=make_user_id, nullable=False, unique=True)
    password = Column(CHAR(40))
    salt = Column(CHAR(32), default=set_value, onupdate=set_value)
    date_created = Column(DateTime(timezone=True), nullable=False, server_default=func.current_timestamp())

    def __repr__(self):
        return f"<User {self.username}, user_id={self.id}>"

    def verify_password(self, password):
        return encrypt_password(password, self.salt)[0] == self.password


class Score(Base):
    __tablename__ = 'scores'
    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True, unique=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    user = relationship(User, backref='scores')
    score = Column(VARBINARY(200), nullable=False)
    date_created = Column(DateTime(timezone=True), nullable=False, server_default=func.current_timestamp())
