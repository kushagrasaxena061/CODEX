import logging
import os
import shutil
import zipfile
import tempfile
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.memory.manager import MemoryManager
from backend.agents.planner import generate_plan
from backend.agents.orchestrator import TaskOrchestrator
from backend.database.models import Conversation, Task
from backend.config.settings import settings

router = APIRouter(prefix="/api", tags=["agent"])
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    prompt: str

@router.post("/workspace/upload")
async def upload_workspace(file: UploadFile = File(...), db: Session = Depends(get_db)):
    workspace = os.path.abspath(settings.WORKSPACE_ROOT)
    
    if os.path.basename(workspace) != "isolated_workspace":
        return {"message": f"CRITICAL ERROR: Workspace is unsafe: {workspace}"}
        
    os.makedirs(workspace, exist_ok=True)
    for item in os.listdir(workspace):
        item_path = os.path.join(workspace, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)
            
    zip_path = os.path.join(tempfile.gettempdir(), "upload_codex.zip")
    with open(zip_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(workspace)
        
    os.remove(zip_path)
    
    # GUARANTEED MEMORY WIPE: Delete all tasks and the main conversation
    db.query(Task).delete()
    db.query(Conversation).delete()
    db.commit()
    
    return {"message": "Isolated Workspace loaded. AI Memory fully reset."}

@router.get("/workspace/download")
async def download_workspace():
    workspace = os.path.abspath(settings.WORKSPACE_ROOT)
    temp_dir = tempfile.gettempdir()
    zip_path = os.path.join(temp_dir, "Export.zip")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(workspace):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, workspace)
                zipf.write(file_path, arcname)
                    
    return FileResponse(path=zip_path, filename="Export.zip", media_type='application/zip')

@router.post("/chat")
async def submit_prompt(req: ChatRequest, db: Session = Depends(get_db)):
    manager = MemoryManager(db)
    conv = db.query(Conversation).first()
    if not conv:
        conv = manager.create_conversation("Isolated Workspace")
        
    recent_tasks = db.query(Task).filter(Task.conversation_id == conv.id).order_by(Task.created_at.asc()).all()[-4:]
    history = "\n".join([f"User: {t.prompt}\nSystem: {t.context_summary}" for t in recent_tasks if t.context_summary])
        
    task = manager.add_task(conv.id, req.prompt)
    try:
        plan = await generate_plan(req.prompt, history)
        orchestrator = TaskOrchestrator(plan, history=history)
        result = await orchestrator.execute()
        
        final_status = "SUCCESS" if result.status == "success" else "FAILED"
        manager.update_task_summary(task.id, final_status, result.message)
            
        return {
            "status": final_status.lower(),
            "prompt": req.prompt,
            "message": result.message,
            "data": result.data if hasattr(result, 'data') else {}
        }
    except Exception as e:
        manager.update_task_summary(task.id, "FAILED", str(e))
        return {"status": "failed", "prompt": req.prompt, "message": str(e)}
