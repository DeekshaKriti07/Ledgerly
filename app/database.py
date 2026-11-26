from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
DB_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'data' / 'ledgerly.db'}")
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
engine = create_engine(DB_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

def init_db():
    from app import models
    Base.metadata.create_all(bind=engine)
