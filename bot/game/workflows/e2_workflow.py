import asyncio
from datetime import datetime
import random

from bot.game.entities.player import Player
from bot.game.services.e2_service import calculate_path, execute_farming_action, find_target_mob, reload_game_and_prepare, return_to_start, schedule_next_login
from bot.game.services.map_services import current_location_map


async def run_e2_workflow(heal_event: asyncio.Event, selected_exp: str | None, selected_e2: str) -> None:
    current_time = datetime.now()
    map_2d = await current_location_map()
    player = Player()
    start = tuple(await player.position())

    target_mob = await find_target_mob(selected_e2, start)
    if not target_mob:
        await asyncio.sleep(random.uniform(0.35, 0.5))
        return

    path_to_mob = await calculate_path(map_2d, start, target_mob.position)
    if not path_to_mob:
        return

    await execute_farming_action(
        target_mob,
        path_to_mob,
        heal_event,
    )

    next_login_time = await schedule_next_login(current_time, selected_e2)

    await return_to_start(map_2d, target_mob.position)

    await reload_game_and_prepare(next_login_time, selected_e2)