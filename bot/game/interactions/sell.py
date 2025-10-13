from bot.game.moving.moving import go_to_target
from bot.game.moving.pathfiding import a_star
from bot.game.navigation.helpers import get_gateway_pos, get_gateways
from bot.game.navigation.maps import go_to_gateway
from bot.utils.dialogues import talk_with_npc
from bot.utils.helpers import current_location_map, current_position
from bot.utils.items import quick_sell_items
from bot.utils.world_graph import bfs_distance, bfs_path

import json

with open("bot/data/merchants_npcs.json", "r", encoding="utf-8") as f:
    merchants_list = json.load(f)


async def merchant_selector(hero_lvl, current_map, merchants_list, world_graph):
    available_merchants = [
        m
        for m in merchants_list.get("general", [])
        if hero_lvl >= m.get("access_min_lvl", 0)
    ]
    if not available_merchants:
        return None

    min_dist = float("inf")
    nearest_merchant = None
    for merchant in available_merchants:
        merchant_map_id = str(merchant.get("npc_location_id"))
        dist = bfs_distance(world_graph, str(current_map), merchant_map_id)
        if dist < min_dist:
            min_dist = dist
            nearest_merchant = merchant

    return nearest_merchant


async def sell_items(hero_lvl, current_map, GRAPH):

    nearest_merchant = await merchant_selector(
        hero_lvl, current_map, merchants_list, GRAPH
    )
    if not nearest_merchant:
        return

    merchant_map_id = str(nearest_merchant["npc_location_id"])
    merchant_coords = nearest_merchant.get("npc_coords", [0, 0])

    if current_map != merchant_map_id:
        path_ids = bfs_path(GRAPH, current_map, merchant_map_id)
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
    goal = tuple(nearest_merchant["npc_coords"])

    path = a_star(map_2d, start, goal)
    await go_to_target(path, mobId=nearest_merchant["npc_id"], mobType="merchant")

    await talk_with_npc(nearest_merchant["npc_id"], options=[1])

    await quick_sell_items()
