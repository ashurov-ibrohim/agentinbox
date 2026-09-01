from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import create_engine
from config import settings

# Render Postgres connection string ba'zan eski "postgres://" prefiksi bilan
# beriladi, lekin SQLAlchemy 2.0 + psycopg2 "postgresql://" ni talab qiladi.
_db_url = settings.DATABASE_URL
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(_db_url)

SessionLocal = sessionmaker(bind=engine, autoflush=True)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()