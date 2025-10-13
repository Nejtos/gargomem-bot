import random
import asyncio
from bot.core.driver import MyDriver


async def login(profile_num=None, creds=None):
    page = await MyDriver().get_driver()
    if profile_num is not None and creds is not None:
        if profile_num not in creds:
            raise KeyError(f"No login details for profile {profile_num}")
        username, password = creds[profile_num]
    try:
        login_input = await page.query_selector("#login-input")
        password_input = await page.query_selector("#login-password")
        if login_input and password_input:
            await asyncio.sleep(random.uniform(0.4, 0.6))
            await login_input.fill(username)
            await asyncio.sleep(random.uniform(0.7, 1.0))
            await password_input.fill(password)
            await asyncio.sleep(random.uniform(0.4, 0.75))
            login_button = await page.query_selector("#js-login-btn")
            if login_button:
                await login_button.click()
                await asyncio.sleep(random.uniform(2.0, 4.0))
        close_game_info_element = await page.query_selector(".close-game-info")
        if close_game_info_element:
            await page.wait_for_selector(".close-game-info", timeout=2000)
            await page.click(".close-game-info")
            await asyncio.sleep(random.uniform(1.91, 2.02))
        login_info_btn = await page.query_selector(".c-btn.enter-game")
        if login_info_btn:
            await page.wait_for_selector(".c-btn.enter-game", timeout=2000)
            await page.click(".c-btn.enter-game")
            await asyncio.sleep(random.uniform(3.61, 4.01))
    except TimeoutError:
        print("Element was not found on the page.")
    except Exception as e:
        print("Error:", e)
