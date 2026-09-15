import aiohttp
import json
import re
import logging
from backend.execution.token_tracker import token_tracker

logger = logging.getLogger(__name__)

def extract_json_from_text(text: str) -> dict:
    if not text or not text.strip():
        return {"error": "Empty response from LLM"}

    # 1. Strip <think>...</think> reasoning blocks from Qwen
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

    # 2. Try direct JSON load
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 3. Strip Markdown code fences
    fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except Exception:
            pass

    # 4. Extract outermost JSON object { ... }
    first_brace = cleaned.find('{')
    last_brace = cleaned.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = cleaned[first_brace:last_brace + 1]
        try:
            return json.loads(candidate)
        except Exception:
            # Handle trailing commas or minor syntax irregularities
            candidate_fixed = re.sub(r',\s*([\}\]])', r'\1', candidate)
            try:
                return json.loads(candidate_fixed)
            except Exception:
                pass

    logger.error(f"Failed to extract JSON from raw response: {text[:200]}...")
    return {"error": "Could not parse valid JSON from model output."}

async def generate_json(prompt: str, model: str, system_prompt: str = "", max_tokens: int = 1500, timeout_sec: int = 180, images: list = None) -> dict:
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "format": "json",
        "options": {"num_predict": max_tokens}
    }
    
    if images:
        payload["images"] = images
        
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=timeout_sec) as response:
                if response.status != 200:
                    return {"error": f"Ollama HTTP {response.status}"}
                
                data = await response.json()
                
                p_tokens = data.get("prompt_eval_count", 0)
                c_tokens = data.get("eval_count", 0)
                token_tracker.add_tokens(p_tokens + c_tokens)
                
                raw_response = data.get("response", "")
                parsed = extract_json_from_text(raw_response)
                return parsed
    except Exception as e:
        logger.error(f"Ollama connection error: {e}")
        return {"error": str(e)}
