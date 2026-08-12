from collections import deque

from bot.game.entities.map import Map
from bot.game.entities.player import Player
from bot.game.services.map_services import a_star, current_location_map
from bot.game.services.mob_service import get_mobs_by_name
import asyncio
import random
from typing import Awaitable, Callable, Literal, Optional

from bot.core.driver import MyDriver

MobType = Literal["exp", "e2", "heroes", "healer", "merchant", "quest", "gateway"]

MOB_ALIVE_CHECK_TYPES: frozenset[str] = frozenset({"exp", "e2", "heroes", "healer", "merchant", "quest"})
NO_DEATH_CHECK_TYPES: frozenset[str] = frozenset({"heroes", "quest"})
END_OF_PATH_TYPES: frozenset[str] = frozenset({"heroes", "gateway"})

MAX_MOVE_ITERATIONS = 200
STALL_TIMEOUT_SECONDS = 4.0  # przerwij jeśli pozycja się nie zmienia w s
FOLLOW_PATH_STALL_TIMEOUT_SECONDS = 6.0
FOLLOW_PATH_MAX_WAIT_SECONDS = 80.0

AbortCheck = Callable[[], Awaitable[bool]]


async def go_to_target(
    path: list[tuple[int, int]] | None,
    mobId: str | None = None,
    mobType: MobType | None = None,
    should_abort: Optional[AbortCheck] = None,
) -> bool:
    """
    should_abort: opcjonalny async callback zwracający True, jeśli akcja powinna
    zostać natychmiast przerwana (np. quest wyłączony w UI w trakcie ruchu).
    Sprawdzany wewnątrz pętli oczekiwania na dojście, nie tylko przed jej startem.
    """
    player = Player()
    if not path:
        return False

    if len(path) <= 2:
        return True

    driver = await MyDriver().get_driver()

    if mobType in END_OF_PATH_TYPES:
        target_x, target_y = path[-1]
    else:
        target_x, target_y = path[-2]

    script = f"""
        (() => {{
            const engine = window.getEngine ? window.getEngine() : window.Engine;
            if (!engine || !engine.hero || !engine.hero.searchPath) {{
                console.error("[BOT] go_to_target: nie znaleziono engine.hero.searchPath");
                return;
            }}
            engine.hero.searchPath({{x: {target_x}, y: {target_y}}});
        }})();
    """
    await driver.evaluate(script, isolated_context=False)

    should_track = (len(path) <= 6 and mobId is not None) or mobType in MOB_ALIVE_CHECK_TYPES

    if not should_track:
        await asyncio.sleep(random.uniform(0.15, 0.23))
        return False

    if mobId is None:
        return await _wait_until_arrived(target_x, target_y, should_abort)

    mob_alive_script = f"""
        () => {{
            let e2 = window.getEngine ? window.getEngine().npcs.getById('{mobId}') : window.Engine.npcs.getById('{mobId}');
            return e2 !== undefined && e2 !== null ? 1 : 0;
        }}
    """

    checker: tuple[int, int] | None = None
    iterations = 0
    last_position: tuple[int, int] | None = None
    stall_started_at: float | None = None
    loop = asyncio.get_event_loop()

    while checker != (target_x, target_y):
        iterations += 1
        if iterations > MAX_MOVE_ITERATIONS:
            print(f"⚠️ go_to_target: przekroczono limit iteracji dla celu ({target_x}, {target_y})")
            return False

        if should_abort is not None and await should_abort():
            print("🔴 go_to_target: przerwano ruch (should_abort=True)")
            return False

        current_pos = await player.position()
        checker = (current_pos[0], current_pos[1])

        now = loop.time()
        if checker != last_position:
            last_position = checker
            stall_started_at = now
        elif stall_started_at is not None and (now - stall_started_at) >= STALL_TIMEOUT_SECONDS:
            print(f"⚠️ go_to_target: brak ruchu przez {STALL_TIMEOUT_SECONDS}s @ {checker} — ponawiam searchPath.")
            await driver.evaluate(script, isolated_context=False)
            stall_started_at = now

        mob_alive = await driver.evaluate(mob_alive_script, isolated_context=False)
        if mob_alive == 0 and mobType not in NO_DEATH_CHECK_TYPES:
            return False

        await asyncio.sleep(random.uniform(0.16, 0.25))

    return True


async def _wait_until_arrived(
    target_x: int,
    target_y: int,
    should_abort: Optional[AbortCheck] = None,
) -> bool:
    player = Player()
    driver = await MyDriver().get_driver()
    script = f"""
        (() => {{
            const engine = window.getEngine ? window.getEngine() : window.Engine;
            if (!engine || !engine.hero || !engine.hero.searchPath) {{
                console.error("[BOT] go_to_target: nie znaleziono engine.hero.searchPath");
                return;
            }}
            engine.hero.searchPath({{x: {target_x}, y: {target_y}}});
        }})();
    """
    checker: tuple[int, int] | None = None
    iterations = 0
    last_position: tuple[int, int] | None = None
    stall_started_at: float | None = None
    loop = asyncio.get_event_loop()

    while checker != (target_x, target_y):
        iterations += 1
        if iterations > MAX_MOVE_ITERATIONS:
            return False

        if should_abort is not None and await should_abort():
            print("🔴 _wait_until_arrived: przerwano ruch (should_abort=True)")
            return False

        current_pos = await player.position()
        checker = (current_pos[0], current_pos[1])

        now = loop.time()
        if checker != last_position:
            last_position = checker
            stall_started_at = now
        elif stall_started_at is not None and (now - stall_started_at) >= STALL_TIMEOUT_SECONDS:
            print(f"⚠️ _wait_until_arrived: brak ruchu przez {STALL_TIMEOUT_SECONDS}s @ {checker} — ponawiam searchPath.")
            await driver.evaluate(script, isolated_context=False)
            stall_started_at = now

        await asyncio.sleep(random.uniform(0.16, 0.25))

    return True


async def back_to_start(map_2d=None, goal: tuple[int, int] | None = None) -> None:
    if goal is None:
        player = Player()
        pos = await player.position()
        goal = (pos[0], pos[1])

    directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

    possible_targets = [
        (goal[0] + dx * distance, goal[1] + dy * distance)
        for distance in range(1, 3)
        for dx, dy in directions
    ]

    valid_targets = []
    for target in possible_targets:
        path = a_star(map_2d, goal, target)
        if path and 2 <= len(path) <= 5:
            valid_targets.append((target, path))

    if not valid_targets:
        return

    _, path = random.choice(valid_targets)
    await go_to_target(path)


async def create_path(mob_name: str, currentMap) -> list[tuple[int, int]] | None:
    player = Player()
    start_position = await player.position()
    start = (start_position[0], start_position[1])
    mob = await get_mobs_by_name(mob_name)
    mob_pos = mob.position
    if not mob_pos:
        return None

    goal = mob_pos[0]
    if start == goal:
        return None

    path = a_star(currentMap, start, goal)
    if path and len(path) != 1:
        return path
    return None


async def move_to_target(target_id, gateway, map_2d, start):
    map = Map()
    gateway_pos = await map.get_current_map_gateway_pos(gateway, int(target_id))
    goal = (gateway_pos[0], gateway_pos[1])
    path = a_star(map_2d, start, goal)
    current_map = await map.get_current_map_id()
    await follow_path(path, current_map)


async def follow_path(
    path,
    currentMap,
    should_abort: Optional[AbortCheck] = None,
) -> bool:
    if not path:
        return False

    map_obj = Map()
    player = Player()
    driver = await MyDriver().get_driver()

    def resend_script(x, y):
        return f"""() => window.Engine.hero.searchPath({{x: {x}, y: {y}}}, !1);"""

    target_x, target_y = path[-1]

    for x, y in path:
        if should_abort is not None and await should_abort():
            print("🔴 follow_path: przerwano ruch (should_abort=True) przed wysłaniem ścieżki")
            return False
        await driver.evaluate(resend_script(x, y), isolated_context=False)
        await asyncio.sleep(random.uniform(0.05, 0.1))

    last_position: tuple[int, int] | None = None
    stall_started_at: float | None = None
    started_at = asyncio.get_event_loop().time()
    loop = asyncio.get_event_loop()

    while True:
        await asyncio.sleep(random.uniform(0.54, 0.89))

        if should_abort is not None and await should_abort():
            print("🔴 follow_path: przerwano ruch (should_abort=True)")
            return False

        new_map = await map_obj.get_current_map_id()
        if new_map != currentMap:
            print("Map has changed.")
            await asyncio.sleep(random.uniform(0.47, 0.62))
            return True

        if loop.time() - started_at >= FOLLOW_PATH_MAX_WAIT_SECONDS:
            print(f"⚠️ follow_path: przekroczono {FOLLOW_PATH_MAX_WAIT_SECONDS}s bez zmiany mapy — przerywam.")
            return False

        current_pos = await player.position()
        checker = (current_pos[0], current_pos[1])

        now = loop.time()
        if checker != last_position:
            last_position = checker
            stall_started_at = now
        elif stall_started_at is not None and (now - stall_started_at) >= FOLLOW_PATH_STALL_TIMEOUT_SECONDS:
            print(f"⚠️ follow_path: brak ruchu przez {FOLLOW_PATH_STALL_TIMEOUT_SECONDS}s @ {checker} — ponawiam searchPath.")
            await driver.evaluate(resend_script(target_x, target_y), isolated_context=False)
            stall_started_at = now


async def go_to_gateway(goal) -> bool:
    map = Map()
    player = Player()
    start_position = await player.position()
    start = (start_position[0], start_position[1])
    map_2d = await current_location_map()
    current_map = await map.get_current_map_id()
    path = a_star(map_2d, start, goal)
    return await follow_path(path, current_map)


def bfs_path(graph, start: str, goal: str, blocked_edges: set[tuple[str, str]] | None = None):
    if start == goal:
        return [start]
    blocked = blocked_edges or set()
    q = deque([start])
    visited = {start: None}
    while q:
        u = q.popleft()
        for v in graph.get(u, []):
            if (u, v) in blocked:
                continue
            if v not in visited:
                visited[v] = u
                if v == goal:
                    path = [v]
                    cur = u
                    while cur is not None:
                        path.append(cur)
                        cur = visited[cur]
                    path.reverse()
                    return path
                q.append(v)
    return None


def bfs_distance(graph, start: str, goal: str) -> int:
    path = bfs_path(graph, start, goal)
    return len(path) - 1 if path else float("inf")
