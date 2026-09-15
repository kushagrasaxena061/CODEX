import logging
from backend.agents.planner import AdvancedExecutionPlan
from backend.agents.base import AgentMessage
from backend.agents.code import implement_step
from backend.agents.verifier import verify_plan
from backend.agents.debug import generate_fix
from backend.repository.file_manager import FileManager
from backend.events.bus import event_bus
from backend.execution.cancel_manager import cancel_manager
from backend.execution.context import current_session_id

logger = logging.getLogger(__name__)

class TaskOrchestrator:
    def __init__(self, plan: AdvancedExecutionPlan, workspace_root: str, session_id: int, history: str = "", max_iterations: int = 8):
        self.plan = plan
        self.workspace_root = workspace_root
        self.session_id = session_id
        self.history = history
        self.max_iterations = max_iterations

    async def execute(self) -> AgentMessage:
        # ABSOLUTE ISOLATION: Forcing the memory tracker to lock onto this specific session ID
        current_session_id.set(self.session_id)
        
        if self.plan.feature_already_exists:
            return AgentMessage(agent_name="orchestrator", status="duplicate", message=f"Functionality already exists: {self.plan.duplication_reason}")

        fm = FileManager(self.workspace_root)
        iteration = 0
        
        while iteration < self.max_iterations:
            current_session_id.set(self.session_id) # Aggressive re-assertion loop
            cancel_manager.check()
            iteration += 1
            
            for step in self.plan.implementation_steps:
                current_session_id.set(self.session_id)
                cancel_manager.check()
                files_context = {f: fm.read_file(f) or "(Empty)" for f in self.plan.target_files} if self.plan.target_files else {}
                await implement_step(step.instruction, step.agent_role, files_context, self.workspace_root, self.history)
                
            current_session_id.set(self.session_id)
            cancel_manager.check()
            passed, reason = await verify_plan(self.plan, workspace_root=self.workspace_root)
            
            if passed:
                return AgentMessage(agent_name="orchestrator", status="success", message="All tests passed. Ready for approval.")
            else:
                event_bus.emit("QA_VERIFIER", f"Refining (Attempt {iteration}/{self.max_iterations}): {reason}", level="WARN")
                for step in self.plan.implementation_steps:
                    current_session_id.set(self.session_id)
                    cancel_manager.check()
                    step.instruction = await generate_fix(reason, step.instruction)
                    
        return AgentMessage(agent_name="orchestrator", status="failed", message="Max retries reached without passing all edge cases.")
