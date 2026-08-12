import random
import asyncio
from bot.core.driver import MyDriver
from bot.game.auth.credentials import generate_credentials
from bot.game.auth.settings import settings


async def register(profile_num):
    page = await MyDriver().get_driver()
    username, password = generate_credentials(profile_num)
    try:
        register_btn = await page.query_selector(".c-btn.button-register.mt-3")
        if register_btn:
            await page.locator('[id="popup-create-account-login"]').fill(username)
            await asyncio.sleep(random.uniform(2, 3))
            await page.locator('[id="popup-create-account-password"]').fill(password)
            await asyncio.sleep(random.uniform(2, 3))
            await page.locator('[id="popup-create-account-password2"]').fill(password)
            await asyncio.sleep(random.uniform(2, 3))
            await page.locator('[id="popup-create-account-checkbox"]').check()
            await asyncio.sleep(random.uniform(2, 3))
            await page.click(".c-btn.button-register.mt-3")
            await asyncio.sleep(random.uniform(1.91, 2.02))
            await page.click(".btn.name-generator-header")
            await asyncio.sleep(random.uniform(2, 3))
            await page.click(".btn.mt-2.js-name-generator-button")
            await asyncio.sleep(random.uniform(3, 8))
            await page.click(".btn.btn-more-worlds")
            await asyncio.sleep(random.uniform(1, 2))
            await page.locator('[id="world-select-input-katahha"]').check()
            await asyncio.sleep(random.uniform(1, 2))
            await page.click(".btn.btn--lg.js-create-character-button.g-recaptcha")
            await asyncio.sleep(random.uniform(16, 24))
            await settings()
    except TimeoutError:
        print("Element was not found on the page.")
    except Exception as e:
        print("Error:", e)
