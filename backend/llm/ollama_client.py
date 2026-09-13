import httpx
import logging
import json
from typing import Dict, Any
from backend.config.settings import settings

logger = logging.getLogger(__name__)

async def check_ollama_health() -> str:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            resp.raise_for_status()
            return "online"
    except Exception:
        return "offline"

async def generate_json(prompt: str, model: str, system: str = "") -> Dict[str, Any]:
    """Robust Ollama client with timeout, JSON enforcement, and error handling."""
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "format": "json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            response_text = data.get("response", "{}")
            
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                logger.error(f"Ollama returned malformed JSON: {response_text}")
                return {"error": "Malformed JSON", "raw": response_text}
                
    except httpx.ConnectError:
        return {"error": "Connection failed. Is Ollama running on port 11434?"}
    except httpx.TimeoutException:
        return {"error": "Ollama request timed out."}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"error": f"Model '{model}' not found. You must pull it."}
        return {"error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        return {"error": str(e)}
