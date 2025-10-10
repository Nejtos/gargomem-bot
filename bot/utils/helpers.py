import math
from bot.core.driver import MyDriver
from bot.game.moving.helpers import get_npcs_from_NI
from bot.game.moving.pathfiding import a_star
from bot.game.navigation.helpers import map_size, update_collisions


async def current_location_map():
    map_str = await update_collisions()
    max_map_size = await map_size()
    max_w = max_map_size[0]
    map_2d = [
        list(map_str[i : i + max_w + 1]) for i in range(0, len(map_str), max_w + 1)
    ]
    map_2d = [list(column) for column in zip(*map_2d)]
    return map_2d


async def get_npc_position(name):
    all_npcs = await get_npcs_from_NI()
    npcs_filtered = []
    for npc_id, npc_data in all_npcs.items():
        if npc_data["nick"] == name:
            x = npc_data["x"]
            y = npc_data["y"]
            npcs_filtered.append(tuple((x, y)))
    return npcs_filtered


async def get_npc_id(arr):
    all_npcs = await get_npcs_from_NI()
    coordinates = arr[0]
    resultX, resultY = coordinates
    mob_id = ""
    mob_type = -1
    for npc_id, npc_data in all_npcs.items():
        if npc_data["x"] == resultX and npc_data["y"] == resultY:
            mob_id = npc_data["id"]
            mob_type = npc_data["type"]
            break
    return mob_id, mob_type


async def find_nearest_mob(map, start, arr):
    distance = None
    nearest_mob = [(1, 1)]
    for mob_XY in arr:
        path = a_star(map, start, mob_XY)
        if path is not None:
            if distance is None or len(path) < len(distance):
                distance = path
                nearest_mob[0] = mob_XY
    return nearest_mob, distance


async def find_nearest_npc(start, filtered):
    hero_posX, hero_posY = start
    nearest_npc_XY = []
    nearest_npc_XY.append(filtered[0])
    nearest_npc_X, nearest_npc_Y = filtered[0]
    calculate_first_distance = math.sqrt(
        (nearest_npc_X - hero_posX) ** 2 + (nearest_npc_Y - hero_posY) ** 2
    )
    shortest_dist_holder = calculate_first_distance
    for filtr in filtered[1:]:
        filtered_X, filtered_Y = filtr
        current_dist = math.sqrt(
            (filtered_X - hero_posX) ** 2 + (filtered_Y - hero_posY) ** 2
        )
        if current_dist < shortest_dist_holder:
            shortest_dist_holder = current_dist
            nearest_npc_XY[0] = filtr
    return nearest_npc_XY


async def current_position():
    driver = await MyDriver().get_driver()
    script = """
        (function() {
            let position = [];
            position.push(window.Engine.hero.d.x);
            position.push(window.Engine.hero.d.y);
            return position;
        })();
    """
    heroPosition = await driver.evaluate(script, isolated_context=False)
    return heroPosition


async def accept_loot():
    driver = await MyDriver().get_driver()
    script = """
        () => window.Engine.loots.acceptLoot()
    """
    await driver.evaluate(script, isolated_context=False)


async def get_hero_prof():
    driver = await MyDriver().get_driver()
    script = """
        () => window.Engine.hero.d.prof
    """
    heroProf = await driver.evaluate(script, isolated_context=False)
    return heroProf


async def get_hero_lvl():
    driver = await MyDriver().get_driver()
    script = """
        () => {
            heroLvl = window.Engine.hero.d.lvl,
            return heroLvl
        }
    """
    heroLvl = await driver.evaluate(
        "() => window.Engine.hero.d.lvl", isolated_context=False
    )
    return heroLvl


async def is_hero_dead():
    driver = await MyDriver().get_driver()
    script = """
        () => {
            isHeroDead = window.Engine.dead
            return isHeroDead
        }
    """
    is_dead = await driver.evaluate("() => window.Engine.dead", isolated_context=False)
    return is_dead


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

