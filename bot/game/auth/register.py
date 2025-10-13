import os
import random
import asyncio
import string
from bot.core.driver import MyDriver
from bot.game.auth.settings import settings


async def register(profile_num):
    page = await MyDriver().get_driver()
    username, password = generate_credentials(profile_num)
    try:
        register_btn = await page.query_selector(".c-btn.button-register.mt-3")
        if register_btn:
            await page.locator('[id="popup-create-account-login"]').fill(username)
            await asyncio.sleep(random.uniform(2, 3))
            # await page.click(".cc-btn.cc-allow")
            # await asyncio.sleep(random.uniform(0.4, 0.7))
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
            await asyncio.sleep(random.uniform(0.5, 0.75))
            await settings()
    except TimeoutError:
        print("Element was not found on the page.")
    except Exception as e:
        print("Error:", e)


def generate_credentials(profile_num: int, save_path="bot/data/login_data.txt"):
    username = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    password = "".join(
        random.choices(string.ascii_letters + string.digits + string.punctuation, k=10)
    )

    line = f"{profile_num},{username},{password}\n"

    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

    with open(save_path, "a", encoding="utf-8") as f:
        f.write(line)

    return username, password
