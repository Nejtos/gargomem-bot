import asyncio

from bot.game.entities.map import Map
from bot.game.entities.player import Player
from bot.game.services.exp_service import (
    execute_farming_action,
    find_nearest_mob_with_path,
    handle_no_mobs_case,
    prepare_potions_and_items,
    resolve_exp_map,
    travel_to_exp_map,
)
from bot.game.services.map_services import current_location_map


async def run_exp_workflow(heal_event: asyncio.Event, selected_exp: str | None, ui) -> None:
    map_entity = Map()
    player = Player()

    hero_lvl = await player.lvl()
    curr_map = str(await map_entity.get_current_map_id())

    curr_map = await prepare_potions_and_items(hero_lvl, curr_map, heal_event)

    exp_name, exp_map_name, mobs_name = await resolve_exp_map(selected_exp, hero_lvl)
    if not exp_map_name:
        print("Brak skonfigurowanej mapy dla expowiska:", selected_exp)
        return
    if not mobs_name:
        print(f"Brak zdefiniowanych potworów dla expowiska: {selected_exp}")
        return

    await travel_to_exp_map(curr_map, exp_name, ui)

    map_2d = await current_location_map()
    start_pos = await player.position()
    start = (start_pos[0], start_pos[1])

    target_mob, path = await find_nearest_mob_with_path(map_2d, start, mobs_name)

    if not target_mob:
        await handle_no_mobs_case(selected_exp, map_2d, start)
    else:
        await execute_farming_action(path, target_mob, heal_event)