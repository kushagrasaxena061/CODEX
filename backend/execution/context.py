from contextvars import ContextVar

# This ensures that even if 10 chats run at the same time,
# Python tracks their variables in isolated memory threads.
current_session_id = ContextVar("current_session_id", default=0)
