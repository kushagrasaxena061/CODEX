import json, os, logging
from backend.execution.context import current_session_id

logger = logging.getLogger(__name__)

class TokenTracker:
    def __init__(self, storage_file="darwin_tokens.json"):
        # Save tokens permanently in the root directory
        self.storage_file = os.path.abspath(os.path.join(os.getcwd(), storage_file))
        self.counts = self._load()

    def _load(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save(self):
        try:
            with open(self.storage_file, "w") as f:
                json.dump(self.counts, f)
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")

    # THE FIX: Restore the exact signature the LLM client expects, 
    # pulling the conversation ID from the context safely.
    def add_tokens(self, count: int, conversation_id: int = None):
        if conversation_id is None:
            try:
                conversation_id = current_session_id.get()
            except Exception:
                conversation_id = 0
                
        cid = str(conversation_id)
        if cid not in self.counts:
            self.counts[cid] = 0
        self.counts[cid] += count
        self._save()

    def get_count(self, conversation_id: int) -> int:
        return self.counts.get(str(conversation_id), 0)

token_tracker = TokenTracker()
