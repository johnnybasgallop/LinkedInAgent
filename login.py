"""
Run this once to log in to LinkedIn and save your session.
After logging in, the session is stored in ./session/ and reused
by the main scraper so you won't need to log in again.
"""

import asyncio
from playwright.async_api import async_playwright

SESSION_DIR = "./session"
LINKEDIN_URL = "https://www.linkedin.com/login"


async def main():
    async with async_playwright() as p:
        print("Opening browser — log in to LinkedIn, then press Enter here to save your session.")

        context = await p.chromium.launch_persistent_context(
            SESSION_DIR,
            headless=False,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )

        page = await context.new_page()
        await page.goto(LINKEDIN_URL)

        # Wait for the user to log in manually
        input("\n  --> Log in to LinkedIn in the browser window, then press Enter here: ")

        # Confirm we're actually logged in by checking for the li_at cookie
        cookies = await context.cookies("https://www.linkedin.com")
        has_li_at = any(c["name"] == "li_at" and c.get("value") for c in cookies)
        if has_li_at:
            print("  Login detected (li_at cookie present). Saving session...")
        else:
            print("  Warning: no li_at cookie found — you may not be logged in.")
            confirm = input("  Save anyway? (y/n): ").strip().lower()
            if confirm != "y":
                print("  Aborted. Re-run this script and complete the login before pressing Enter.")
                await context.close()
                return

        await context.storage_state(path=f"{SESSION_DIR}/state.json")
        print("  Session saved to ./session/state.json")
        print("  You can now run the main scraper.")

        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
