import logging
from duckduckgo_search import DDGS
from backend.events.bus import event_bus

logger = logging.getLogger(__name__)

def search_web(query: str) -> str:
    event_bus.emit("RESEARCHER", f"Browsing the live web for: {query}")
    try:
        results = list(DDGS().text(query, max_results=3))
        if not results:
            return "No results found."
        context = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        event_bus.emit("RESEARCHER", "Live web knowledge retrieved successfully.", level="SUCCESS")
        return context
    except Exception as e:
        event_bus.emit("RESEARCHER", f"Web search unavailable: {e}", level="WARN")
        return ""
