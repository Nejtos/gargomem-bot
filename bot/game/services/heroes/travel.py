import asyncio
import random
from typing import Optional
from bot.game.moving.moving import go_to_target
from bot.game.navigation.helpers import get_current_map
from bot.game.services.heroes.config import INF_BIG
from bot.game.services.heroes.gateways import (
    collect_exit_positions_for_target,
    wait_for_gateways_ready,
    wait_for_map_switch,
)
from bot.game.services.heroes.grid_utils import (
    _grid_is_valid,
    bfs_dist_cached,
    pick_a_star,
)
from bot.game.services.heroes.utils import (
    safe_current_position,
    safe_currentLocationMap,
)
from bot.game.services.heroes.world_graph import bfs_path, bfs_path_avoid_nodes


async def wait_for_map_render_ready(
    target_map_id: Optional[str] = None, timeout: float = 6.0, poll: float = 0.15
) -> bool:
    start_t = asyncio.get_event_loop().time()
    while True:
        try:
            cur = str(await get_current_map())
            if target_map_id is None or str(target_map_id) == cur:
                grid = await safe_currentLocationMap(max_retries=1, delay=poll)
                if _grid_is_valid(grid):
                    return True
        except Exception:
            pass
        if asyncio.get_event_loop().time() - start_t > timeout:
            return False
        await asyncio.sleep(poll)


async def choose_nearest_by_path(
    start: tuple[int, int], candidates: list[tuple[int, int]]
):
    if not candidates:
        return None
    grid = await safe_currentLocationMap()
    dist = bfs_dist_cached(grid, start)
    best, bestd = None, INF_BIG
    for x, y in candidates:
        d = dist[int(x)][int(y)]
        if d != -1 and d < bestd:
            best, bestd = (int(x), int(y)), d
    if best is not None:
        return best
    astar = pick_a_star()
    for x, y in candidates:
        path = astar(grid, start, (int(x), int(y)))
        if path:
            d = len(path) - 1
            if d < bestd:
                best, bestd = (int(x), int(y)), d
    return best


async def travel_one_step(cur_map: str, nxt_map: str) -> bool:
    cur_map = str(cur_map)
    nxt_map = str(nxt_map)
    on_cur = str(await get_current_map()) == cur_map
    if not on_cur:
        await wait_for_gateways_ready(str(await get_current_map()))
    else:
        await wait_for_gateways_ready(cur_map, expect_next=nxt_map)

    exits = await collect_exit_positions_for_target(nxt_map)
    if not exits:
        return False

    astar = pick_a_star()
    exits_left = list(exits)
    while exits_left:
        pos = await safe_current_position()
        if not pos:
            return False
        sx, sy = pos
        grid = await safe_currentLocationMap()
        ex = await choose_nearest_by_path((sx, sy), exits_left)
        if not ex:
            break
        path = astar(grid, (sx, sy), ex)
        if not path:
            exits_left.remove(ex)
            continue
        try:
            await go_to_target(path, mobType="heroes")
        except Exception:
            exits_left.remove(ex)
            continue
        switched = await wait_for_map_switch(cur_map, nxt_map, timeout=30.0)
        if switched:
            await wait_for_gateways_ready(nxt_map)
            await wait_for_map_render_ready(nxt_map, timeout=6.0, poll=0.15)
            await asyncio.sleep(random.uniform(0.25, 0.45))
            return True
        exits_left.remove(ex)
        await asyncio.sleep(0.2)
    return False


async def travel_multi_step_between_maps(
    start_map: str,
    target_map: str,
    graph,
    avoid_nodes: Optional[set[str]] = None,
    blocked_edges: Optional[set[tuple[str, str]]] = None,
) -> bool:
    start_map = str(start_map)
    target_map = str(target_map)
    if start_map == target_map:
        return True
    path = bfs_path_avoid_nodes(
        graph, start_map, target_map, blocked_edges, avoid_nodes=avoid_nodes
    ) or bfs_path(graph, start_map, target_map, blocked_edges)
    if not path or len(path) < 2:
        return False
    for u, v in zip(path, path[1:]):
        ok = await travel_one_step(u, v)
        if not ok:
            return False
    return True
