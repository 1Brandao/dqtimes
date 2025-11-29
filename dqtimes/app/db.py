from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    task_id = Column(String, index=True, unique=True)
    status = Column(String, index=True)
    created_at = Column(DateTime)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    payload = Column(JSONB)
    result = Column(JSONB, nullable=True)

Base.metadata.create_all(bind=engine)
