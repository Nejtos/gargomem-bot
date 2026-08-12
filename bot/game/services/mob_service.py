import math

from bot.core.driver import MyDriver
from bot.game.entities.mob import Mob
from bot.game.services.map_services import a_star, find_path_to_or_near


async def get_mobs_by_name(name: str) -> list[Mob]:
    mobs = Mob()
    all_npcs = await mobs.get_all_npcs()
    if not all_npcs:
        return []

    mobs_filtered: list[Mob] = []
    for npc_data in all_npcs.values():
        if npc_data.get("nick") == name:
            mobs_filtered.append(Mob.from_raw(npc_data))

    return mobs_filtered


async def find_nearest_quest_mob(map_2d, start, mobs: list[Mob]):
    if not mobs:
        return None, None

    distance = None
    nearest_mob = mobs[0]
    for mob in mobs:
        path = find_path_to_or_near(map_2d, start, mob.position)
        if path is not None:
            if distance is None or len(path) < len(distance):
                distance = path
                nearest_mob = mob
    return nearest_mob, distance


async def find_nearest_mob(map_2d, start, mobs: list[Mob]):
    if not mobs:
        return None, None

    distance = None
    nearest_mob = mobs[0]
    for mob in mobs:
        path = a_star(map_2d, start, mob.position)
        if path is not None:
            if distance is None or len(path) < len(distance):
                distance = path
                nearest_mob = mob
    return nearest_mob, distance


async def find_nearest_npc(start, mobs: list[Mob]) -> Mob | None:
    if not mobs:
        return None

    hero_posX, hero_posY = start

    nearest_mob = mobs[0]
    nearest_npc_X, nearest_npc_Y = nearest_mob.position

    shortest_dist = math.sqrt(
        (nearest_npc_X - hero_posX) ** 2 + (nearest_npc_Y - hero_posY) ** 2
    )

    for mob in mobs[1:]:
        fx, fy = mob.position
        dist = math.sqrt((fx - hero_posX) ** 2 + (fy - hero_posY) ** 2)

        if dist < shortest_dist:
            shortest_dist = dist
            nearest_mob = mob

    return nearest_mob


async def is_npc_walkover(goal):
    resultX, resultY = goal

    page = await MyDriver().get_driver()

    walk_over = await page.evaluate(
        f"""
        (() => {{
            const npcs = window.Engine.npcs.check();
            for (const npc of Object.values(npcs)) {{
                if (npc.d.x === {resultX} && npc.d.y === {resultY}) {{
                    return !!npc.walkOver;
                }}
            }}
            return false;
        }})()
        """,
        isolated_context=False,
    )

    return bool(walk_over)
