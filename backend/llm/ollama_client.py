import aiohttp
import json
import logging
from backend.config.settings import settings

logger = logging.getLogger(__name__)

async def generate_json(prompt: str, model: str, system_prompt: str = "") -> dict:
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.1}
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=120) as response:
                if response.status != 200:
                    return {"error": f"Ollama HTTP {response.status}"}
                
                result = await response.json()
                
                # Extract actual token metrics for DARWIN benchmark
                input_tokens = result.get("prompt_eval_count", 0)
                output_tokens = result.get("eval_count", 0)
                latency = result.get("total_duration", 0) / 1e9 # Convert nanoseconds to seconds
                
                try:
                    parsed_response = json.loads(result["response"])
                    parsed_response["_benchmark"] = {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "latency_seconds": round(latency, 2)
                    }
                    return parsed_response
                except json.JSONDecodeError:
                    return {"error": "Invalid JSON returned from model."}
    except Exception as e:
        return {"error": str(e)}
