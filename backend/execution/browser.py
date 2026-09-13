import asyncio
import logging
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)

class BrowserAgent:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()
        # Ensure a screenshots directory exists
        self.screenshot_dir = self.workspace_root / ".codex_screenshots"
        self.screenshot_dir.mkdir(exist_ok=True)

    async def verify_page(self, url: str, expected_text: str = None, screenshot_name: str = None) -> dict:
        """
        Navigates to a local URL, verifies DOM content, and optionally takes a screenshot.
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Navigate with a strict timeout so the agent doesn't hang
                await page.goto(url, timeout=10000)
                
                # Wait for network idle to ensure frameworks like React have rendered
                await page.wait_for_load_state("networkidle", timeout=5000)

                html_content = await page.content()
                text_found = False
                
                if expected_text:
                    # Simple text verification in the rendered DOM
                    text_found = expected_text.lower() in html_content.lower()

                screenshot_path = None
                if screenshot_name:
                    path = self.screenshot_dir / f"{screenshot_name}.png"
                    await page.screenshot(path=str(path))
                    screenshot_path = str(path)

                await browser.close()

                return {
                    "status": "success",
                    "url": url,
                    "text_found": text_found if expected_text else None,
                    "screenshot_path": screenshot_path,
                    "error": None
                }
        except PlaywrightTimeout:
            return {"status": "failed", "error": f"Timeout connecting to {url}. Is the server running?"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
