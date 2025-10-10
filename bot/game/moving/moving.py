import asyncio
import random
from bot.core.driver import MyDriver
from bot.game.moving.pathfiding import a_star
from bot.utils.helpers import current_position, get_npc_position


async def go_to_target(path, mobId=None, mobType=None):
    if not path:
        return False

    if len(path) <= 2:
        return True

    driver = await MyDriver().get_driver()

    if mobType == "heroes":
        target_x, target_y = path[-1]
    else:
        target_x, target_y = path[-2]

    script = f"""window.Engine.hero.searchPath({{x: {target_x}, y: {target_y}}});"""
    await driver.evaluate(script, isolated_context=False)

    if (len(path) <= 6 and mobId is not None) or (
        mobType == "e2" or mobType == "heroes" or mobType == "healer"
    ):
        mob_alive_script = f"""
            () => {{
                let e2 = window.Engine.npcs.getById('{mobId}');
                return e2 !== undefined && e2 !== null ? 1 : 0;
            }}
        """

        checker = None
        while checker != (target_x, target_y):
            current_pos = await current_position()
            checker = (current_pos[0], current_pos[1])

            if (
                await driver.evaluate(mob_alive_script, isolated_context=False) == 0
                and mobType != "heroes"
            ):
                return False

            await asyncio.sleep(random.uniform(0.16, 0.25))

        return True
    else:
        await asyncio.sleep(random.uniform(0.15, 0.23))
        return False


async def back_to_start(map_2d=None, goal=None):
    """
    Po zabiciu E2 bot wykonuje losowy ruch (również po skosie)
    o 1–3 kratki z pola, gdzie była E2.
    Używa a_star, żeby ruch był legalny (tylko po dostępnych polach).
    """
    if goal is None:
        pos = await current_position()
        goal = (pos[0], pos[1])

    directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

    possible_targets = []
    for distance in range(1, 3):
        for dx, dy in directions:
            target_x = goal[0] + dx * distance
            target_y = goal[1] + dy * distance
            possible_targets.append((target_x, target_y))

    valid_targets = []
    for target in possible_targets:
        path = a_star(map_2d, goal, target)
        if path and len(path) >= 2:
            valid_targets.append((target, path))

    if not valid_targets:
        return

    target, path = random.choice(valid_targets)

    await go_to_target(path)


async def create_path(mob_name, currentMap):
    start_position = await current_position()
    start = (start_position[0], start_position[1])
    mobPos = await get_npc_position(mob_name)
    if not mobPos:
        return None
    goal = mobPos[0]
    if start == goal:
        return None
    path = a_star(currentMap, start, goal)
    if path and len(path) != 1:
        return path
    return None
