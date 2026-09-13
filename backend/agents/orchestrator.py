import logging
from backend.prompts.schemas import ExecutionPlan
from backend.agents.base import AgentMessage
from backend.agents.code import implement_step
from backend.agents.verifier import verify_plan
from backend.agents.debug import generate_fix
from backend.config.settings import settings
from backend.repository.file_manager import FileManager

logger = logging.getLogger(__name__)

class TaskOrchestrator:
    def __init__(self, plan: ExecutionPlan, history: str = "", max_iterations: int = 3):
        self.plan = plan
        self.history = history
        self.state = "PLANNED"
        self.iterations = 0
        self.max_iterations = max_iterations
        self.current_instruction = self.plan.goal

    async def execute(self) -> AgentMessage:
        fm = FileManager(settings.WORKSPACE_ROOT)
        
        while self.iterations < self.max_iterations:
            self.iterations += 1
            self.state = "IMPLEMENTING"
            mentioned_files = self.plan.target_files if self.plan.target_files else ["README.md"]
                
            files_context = {}
            for f in mentioned_files:
                content = fm.read_file(f)
                files_context[f] = content if content else "(File does not exist yet.)"
                    
            code_result = await implement_step(self.current_instruction, files_context, settings.WORKSPACE_ROOT, self.history)
            
            if code_result.status == "failed":
                return code_result
                
            self.state = "VERIFYING"
            passed, reason = await verify_plan(self.plan)
            
            if passed:
                self.state = "SUCCESS"
                return AgentMessage(agent_name="orchestrator", status="success", message=f"Success: {reason}", data=code_result.data)
            else:
                self.state = "DEBUGGING"
                self.current_instruction = await generate_fix(reason, self.current_instruction)
                
        self.state = "FAILED"
        return AgentMessage(agent_name="orchestrator", status="failed", message=f"Max retries exceeded.")
