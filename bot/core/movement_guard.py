import asyncio
import random
from bot.core.driver import MyDriver
from bot.utils.helpers import current_position


async def check_collision(driver, x, y):
    script = f"""
        () => {{
            return window.Engine.map.col.check({x}, {y});
        }}
    """
    result = await driver.evaluate(script, isolated_context=False)
    await asyncio.sleep(random.uniform(0.25, 0.35))
    return result in (0, "0")


def generate_possible_moves(x, y):
    return [
        (x + dx, y + dy)
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
        if not (dx == 0 and dy == 0)
    ]


async def is_move_blocked(captcha_event=None):
    driver = await MyDriver().get_driver()

    overlay_visible = await driver.evaluate(
        """
        (function() {
            const overlay = document.querySelector('.stasis-incoming-overlay.map-overlay');
            return overlay && overlay.style.display !== 'none';
        })();
        """,
        isolated_context=False
    )

    is_blocked = await driver.evaluate(
        "() => window.Engine.hero.checkStasis();", isolated_context=False
    )

    if overlay_visible or is_blocked:
        await asyncio.sleep(random.uniform(1, 4))
        start_x, start_y = await current_position()
        possible_moves = generate_possible_moves(start_x, start_y)
        random.shuffle(possible_moves)

        for move_x, move_y in possible_moves:
            await asyncio.sleep(random.uniform(2.5, 3.5))
            if await check_collision(driver, move_x, move_y):
                move_script = f"""
                    window.Engine.hero.autoGoTo({{
                        x: {move_x},
                        y: {move_y}
                    }});
                """
                await driver.evaluate(move_script, isolated_context=False)
                await asyncio.sleep(random.uniform(1.5, 2))
                break

    script = """
        (function() {
            const captchaElement = document.querySelector(
                '.pre-captcha.show, .border-window.ui-draggable.captcha-window.transparent.window-on-peak.no-exit-button'
            );
            const isCaptchaPresent = captchaElement !== null;
            return isCaptchaPresent;
        })();
    """
    is_captcha = await driver.evaluate(script, isolated_context=False)
    if is_captcha:
        captcha_event.set()
