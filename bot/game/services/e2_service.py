import asyncio
from datetime import datetime, timedelta
import os
import random
import sys

import keyboard
from bot.game.services.mob_service import find_nearest_npc, get_mobs_by_name
from bot.game.services.move_service import a_star, back_to_start, go_to_target
import bot.globals as globals
from bot.core.driver import MyDriver
from bot.data.e2_data import e2_dict
from bot.game.auth.login import login
from bot.game.behaviors.attack import attack_mob
from bot.game.entities.mob import Mob
from bot.ui.botUI import BotUI


async def find_e2mob(selected_e2, e2mob_dict):
    if selected_e2 in e2mob_dict:
        return e2mob_dict[selected_e2]["mob_name"]
    else:
        return []


async def find_target_mob(selected_e2: str, start_position) -> Mob | None:
    mob_name = await find_e2mob(selected_e2, e2_dict)
    
    mobs = await get_mobs_by_name(mob_name)

    if not mobs:
        return None

    target_mob = await find_nearest_npc(start_position, mobs)

    return target_mob


async def calculate_path(map_2d, start, goal):
    if start == goal:
        return None

    path = a_star(map_2d, start, goal)
    if not path or len(path) == 1:
        return None

    print(f"Path found: {path}")
    return path


async def execute_farming_action(mob, path, heal_event):
    print(mob)
    
    if not mob:
        print(f"⚠️ Nie znaleziono potwora na pozycji: {mob.position}")
        return

    await asyncio.sleep(random.uniform(1.01, 1.3))
    result = await go_to_target(path, mob.id, mobType="e2")
    if result:
        await attack_mob(mob, heroes=False, heal_event=heal_event)

    await asyncio.sleep(random.uniform(0.5, 0.65))


async def calculate_respawn(lvl: int, multiplier: float, early_reduction: float) -> int:
    if lvl > 200:
        i = 18.5
    else:
        i = 0.7 + 0.18 * lvl - 0.00045 * lvl**2

    return round(round(60 * i / multiplier) * (1 - early_reduction))


async def schedule_next_login(current_time: datetime, selected_e2: str) -> datetime:
    mob_lvl = e2_dict[selected_e2]["mob_lvl"]
    next_respawn = await calculate_respawn(mob_lvl, multiplier=1, early_reduction=0.14)
    next_time = current_time + timedelta(seconds=next_respawn)
    print(f"Next login: ~{next_time.strftime('%H:%M:%S')}")
    return next_time


async def return_to_start(map_2d, goal) -> None:
    await back_to_start(map_2d, goal)


async def reload_game_and_prepare(next_login_time: datetime, selected_e2: str) -> None:
    if random.random() >= 0.8:
        return

    await asyncio.sleep(random.uniform(3.5, 6))
    page = await MyDriver().get_driver()
    await page.goto(os.getenv("GAME_URL"))

    await wait_until_login_time(next_login_time)
    await check_and_relogin(page)
    await restore_interface(selected_e2)


async def wait_until_login_time(next_login_time: datetime) -> None:
    while datetime.now() < next_login_time:
        if keyboard.is_pressed("|"):
            print("🛑 Program has stopped — closing browser...")
            try:
                await MyDriver().close_driver()
            finally:
                sys.exit(0)
        await asyncio.sleep(4)


async def check_and_relogin(page) -> None:
    try:
        if page is None or page.is_closed():
            print("Page is closed, skipping relogin")
            return
        checker = await page.query_selector(".c-btn.enter-game")
        if checker:
            await login()
    except Exception as e:
        print(f"Failed to check login status: {e}")


async def restore_interface(selected_e2: str) -> None:
    ui = BotUI()
    await ui.renderUI()
    await asyncio.sleep(random.uniform(2.5, 4.5))
    await ui.restore_UI(selected_e2)
    globals.is_game_loading[0] = True