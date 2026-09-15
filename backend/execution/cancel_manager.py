from backend.execution.context import current_session_id

class CancelManager:
    def __init__(self):
        self.flags = set()

    def request_cancel(self, session_id: int):
        self.flags.add(session_id)

    def check(self):
        sid = current_session_id.get()
        if sid in self.flags:
            raise InterruptedError("Task cancelled by user.")

    def reset(self):
        sid = current_session_id.get()
        self.flags.discard(sid)

cancel_manager = CancelManager()
