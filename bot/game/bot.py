import asyncio
import random
import sys
import keyboard
from bot.core.driver import MyDriver
from bot.core.movement_guard import is_move_blocked
from bot.game.tutorials.intro import (
    tutorial_part1,
    tutorial_part2,
    tutorial_part3,
    tutorial_part4,
)
from bot.core.captcha import is_captcha_active
from bot.ui.botUI import (
    get_selected_exp,
    get_selected_elita2,
    get_selected_heroes,
)
from bot.game.services.e2_service import e2_service
from bot.game.services.exp_service import exp_service
from bot.game.services.heroes.heroes_service import heroes_service
import bot.globals as globals


async def bot(heal_event, captcha_event):
    driver_instance = MyDriver()
    prof_index = await driver_instance.get_profNum()
    print(f"Bot is running - profile {prof_index}")
    globals.is_game_loading[0] = True

    try:
        while True:
            if keyboard.is_pressed("|"):
                print("🛑 Stop key detected — shutting down...")
                break
            await handle_game_flow(heal_event, captcha_event)
            await asyncio.sleep(0.1)
    except Exception as e:
        import traceback

        print("⚠️ BOT CRASH DETECTED ⚠️")
        traceback.print_exc()
        print(f"❌ Error message: {e}")
        await asyncio.sleep(3)
    finally:
        print("🛑 Bot has stopped — closing browser...")
        try:
            await driver_instance.close_driver()
        finally:
            sys.exit(0)


async def handle_game_flow(heal_event, captcha_event):
    captcha_active = await check_captcha_and_loading(captcha_event)

    selected_exp = await get_selected_exp()
    selected_e2 = await get_selected_elita2()
    selected_heroes = await get_selected_heroes()

    if selected_exp and selected_exp != "Wybierz":
        await handle_exp_selection(heal_event, selected_exp, selected_e2)
    elif selected_e2 and selected_e2 != "Wybierz" and captcha_active is False:
        await e2_service(heal_event, None, selected_e2)
    elif selected_heroes and selected_heroes != "Wybierz":
        await heroes_service(selected_heroes, heal_event)


async def check_captcha_and_loading(captcha_event):
    captcha_active = await is_captcha_active()

    if globals.is_game_loading[0] and captcha_active:
        captcha_event.set()
        await captcha_event.wait()
        await asyncio.sleep(random.uniform(2.0, 4.0))
    else:
        globals.is_game_loading[0] = False
        await is_move_blocked(captcha_event)

    return captcha_active


async def handle_exp_selection(heal_event, selected_exp, selected_e2):
    if selected_e2 and selected_e2 != "Wybierz":
        return

    tutorial_handlers = {
        "Intro P1": tutorial_part1,
        "Intro P2": tutorial_part2,
        "Intro P3": tutorial_part3,
        "Intro P4": tutorial_part4,
    }

    if selected_exp in tutorial_handlers:
        await tutorial_handlers[selected_exp]()
    elif selected_exp != "Intro":
        await exp_service(heal_event, selected_exp)