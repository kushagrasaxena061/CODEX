import logging
from collections import defaultdict
from datetime import datetime
from backend.execution.context import current_session_id

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self.logs = defaultdict(list)

    def emit(self, tag: str, message: str, level: str = "INFO"):
        sid = current_session_id.get()
        log_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "tag": tag,
            "message": message,
            "level": level
        }
        self.logs[sid].append(log_entry)
        logger.info(f"[Session {sid}] [{tag}] {message}")

    def get_logs(self, session_id: int):
        return self.logs[session_id]

    def clear(self):
        sid = current_session_id.get()
        self.logs[sid] = []

event_bus = EventBus()
