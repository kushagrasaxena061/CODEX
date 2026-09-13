import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.connection import Base
from backend.memory.manager import MemoryManager
from backend.database.models import Conversation, Task

# Create an in-memory SQLite database specifically for testing
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_memory_manager_flow(db_session):
    manager = MemoryManager(db_session)
    
    # 1. Create a conversation
    conv = manager.create_conversation("UI Updates")
    assert conv.id is not None
    
    # 2. Add first task and mark successful
    task1 = manager.add_task(conv.id, "Make header red")
    manager.update_task_summary(task1.id, "SUCCESS", "Modified Header.jsx background to #FF0000")
    
    # 3. Add second task (PENDING, shouldn't appear in context yet)
    task2 = manager.add_task(conv.id, "Make footer match header")
    
    # 4. Retrieve context
    context = manager.get_context_string(conv.id)
    
    assert "Make header red" in context
    assert "Modified Header.jsx" in context
    assert "Make footer match header" not in context  # Pending tasks have no confirmed result yet
