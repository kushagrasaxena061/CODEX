import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.memory.manager import MemoryManager
from backend.agents.planner import generate_plan
from backend.agents.orchestrator import TaskOrchestrator
from backend.database.models import Conversation, Task
from backend.git.manager import GitManager

router = APIRouter(prefix="/api", tags=["agent"])
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    prompt: str

@router.post("/chat")
async def submit_prompt(req: ChatRequest, db: Session = Depends(get_db)):
    manager = MemoryManager(db)
    git = GitManager()
    
    conv = db.query(Conversation).first()
    if not conv:
        conv = manager.create_conversation("Main Workspace")
        
    # Extract Conversation History for Memory (Phase 14)
    recent_tasks = db.query(Task).filter(Task.conversation_id == conv.id).order_by(Task.created_at.asc()).all()[-4:]
    history = "\n".join([f"User: {t.prompt}\nSystem: {t.context_summary}" for t in recent_tasks if t.context_summary])
        
    task = manager.add_task(conv.id, req.prompt)
    
    try:
        plan = await generate_plan(req.prompt, history)
        orchestrator = TaskOrchestrator(plan, history=history, max_iterations=2)
        result = await orchestrator.execute()
        
        final_status = "SUCCESS" if result.status == "success" else "FAILED"
        manager.update_task_summary(task.id, final_status, result.message)
        
        # Git Commit (Phase 20)
        if final_status == "SUCCESS":
            git.commit(f"Codex AI: {req.prompt[:50]}")
            
        return {
            "status": final_status.lower(),
            "prompt": req.prompt,
            "message": result.message,
            "data": result.data if hasattr(result, 'data') else {}
        }
    except Exception as e:
        manager.update_task_summary(task.id, "FAILED", str(e))
        return {"status": "failed", "prompt": req.prompt, "message": str(e)}
