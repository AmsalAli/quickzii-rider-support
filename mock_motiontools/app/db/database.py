'''SQLAlchemy engine, session factory, and Base declaration.

SQLite for prototype simplicity; the schema and code are portable to
PostgreSQL by changing DATABASE_URL alone (no ORM changes needed).
'''
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={'check_same_thread': False},  # required for SQLite + FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    '''FastAPI dependency: yields a session, guarantees close.'''
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
