import asyncio
from datetime import datetime
import os
import random
from dotenv import load_dotenv
import keyboard
from bot.core.driver import MyDriver
from bot.game.auth.login import login
from bot.ui.botUI import bot_interface

load_dotenv()


async def wait_until_login_time(next_login_time: datetime):
    while datetime.now() < next_login_time:
        if keyboard.is_pressed("|"):
            print("Program has stopped")
            await MyDriver().close_driver()
            break
        await asyncio.sleep(4)


async def check_and_relogin(page):
    checker = await page.query_selector(".c-btn.enter-game")
    if checker:
        await login()


async def restore_interface_for_heroes(selected_heroes: str):
    await bot_interface()
    await asyncio.sleep(random.uniform(2.5, 4.5))
    try:
        page = await MyDriver().get_driver()
        await page.evaluate(
            f"""
            try {{
                window.selectedHero = '{selected_heroes}';
                const sel = document.getElementById('heroesOptions') || document.getElementById('heroOptions');
                if (sel) {{
                    const opts = sel.options;
                    for (let i = 0; i < opts.length; i++) {{
                        if (opts[i].text === window.selectedHero) {{
                            sel.selectedIndex = i;
                            break;
                        }}
                    }}
                }}
            }} catch(e) {{}}
        """
        )
    except Exception:
        pass
    try:
        if (
            hasattr(globals, "is_game_loading")
            and isinstance(globals.is_game_loading, list)
            and globals.is_game_loading
        ):
            globals.is_game_loading[0] = True
    except Exception:
        pass


async def heroes_reload_game_and_prepare(
    next_login_time: datetime, selected_heroes: str
):
    await asyncio.sleep(random.uniform(3.5, 6.0))
    page = await MyDriver().get_driver()
    await page.goto(os.getenv("GAME_URL"))
    await wait_until_login_time(next_login_time)
    await check_and_relogin(page)
    await restore_interface_for_heroes(selected_heroes)
