from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database.connection import Base

def utc_now():
    return datetime.now(timezone.utc)

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime, default=utc_now)
    
    tasks = relationship("Task", back_populates="conversation", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    prompt = Column(Text, nullable=False)
    status = Column(String, default="PENDING")
    
    context_summary = Column(Text, default="")
    created_at = Column(DateTime, default=utc_now)
    
    conversation = relationship("Conversation", back_populates="tasks")
