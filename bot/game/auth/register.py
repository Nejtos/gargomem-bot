import random
import asyncio
from bot.core.driver import MyDriver
from bot.game.auth.settings import settings


async def register():
    page = await MyDriver().get_driver()
    try:
        register_btn = await page.query_selector(".c-btn.button-register.mt-3")
        if register_btn:
            await page.locator('[id="popup-create-account-login"]').fill(
                "example-login"
            )
            await asyncio.sleep(random.uniform(2, 3))
            await page.click(".cc-btn.cc-allow")
            await asyncio.sleep(random.uniform(0.4, 0.7))
            await page.locator('[id="popup-create-account-password"]').fill(
                "example-pass"
            )
            await asyncio.sleep(random.uniform(2, 3))
            await page.locator('[id="popup-create-account-password2"]').fill(
                "example-pass"
            )
            await asyncio.sleep(random.uniform(2, 3))
            await page.locator('[id="popup-create-account-checkbox"]').check()
            await asyncio.sleep(random.uniform(2, 3))
            await page.click(".c-btn.button-register.mt-3")
            await asyncio.sleep(random.uniform(1.91, 2.02))
            await page.click(".btn.name-generator-header")
            await asyncio.sleep(random.uniform(2, 3))
            await page.click(".btn.mt-2.js-name-generator-button")
            await asyncio.sleep(random.uniform(12, 20))
            await page.click(".prof.mag")
            await asyncio.sleep(random.uniform(1, 2))
            await page.click(".btn.btn-more-worlds")
            await asyncio.sleep(random.uniform(1, 2))
            await page.locator('[id="world-select-input-katahha"]').check()
            await asyncio.sleep(random.uniform(1, 2))
            await page.click(".btn.btn--lg.js-create-character-button.g-recaptcha")
            await asyncio.sleep(random.uniform(16, 24))
            await page.click(".skip-tutorial-span")
            await asyncio.sleep(random.uniform(0.4, 0.6))
            await settings()
    except TimeoutError:
        print("Element was not found on the page.")
    except Exception as e:
        print("Error:", e)
