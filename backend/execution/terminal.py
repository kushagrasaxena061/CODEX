import asyncio
import logging

logger = logging.getLogger(__name__)

class Terminal:
    def __init__(self, cwd: str):
        self.cwd = cwd

    async def run(self, command: str, timeout: int = 15) -> dict:
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.cwd
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "exit_code": proc.returncode,
                "stdout": stdout.decode().strip(),
                "stderr": stderr.decode().strip()
            }
        except asyncio.TimeoutError:
            return {"exit_code": -1, "stdout": "", "stderr": "Command timed out."}
        except Exception as e:
            return {"exit_code": -1, "stdout": "", "stderr": str(e)}
