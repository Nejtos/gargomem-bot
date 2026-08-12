import asyncio
from functools import wraps
import re
import traceback

from bot.core.driver import MyDriver


def retry(max_attempts=10, delay=3, refresh=False):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 1
            current_e2 = None
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception:
                    traceback.print_exc()
                    if attempt >= max_attempts:
                        raise
                    if refresh is True:
                        from bot.ui.botUI import BotUI
                        from bot.game.services.e2_service import restore_interface

                        ui = BotUI()
                        page = await MyDriver().get_driver()
                        if attempt == 1:
                            current_e2 = await ui.get_selected_elita2()
                        print(f"Błąd, robię F5 (próba {attempt}/{max_attempts})...")
                        await page.reload()
                        await asyncio.sleep(0.1)
                        await restore_interface(current_e2)
                    await asyncio.sleep(delay)
                    attempt += 1

        return wrapper

    return decorator


async def get_respawn_time():
    driver = await MyDriver().get_driver()
    dazed_time = await driver.evaluate(
        """
        () => {
            const el = document.querySelector('.dazed-time');
            return el ? el.textContent.trim() : null;
        }
    """,
        isolated_context=False,
    )

    if not dazed_time:
        return 0

    match = re.match(r"(?:(\d+)min)?\s*(\d+)s", dazed_time)
    if match:
        minutes = int(match.group(1)) if match.group(1) else 0
        seconds = int(match.group(2))
        return minutes * 60 + seconds

    return 0
