import asyncio
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ProcessManager:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()
        self.running_processes = {} # Tracks processes by custom names

    async def start_background_process(self, name: str, command: str) -> int:
        """Starts a long-running process (e.g., a web server) without waiting for it to finish."""
        if name in self.running_processes:
            self.stop_process(name) # Ensure no duplicate servers

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.workspace_root)
        )
        self.running_processes[name] = process
        logger.info(f"Started background process '{name}' (PID: {process.pid})")
        return process.pid

    def stop_process(self, name: str) -> bool:
        """Safely terminates a background process."""
        process = self.running_processes.get(name)
        if process and process.returncode is None:
            try:
                process.terminate()
                logger.info(f"Terminated process '{name}'")
                return True
            except ProcessLookupError:
                pass
        return False
        
    def stop_all(self):
        """Cleanup function to stop all orphaned processes (used during Task Cancellation or App Shutdown)."""
        for name in list(self.running_processes.keys()):
            self.stop_process(name)
        self.running_processes.clear()
