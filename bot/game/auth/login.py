import random
import asyncio
from bot.core.driver import MyDriver


async def login():
    page = await MyDriver().get_driver()
    try:
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
