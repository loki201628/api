
from pymongo import MongoClient
from contextlib import contextmanager
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Index
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# MongoDB Connection
MONGO_URI = "mongodb://localhost:27017"
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["contact_management_lokesh"]
contacts_collection = mongo_db["contacts"]

# SQLite Connection using SQLAlchemy
SQLITE_DB_URL = "sqlite:///sqlite_contacts.db"
engine = create_engine(SQLITE_DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define tables using SQLAlchemy ORM
class ActivityLogTable(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False)
    activity_type = Column(String(50), nullable=False)
    description = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


class ContactRelationshipTable(Base):
    __tablename__ = "contact_relationships"
    id = Column(Integer, primary_key=True, index=True)
    owner_email = Column(String(255), nullable=False)
    linked_user_id = Column(String(50), nullable=False)
    relationship_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_owner_email", "owner_email"),)


# Context manager for SQLite sessions
@contextmanager
def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# Initialize SQLite tables if they don't exist
Base.metadata.create_all(bind=engine)
