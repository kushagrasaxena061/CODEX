from backend.repository.tools import count_tokens

class ContextManager:
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
        self.current_context = ""

    def build_context(self, system_instruction: str, user_request: str, repo_map: str = "") -> str:
        """Safely packs information into the context window without exceeding limits."""
        base_context = f"{system_instruction}\n\nUSER REQUEST:\n{user_request}\n\n"
        base_tokens = count_tokens(base_context)
        
        if repo_map:
            repo_tokens = count_tokens(repo_map)
            # Truncate repo map if it exceeds available token budget
            if base_tokens + repo_tokens > self.max_tokens:
                allowed_chars = (self.max_tokens - base_tokens) * 4  # Approximation
                repo_map = repo_map[:allowed_chars] + "\n...[TRUNCATED FOR LENGTH]"
            
            base_context += f"REPOSITORY MAP:\n{repo_map}\n"
            
        return base_context
