import asyncio
import random
from bot.game.interactions.attack import attack_mob
from bot.game.interactions.buy import buy_potions
from bot.game.interactions.heal import get_potions, potions_amount
from bot.game.moving.moving import go_to_target
from bot.game.navigation.maps_dict import flatten_maps, maps_dict
from bot.game.navigation.helpers import (
    get_current_map,
    get_gateway_pos,
    get_gateways,
    get_main_map_name,
)
from bot.game.navigation.maps import change_exp_map, go_to_gateway
from bot.game.services.helpers import find_mobs
from bot.data.exp_data import exp_dict
from bot.ui.botUI import set_selected_exp_to_new_value
from bot.utils.helpers import (
    current_location_map,
    current_position,
    exp_selector,
    find_nearest_mob,
    get_hero_lvl,
    get_npc_id,
    get_npc_position,
)
from bot.utils.world_graph import load_world_graph, bfs_path

GRAPH = load_world_graph("bot/data/world_maps.json")


async def exp_service(heal_event, selected_exp):
    hero_lvl = await get_hero_lvl()
    curr_map = str(await get_current_map())

    potions = await get_potions()
    amount = await potions_amount(potions)

    if amount < 0:
        await buy_potions(hero_lvl, curr_map, GRAPH)

    exp_name, exp_map_name = exp_selector(exp_dict, hero_lvl)
    if not exp_map_name:
        print("No exp map found for level:", hero_lvl)
        return

    exp_maps = flatten_maps(maps_dict[exp_name])

    if curr_map not in exp_maps:
        path_ids = bfs_path(GRAPH, curr_map, exp_maps[0])
        if not path_ids:
            return

        for map_id in path_ids[1:]:
            gateways = await get_gateways()
            gw_loc = await get_gateway_pos(gateways, map_id)
            goal = (gw_loc[0], gw_loc[1])
            await go_to_gateway(goal)

        await set_selected_exp_to_new_value(exp_name)

    map_2d = await current_location_map()
    start_pos = await current_position()
    start = (start_pos[0], start_pos[1])

    mobs_name = []
    exp_name = None
    for group, data in exp_dict.items():
        if data.get("target_map") == exp_map_name:
            mobs_name = data["mobs"]
            exp_name = group
            break
    if not mobs_name:
        print(f"No mobs available for exping on map: {exp_name}")
        return

    mob_positions = await get_mobs_positions(mobs_name)
    filtered_positions = filter_valid_positions(mob_positions, [])

    nearest_npc, path = await find_nearest_mob_with_path(
        map_2d, start, filtered_positions
    )
    if not nearest_npc:
        await handle_no_mobs_case(selected_exp, map_2d, start)
    else:
        mob_id, mob_type = await get_npc_id(nearest_npc)
        await execute_farming_action(
            path, exp_map_name, selected_exp, mobs_name[0], mob_id, mob_type, heal_event
        )


async def get_mobs_positions(mobs_name):
    positions = []
    for mob_name in mobs_name:
        positions += await get_npc_position(mob_name)
    return positions


def filter_valid_positions(mob_positions, map_err_pos):
    return [pos for pos in mob_positions if pos not in map_err_pos]


async def handle_no_mobs_case(selected_exp, map_2d, start):
    curr_map = await get_current_map()
    gateways = await get_gateways()
    await change_exp_map(
        selected_exp,
        curr_map,
        gateways,
        map_2d,
        start,
    )
    await asyncio.sleep(random.uniform(0.13, 0.29))

    map_2d = await current_location_map()
    await asyncio.sleep(random.uniform(0.25, 0.4))

    return


async def find_nearest_mob_with_path(map_2d, start, positions):
    nearest_npc, path = await find_nearest_mob(map_2d, start, positions)
    await asyncio.sleep(random.uniform(0.13, 0.29))

    if path and len(path) > 1:
        return nearest_npc, path
    return None, None


async def execute_farming_action(
    path, selected_exp, selected_e2, mob_name, mob_id, mob_type, heal_event
):
    print("Path found:", path)

    result = await go_to_target(path, mob_id)
    if result:
        await attack_mob(
            mob_id, mob_name, heroes=False, heal_event=heal_event
        )
    await asyncio.sleep(random.uniform(0.15, 0.23))


async def handle_no_path_case(start, goal, map_err_pos):
    if goal != start:
        map_err_pos.append(goal)
    await asyncio.sleep(random.uniform(0.84, 1.11))
    return map_err_pos
