from backend.config.settings import settings, AutonomyLevel

class CommandValidator:
    def __init__(self):
        # Commands that are inherently dangerous and should always be blocked
        self.blocklist = [
            "rm -rf /", "mkfs", "dd ", "wget ", "curl ", 
            "sudo ", "chmod 777", "chown", "history -c"
        ]
        
        # Destructive Git commands requiring strict approval
        self.git_destructive = [
            "git push", "git reset --hard", "git clean", "git rebase"
        ]

    def is_command_allowed(self, command: str) -> tuple[bool, str]:
        """
        Checks if a command is allowed based on the system's autonomy level.
        Returns (is_allowed, reason_if_blocked)
        """
        cmd_lower = command.lower().strip()

        # 1. Absolute blocklist (never allowed)
        for blocked in self.blocklist:
            if blocked in cmd_lower:
                return False, f"Command contains blocked keyword: {blocked}"

        # 2. Autonomy Level Enforcement
        is_destructive_git = any(g in cmd_lower for g in self.git_destructive)
        
        if settings.AUTONOMY_LEVEL == AutonomyLevel.LOW:
            return False, "Low autonomy level requires human approval for all commands."
            
        if settings.AUTONOMY_LEVEL == AutonomyLevel.MEDIUM:
            if is_destructive_git or "rm " in cmd_lower:
                return False, "Medium autonomy blocks destructive commands without explicit approval."

        # HIGH autonomy allows anything not on the absolute blocklist
        return True, ""
