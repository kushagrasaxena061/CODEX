from sqlalchemy.orm import Session
from backend.database.models import Conversation, Task

class MemoryManager:
    def __init__(self, db_session: Session):
        self.db = db_session

    def create_conversation(self, title: str = "New Conversation") -> Conversation:
        """Initializes a new persistent conversation thread."""
        conv = Conversation(title=title)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def add_task(self, conversation_id: int, prompt: str) -> Task:
        """Records a new user prompt into the conversation."""
        task = Task(conversation_id=conversation_id, prompt=prompt)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update_task_summary(self, task_id: int, status: str, summary: str):
        """Updates the task with the final outcome to be used as future memory."""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = status
            task.context_summary = summary
            self.db.commit()

    def get_context_string(self, conversation_id: int) -> str:
        """
        Retrieves past tasks and formats them into a compact string for LLM context.
        Rule: This informs the LLM of *past intent*, but repository inspection
        must still be used to verify the *current truth*.
        """
        tasks = self.db.query(Task).filter(
            Task.conversation_id == conversation_id,
            Task.status == "SUCCESS"
        ).order_by(Task.created_at).all()
        
        if not tasks:
            return ""
            
        context = "PREVIOUS TASK HISTORY:\n"
        for t in tasks:
            if t.context_summary:
                context += f"- Prompt: '{t.prompt}' -> Result: {t.context_summary}\n"
        return context
