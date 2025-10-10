from bot.game.moving.moving import go_to_target
from bot.game.moving.pathfiding import a_star
from bot.game.navigation.helpers import get_gateway_pos, get_gateways
from bot.game.navigation.maps import go_to_gateway
from bot.utils.dialogues import talk_with_npc
from bot.utils.helpers import current_location_map, current_position
from bot.utils.items import buy_item
from bot.utils.world_graph import bfs_distance, bfs_path
from bot.data.potions_data import potions_dict

import json

with open("bot/data/healers_npcs.json", "r", encoding="utf-8") as f:
    healers_list = json.load(f)


async def healer_selector(hero_lvl, current_map, healers_list, world_graph):
    available_healers = [
        m for m in healers_list if hero_lvl >= m.get("access_min_lvl", 0)
    ]
    if not available_healers:
        return None

    min_dist = float("inf")
    nearest_healer = None
    for healer in available_healers:
        healer_map_id = str(healer.get("npc_location_id"))
        dist = bfs_distance(world_graph, str(current_map), healer_map_id)
        if dist < min_dist:
            min_dist = dist
            nearest_healer = healer

    return nearest_healer


def select_potion(hero_lvl, potions_dict):
    available = [p for p in potions_dict if hero_lvl <= p["max_lvl"]]
    if not available:
        return None

    selected = min(available, key=lambda x: x["max_lvl"])
    return selected["potion_id"]


async def buy_potions(hero_lvl, current_map, GRAPH):

    nearest_healer = await healer_selector(
        hero_lvl, current_map, healers_list, GRAPH
    )
    if not nearest_healer:
        return

    healer_map_id = str(nearest_healer["npc_location_id"])
    healer_coords = nearest_healer.get("npc_coords", [0, 0])

    if current_map != healer_map_id:
        path_ids = bfs_path(GRAPH, current_map, healer_map_id)
        if not path_ids:
            return

        for map_id in path_ids[1:]:
            gateways = await get_gateways()
            gw_loc = await get_gateway_pos(gateways, map_id)
            goal = (gw_loc[0], gw_loc[1])
            await go_to_gateway(goal)

    map_2d = await current_location_map()
    start_pos = await current_position()
    start = (start_pos[0], start_pos[1])
    goal = tuple(nearest_healer["npc_coords"])

    path = a_star(map_2d, start, goal)
    await go_to_target(path, mobId=nearest_healer["npc_id"], mobType="healer")

    await talk_with_npc(nearest_healer["npc_id"], options=[2])

    potion_id = select_potion(hero_lvl, potions_dict)

    if potion_id:
        amount_needed = 30
        await buy_item([potion_id] * amount_needed, amount_needed)
