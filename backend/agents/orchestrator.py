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
        self.max_iterations = max_iterations
        self.state = "PLANNED"

    async def execute(self) -> AgentMessage:
        fm = FileManager(settings.WORKSPACE_ROOT)
        all_logs = []
        all_files = []
        total_input_tokens = 0
        total_output_tokens = 0
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            self.state = "IMPLEMENTING"
            
            for step in self.plan.implementation_steps:
                mentioned_files = self.plan.target_files if self.plan.target_files else ["README.md"]
                files_context = {f: fm.read_file(f) or "(Empty)" for f in mentioned_files}
                        
                code_result = await implement_step(step.instruction, step.agent_role, files_context, settings.WORKSPACE_ROOT, self.history)
                
                if code_result.status == "failed":
                    return code_result
                    
                all_logs.append(f"[{step.agent_role} (Iter {iteration})] {code_result.message}")
                if "terminal_logs" in code_result.data:
                    all_logs.extend(code_result.data["terminal_logs"])
                if "files_changed" in code_result.data:
                    all_files.extend(code_result.data["files_changed"])
                    
            self.state = "VERIFYING"
            passed, reason = await verify_plan(self.plan)
            
            if passed:
                self.state = "SUCCESS"
                all_logs.append(f"[QA VERIFIED] {reason}")
                return AgentMessage(agent_name="orchestrator", status="success", message=f"Verified successfully in {iteration} attempts.", data={"files_changed": list(set(all_files)), "terminal_logs": all_logs})
            else:
                self.state = "DEBUGGING"
                all_logs.append(f"[QA FAILED] {reason}. Triggering self-healing...")
                # Update instruction for next loop
                for step in self.plan.implementation_steps:
                    step.instruction = await generate_fix(reason, step.instruction)
                    
        self.state = "FAILED"
        return AgentMessage(agent_name="orchestrator", status="failed", message="Max retries exceeded during self-healing.", data={"terminal_logs": all_logs})
