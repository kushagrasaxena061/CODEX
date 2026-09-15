import os
import base64
import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

async def test_frontend(file_path: str) -> dict:
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # THE FIX: Try/Finally block guarantees the browser process is killed in RAM
            # even if the webpage causes a critical timeout or Python crash.
            try:
                page = await browser.new_page()
                console_errors = []
                page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
                page.on("pageerror", lambda exc: console_errors.append(str(exc)))
                
                await page.goto(f"file://{file_path}", timeout=15000)
                await page.wait_for_load_state("networkidle", timeout=15000)
                
                content = await page.content()
                title = await page.title()
                
                screenshot_bytes = await page.screenshot(type="jpeg", quality=60)
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                
                return {
                    "success": True, 
                    "title": title, 
                    "errors": console_errors, 
                    "dom_snippet": content[:400],
                    "screenshot": screenshot_b64
                }
            finally:
                await browser.close()
    except Exception as e:
        return {"success": False, "error": str(e)}
