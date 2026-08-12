import asyncio
import random

from bot.game.behaviors.attack import attack_mob
from bot.game.behaviors.buy import buy_item
from bot.game.behaviors.sell import sell_items
from bot.game.behaviors.talk import talk_with_npc
from bot.game.entities.map import Map
from bot.game.entities.mob import Mob
from bot.game.entities.player_inventory import PlayerInventory
from bot.game.services.heroes.world_graph import load_world_graph
from bot.game.services.item_service import select_potion
from bot.game.services.map_services import current_location_map
from bot.game.services.mob_service import find_nearest_mob, get_mobs_by_name
from bot.game.services.move_service import bfs_path, go_to_gateway, go_to_target
from bot.game.services.navigate import (
    change_exp_map,
    flatten_maps,
    navigate_to_service_npc,
    travel_to_target_map,
)

from bot.data.potions_data import potions_dict
from bot.data.exp_data import exp_dict
from bot.data.map_order_data import maps_dict

GRAPH = load_world_graph("bot/data/world_maps.json")


def exp_selector(exp_maps, hero_lvl):
    available = {
        key: data for key, data in exp_maps.items() if data["max_lvl"] >= hero_lvl
    }
    if not available:
        print("No suitable EXP maps for the current level!")
        return None
    selected_key, selected_data = min(
        available.items(), key=lambda item: item[1]["max_lvl"]
    )
    return selected_key, selected_data["target_map"]


async def prepare_potions_and_items(
    hero_lvl: int,
    curr_map: str,
    heal_event: asyncio.Event,
) -> str:
    """Sprzedaje przedmioty jeśli brak miejsca w eq i dokupuje mikstury."""
    map_entity = Map()
    player_eq = PlayerInventory()

    potions = await player_eq.get_potions()
    amount = len(potions)

    items_amount = await player_eq.get_free_slots()
    if items_amount == 0:
        target_service_npc = await navigate_to_service_npc(
            hero_lvl, curr_map, "merchant", GRAPH
        )
        if target_service_npc:
            await talk_with_npc(target_service_npc["npc_id"], _options=[1])
            await sell_items()
        curr_map = str(await map_entity.get_current_map_id())

    if amount == 0:
        target_service_npc = await navigate_to_service_npc(
            hero_lvl, curr_map, "merchant", GRAPH
        )
        if target_service_npc:
            await talk_with_npc(target_service_npc["npc_id"], _options=[1])
            await asyncio.sleep(random.uniform(1.15, 1.45))
            await sell_items()
        curr_map = str(await map_entity.get_current_map_id())
        target_service_npc = await navigate_to_service_npc(
            hero_lvl, curr_map, "healer", GRAPH
        )
        if target_service_npc:
            await talk_with_npc(target_service_npc["npc_id"], _options=[2])
            await asyncio.sleep(random.uniform(1.15, 1.45))
            potion_id = select_potion(hero_lvl, potions_dict)
            if potion_id:
                await buy_item([potion_id], 30)
            await asyncio.sleep(random.uniform(0.15, 0.25))
            heal_event.set()
        curr_map = str(await map_entity.get_current_map_id())

    return curr_map


async def resolve_exp_map(
    selected_exp: str | None,
    hero_lvl: int,
) -> tuple[str | None, str | None, list[str]]:
    """Ustala nazwę expowiska, docelową mapę i listę mobów do bicia.
    Jeśli selected_exp jest nieustawione albo postać przebiła docelowy poziom,
    dobiera wyższe expowisko automatycznie na podstawie hero_lvl."""
    exp_data = exp_dict.get(selected_exp)

    if not exp_data or hero_lvl > exp_data["max_lvl"]:
        selected = exp_selector(exp_dict, hero_lvl)
        if not selected:
            return None, None, []
        exp_name, exp_map_name = selected
        exp_data = exp_dict.get(exp_name)
    else:
        exp_name = selected_exp
        exp_map_name = exp_data.get("target_map")

    mobs_name = exp_data.get("mobs", []) if exp_data else []
    return exp_name, exp_map_name, mobs_name


async def travel_to_exp_map(curr_map: str, exp_name: str, ui) -> None:
    """Ustala i przemieszcza postać aż bot znajdzie się na jednej z map expowiska."""
    exp_maps = flatten_maps(maps_dict.get(exp_name, []))
    if exp_maps and curr_map not in exp_maps:
        await travel_to_target_map(curr_map, exp_maps, ui)
    await ui.set_selected_exp_to_new_value(exp_name)


async def get_mobs_by_names(mobs_names: list[str]) -> list[Mob]:
    mobs = []
    for mob_name in mobs_names:
        mobs.extend(await get_mobs_by_name(mob_name))
    return mobs


async def find_nearest_mob_with_path(
    map_2d,
    start: tuple[int, int],
    mobs_name: list[str],
) -> tuple[Mob | None, list[tuple[int, int]] | None]:
    mobs = await get_mobs_by_names(mobs_name)
    nearest_mob, path = await find_nearest_mob(map_2d, start, mobs)
    await asyncio.sleep(random.uniform(0.13, 0.29))

    if path and len(path) > 1:
        print(f"Path found: {path}")
        return nearest_mob, path
    return None, None


async def handle_no_mobs_case(
    selected_exp: str | None, map_2d, start: tuple[int, int]
) -> None:
    map_entity = Map()
    curr_map = await map_entity.get_current_map_id()
    gateways = await map_entity.get_current_map_gateways()
    await change_exp_map(
        selected_exp,
        curr_map,
        gateways,
        map_2d,
        start,
    )
    await asyncio.sleep(random.uniform(0.13, 0.29))
    await current_location_map()
    await asyncio.sleep(random.uniform(0.25, 0.4))


async def execute_farming_action(
    path, target_mob: Mob, heal_event: asyncio.Event
) -> None:
    print(target_mob)

    result = await go_to_target(path, target_mob.id)
    if result:
        await attack_mob(target_mob, heroes=False, heal_event=heal_event)
    await asyncio.sleep(random.uniform(0.15, 0.23))
