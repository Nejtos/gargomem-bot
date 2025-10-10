import os
import sys
import random
import asyncio
from datetime import datetime, timedelta
import keyboard
from dotenv import load_dotenv
from bot.game.interactions.attack import attack_mob
from bot.game.moving.moving import back_to_start, go_to_target
from bot.game.moving.pathfiding import a_star
from bot.game.services.helpers import find_e2mob
from bot.data.e2_data import e2_dict
from bot.game.auth.login import login
from bot.ui.botUI import bot_interface
from bot.core.driver import MyDriver
import bot.globals as globals
from bot.utils.helpers import (
    current_location_map,
    current_position,
    find_nearest_npc,
    get_npc_id,
    get_npc_position,
)

load_dotenv()


async def e2_service(heal_event, selected_exp, selected_e2):
    current_time = datetime.now()
    map_2d = await current_location_map()
    start_position = await current_position()
    start = (start_position[0], start_position[1])

    mob_name, mob_pos, goal = await find_target_mob(selected_e2, start)
    if not mob_pos:
        goal = start
        await asyncio.sleep(random.uniform(0.35, 0.5))

    path_to_mob = await calculate_path(map_2d, start, goal)
    if not path_to_mob:
        return

    await execute_farming_action(
        path_to_mob,
        selected_exp,
        selected_e2,
        mob_name,
        heal_event,
        map_2d,
        goal,
        start,
    )

    next_login_time = await schedule_next_login(current_time, selected_e2)

    await return_to_start(map_2d, goal, start)

    await reload_game_and_prepare(next_login_time, selected_e2)


async def find_target_mob(selected_e2, start_position):
    mob_name = await find_e2mob(selected_e2, e2_dict)
    mob_positions = await get_npc_position(mob_name)

    if not mob_positions:
        return mob_name, None, start_position

    nearest_npc = await find_nearest_npc(start_position, mob_positions)
    mob_id, mob_type = await get_npc_id(nearest_npc)
    print(f"NPC_XY: {nearest_npc}")

    return mob_name, mob_positions, nearest_npc[0]


async def calculate_path(map_2d, start, goal):
    if start == goal:
        return None

    path = a_star(map_2d, start, goal)
    if not path or len(path) == 1:
        return None

    print(f"Path found: {path}")
    return path


async def execute_farming_action(
    path, selected_exp, selected_e2, mob_name, heal_event, map_2d, goal, start
):
    mob_id, mob_type = await get_npc_id((goal,))
    await asyncio.sleep(random.uniform(1.11, 1.73))

    result = await go_to_target(path, mob_id, mobType="e2")
    if result:
        await attack_mob(mob_id, mob_name, heroes=False, heal_event=heal_event)

    await asyncio.sleep(random.uniform(0.5, 0.65))


async def calculate_respawn(lvl, multiplier, early_reduction):
    if lvl > 200:
        i = 18.5
    else:
        i = 0.7 + 0.18 * lvl - 0.00045 * lvl**2

    reduced_time_seconds = round(round(60 * i / multiplier) * (1 - early_reduction))
    return reduced_time_seconds


async def schedule_next_login(current_time, selected_e2):
    mob_lvl = e2_dict[selected_e2]["mob_lvl"]
    next_respawn = await calculate_respawn(mob_lvl, multiplier=1, early_reduction=0.14)
    next_time = current_time + timedelta(seconds=next_respawn)
    log_time_str = next_time.strftime("%H:%M:%S")
    print(f"Next login: ~{log_time_str}")
    return next_time


async def return_to_start(map_2d, goal, start):
    await back_to_start(map_2d, goal)
    # return_path = a_star(map_2d, goal, start)
    # if return_path:
        # await back_to_start(return_path)


async def reload_game_and_prepare(next_login_time, selected_e2):
    if random.random() >= 0.8:
        return

    await asyncio.sleep(random.uniform(3.5, 6))
    page = await MyDriver().get_driver()
    await page.goto(os.getenv("GAME_URL"))

    await wait_until_login_time(next_login_time)

    await check_and_relogin(page)

    await restore_interface(selected_e2)


async def wait_until_login_time(next_login_time):
    while datetime.now() < next_login_time:
        if keyboard.is_pressed("|"):
            print("🛑 Program has stopped — closing browser...")
            try:
                await MyDriver().close_driver()
            finally:
                sys.exit(0)
        await asyncio.sleep(4)


async def check_and_relogin(page):
    try:
        if page is None or page.is_closed():
            print("Page is closed, skipping relogin")
            return
        checker = await page.query_selector(".c-btn.enter-game")
        if checker:
            await login()
    except Exception as e:
        print(f"Failed to check login status: {e}")


async def restore_interface(selected_e2):
    await bot_interface()
    await asyncio.sleep(random.uniform(2.5, 4.5))

    page = await MyDriver().get_driver()
    await page.evaluate(
        f"""
        window.selectedE2 = '{selected_e2}';
        let selectElement2 = document.getElementById('e2Options');
        let options2 = selectElement2.options;
        for (let i = 0; i < options2.length; i++) {{
            if (options2[i].text === window.selectedE2) {{
                selectElement2.selectedIndex = i;
                break;
            }}
        }}
    """
    )
    globals.is_game_loading[0] = True
