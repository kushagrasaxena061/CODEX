from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database.connection import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), default="New Project")
    created_at = Column(DateTime, default=datetime.utcnow)
    github_repo_url = Column(String(500), nullable=True)
    github_token = Column(String(500), nullable=True)

    tasks = relationship("Task", back_populates="conversation", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    prompt = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING")
    context_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="tasks")
