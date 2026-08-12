import json

from bot.game.services.move_service import bfs_distance

with open("bot/data/healers_npcs.json", "r", encoding="utf-8") as f:
    healers_list = json.load(f)
with open("bot/data/merchants_npcs.json", "r", encoding="utf-8") as f:
    merchants_list = json.load(f)

# Mapa typów przypisująca nazwę kategorii do odpowiedniej listy
NPC_DATA_MAP = {
    "healer": healers_list,
    "merchant": merchants_list.get("general", []) if isinstance(merchants_list, dict) else merchants_list
}

async def find_nearest_service_npc(hero_lvl, current_map, npc_type: str, world_graph):
    """
    npc_type: 'healer' lub 'merchant'
    """
    npc_list = NPC_DATA_MAP.get(npc_type, [])
    
    available_npcs = [
        npc for npc in npc_list if hero_lvl >= npc.get("access_min_lvl", 0)
    ]
    if not available_npcs:
        return None

    min_dist = float("inf")
    nearest_npc = None
    curr_map_str = str(current_map)

    for npc in available_npcs:
        npc_map_id = str(npc.get("npc_location_id"))
        dist = bfs_distance(world_graph, curr_map_str, npc_map_id)
        if dist < min_dist:
            min_dist = dist
            nearest_npc = npc

    return nearest_npc
