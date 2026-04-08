from playwright.async_api import async_playwright, Browser, BrowserContext
from config import SESSION_STATE, USER_AGENT


async def create_context() -> tuple:
    """
    Launch a headless Chromium browser and return (playwright, browser, context)
    loaded with the saved LinkedIn session.
    """
    if not SESSION_STATE.exists():
        raise FileNotFoundError(
            f"No session found at {SESSION_STATE} — run login.py first."
        )

    playwright = await async_playwright().start()
    browser: Browser = await playwright.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"],
    )
    context: BrowserContext = await browser.new_context(
        storage_state=str(SESSION_STATE),
        user_agent=USER_AGENT,
    )
    return playwright, browser, context


async def teardown(playwright, browser) -> None:
    await browser.close()
    await playwright.stop()
