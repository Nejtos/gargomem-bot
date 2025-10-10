import asyncio
from collections import deque
from typing import Optional
from bot.core.driver import MyDriver
from bot.game.interactions.attack import attack_mob
from bot.game.moving.moving import go_to_target
from bot.game.services.heroes.config import (
    APPROACH_RESP_RADIUS_TILES,
    DECISION_TIMEOUT_SECONDS,
    HERO_DISPLAY_NAME,
    HERO_NEAR_RADIUS_TILES,
    HERO_STRICT_SINGLE_PARENT,
    INF_BIG,
    REPLAN_LARGE,
    REPLAN_MEDIUM,
    REPLAN_SMALL,
    REPLAN_THRESHOLDS,
    RESTART_CYCLE_SIGNAL,
    SUB_ENTRY_LIMIT,
    WAIT_ON_CHOOSE_SECONDS,
    WORLD_JSON_PATH,
)
from bot.game.services.heroes.detection import (
    detect_hero_near_any_respawn_on_map,
    detect_hero_near_coordinate,
    engine_get_npc_by_id,
)
from bot.game.services.heroes.gateways import (
    collect_exit_positions_for_target,
    wait_for_gateways_ready,
)
from bot.game.services.heroes.grid_utils import (
    bfs_dist_and_parent,
    bfs_dist_cached,
    pick_a_star,
    unique_points,
)
from bot.game.services.heroes.region_helpers import (
    has_resp_here,
    is_region_map,
    region_hubs_for,
)
from bot.game.services.heroes.travel import (
    choose_nearest_by_path,
    travel_multi_step_between_maps,
)
from bot.game.services.heroes.tsp_utils import (
    bfs_multisource_dist,
    calculate_distance_matrix_mixed,
    optimize_tail_end,
    robust_route_indices_points,
    robust_route_indices_points_end_at,
)
from bot.game.services.heroes.utils import (
    get_hero_min_respawn_seconds,
    safe_current_position,
    safe_currentLocationMap,
)
from bot.game.services.heroes.world_graph import build_reverse_graph, load_world_graph
from bot.integrations.dsc_reaction_control import request_hero_decision_via_webhook
from bot.utils.helpers import get_npc_id
from bot.data.heroes_data import heroes_dict


def _replan_every_steps_by_size(total_pts: int) -> int:
    if total_pts <= REPLAN_THRESHOLDS[0]:
        return REPLAN_SMALL
    if total_pts <= REPLAN_THRESHOLDS[1]:
        return REPLAN_MEDIUM
    return REPLAN_LARGE


def parents_of(rev_graph: dict[str, set[str]], child: str) -> set[str]:
    return set(rev_graph.get(str(child), set()))


def parents_of_for_hero(
    rev_graph: dict[str, set[str]], child: str, hero: str
) -> set[str]:
    return parents_of(rev_graph, child) & hero_maps_set(hero)


def hero_maps_set(hero: str) -> set[str]:
    return {str(m) for m, pts in heroes_dict[hero]["maps"].items() if pts}


def build_dm_with_sink_finish_near_exit(grid, start, respawns, exit_positions):
    INF = float("inf")
    nodes = [start] + respawns
    n = len(nodes)
    N = n + 1  # sink as last
    S = n
    dm = [[INF] * N for _ in range(N)]
    astar = pick_a_star()

    # dystanse między węzłami
    for i in range(n):
        dm[i][i] = 0.0
        dist_i = bfs_dist_cached(grid, nodes[i])
        for j in range(n):
            if i == j:
                continue
            d = dist_i[int(nodes[j][0])][int(nodes[j][1])]
            if d == -1:
                path = astar(grid, nodes[i], nodes[j])
                dm[i][j] = float(len(path) - 1) if path else INF
            else:
                dm[i][j] = float(d)

    # sink – multi-source BFS od wszystkich wyjść
    dist_sink = bfs_multisource_dist(
        grid, [(int(x), int(y)) for (x, y) in (exit_positions or [])]
    )
    for i in range(n):
        ix, iy = int(nodes[i][0]), int(nodes[i][1])
        dd = (
            dist_sink[ix][iy]
            if dist_sink and 0 <= ix < len(dist_sink) and 0 <= iy < len(dist_sink[0])
            else -1
        )
        if dd == -1:
            bestd = INF
            for ex in exit_positions or []:
                path = astar(grid, nodes[i], ex)
                if path:
                    bestd = min(bestd, float(len(path) - 1))
            dm[i][S] = bestd
        else:
            dm[i][S] = float(dd)

    dm[S][S] = 0.0
    return dm, nodes, S


def _anchor_child_to_hub(
    hub_map_id: str, child_id: str, graph, rev_graph, max_depth: int = 6
) -> Optional[str]:
    hub = str(hub_map_id)
    child = str(child_id)
    if child in (graph.get(hub, set()) or set()):
        return child
    visited = {child}
    q = deque([(child, 0)])
    while q:
        node, d = q.popleft()
        if d > max_depth:
            break
        parents = rev_graph.get(node, set()) or set()
        for p in parents:
            if p in visited:
                continue
            if p in (graph.get(hub, set()) or set()):
                return p
            visited.add(p)
            q.append((p, d + 1))
    return None


async def list_region_hub_entries(
    hero: str,
    hub_map_id: str,
    child_ids: list[str],
    grid,
    start: tuple[int, int],
    exits_next: Optional[list[tuple[int, int]]],
    entry_limit: Optional[int] = None,
    graph=None,
    rev_graph=None,
) -> dict[tuple[int, int], str]:
    entry_to_child: dict[tuple[int, int], str] = {}
    limit = entry_limit if entry_limit is not None else SUB_ENTRY_LIMIT
    g = graph or load_world_graph(WORLD_JSON_PATH, directed=True)
    rg = rev_graph or build_reverse_graph(g)

    seen_anchors: set[str] = set()
    for ch in (str(x) for x in (child_ids or [])):
        anchor = ch
        tops = await _pick_top_entries_for_child(anchor, grid, start, exits_next, limit)
        if not tops:
            anc = _anchor_child_to_hub(str(hub_map_id), ch, g, rg, max_depth=6)
            if anc and anc not in seen_anchors:
                tops = await _pick_top_entries_for_child(
                    anc, grid, start, exits_next, limit
                )
                if tops:
                    anchor = anc
                else:
                    print(
                        f"[region-hub] {hub_map_id} -> {ch}: no entry and no anchor for the gate."
                    )
                    continue
            else:
                print(
                    f"[region-hub] {hub_map_id} -> {ch}: no gate found from the hub (might be a floor)."
                )
                continue
        if anchor in seen_anchors:
            continue
        seen_anchors.add(anchor)
        for e in tops or []:
            entry_to_child[(int(e[0]), int(e[1]))] = anchor
    return entry_to_child


async def compute_attached_children(
    hero: str, remaining: set[str], graph, rev_graph
) -> dict[str, set[str]]:
    attachments: dict[str, set[str]] = {}
    hset = hero_maps_set(hero)
    for ch in list(remaining):
        if not has_resp_here(hero, ch):
            continue
        pars = parents_of(rev_graph, ch)
        if not pars:
            continue
        hero_pars = pars & hset
        for parent in pars:
            if parent not in remaining:
                continue
            if hero_pars == {parent} or (
                not HERO_STRICT_SINGLE_PARENT and not hero_pars
            ):
                attachments.setdefault(parent, set()).add(ch)
                break
    return attachments


def reconstruct_path(parent, start, goal):
    sx, sy = start
    gx, gy = goal
    if (gx, gy) != (sx, sy) and parent[gx][gy] is None:
        return None
    path = [(gx, gy)]
    x, y = gx, gy
    while (x, y) != (sx, sy):
        x, y = parent[x][y]
        path.append((x, y))
    path.reverse()
    return path


def hero_region_maps_set(hero: str) -> set[str]:
    try:
        cfg = heroes_dict.get(hero) or {}
    except Exception:
        cfg = {}
    regs = cfg.get("region_maps") or cfg.get("regions") or []
    return {str(x) for x in regs}


def build_reachable_choice(grid, start, exits):
    dist = bfs_dist_cached(grid, start)
    reachable = [
        (ex, dist[int(ex[0])][int(ex[1])])
        for ex in exits
        if dist[int(ex[0])][int(ex[1])] != -1
    ]
    if reachable:
        return min(reachable, key=lambda t: t[1])[0]
    astar = pick_a_star()
    best, bestd = None, INF_BIG
    for e in exits:
        path = astar(grid, start, (int(e[0]), int(e[1])))
        if path:
            d = len(path) - 1
            if d < bestd:
                best, bestd = (int(e[0]), int(e[1])), d
    return best or exits[0]


def hero_avoid_region_nodes(hero: str) -> set[str]:
    # Unikamy wychodzenia do map regionowych podczas sprzątania huba
    return hero_region_maps_set(hero)


def build_approach_subpath(path, target, min_distance_tiles=APPROACH_RESP_RADIUS_TILES):
    if not path or len(path) == 1:
        return path
    tx, ty = int(target[0]), int(target[1])
    stop_idx = None
    for i in range(len(path) - 1, -1, -1):
        if abs(int(path[i][0]) - tx) + abs(int(path[i][1]) - ty) >= int(
            min_distance_tiles
        ):
            stop_idx = i
            break
    if stop_idx is None:
        return path[:2] if len(path) >= 2 else path
    return path[: stop_idx + 1]


async def pick_unique_entry_from_parent_to_child(
    child_map_id: str,
) -> Optional[tuple[int, int]]:
    exits = await collect_exit_positions_for_target(child_map_id)
    if len(exits) == 1:
        return exits[0]
    return None


async def select_entry_point_to_child(
    child_map_id: str, prefer_from: Optional[tuple[int, int]] = None
) -> Optional[tuple[int, int]]:
    exits = await collect_exit_positions_for_target(child_map_id)
    if not exits:
        return None
    if prefer_from:
        grid = await safe_currentLocationMap()
        dist = bfs_dist_cached(grid, (int(prefer_from[0]), int(prefer_from[1])))
        reachable = [
            (e, dist[int(e[0])][int(e[1])])
            for e in exits
            if dist[int(e[0])][int(e[1])] != -1
        ]
        if reachable:
            return min(reachable, key=lambda t: t[1])[0]
        best, bestd = None, INF_BIG
        astar = pick_a_star()
        for e in exits:
            path = astar(grid, prefer_from, (int(e[0]), int(e[1])))
            if path:
                d = len(path) - 1
                if d < bestd:
                    best, bestd = (int(e[0]), int(e[1])), d
        if best:
            return best
    return exits[0]


async def select_entry_point_to_child_smart(
    child_map_id: str,
    grid,
    start: tuple[int, int],
    exits_next: Optional[list[tuple[int, int]]],
) -> Optional[tuple[int, int]]:
    exits = await collect_exit_positions_for_target(child_map_id)
    if not exits:
        return None
    dist_start = bfs_dist_cached(grid, start)
    if not exits_next:
        reach = [
            (e, dist_start[int(e[0])][int(e[1])])
            for e in exits
            if dist_start[int(e[0])][int(e[1])] != -1
        ]
        if reach:
            return min(reach, key=lambda t: t[1])[0]
        astar = pick_a_star()
        best, bestd = None, INF_BIG
        for e in exits:
            path = astar(grid, start, (int(e[0]), int(e[1])))
            if path:
                d = len(path) - 1
                if d < bestd:
                    best, bestd = (int(e[0]), int(e[1])), d
        return best or exits[0]
    best, best_score = None, INF_BIG
    for e in exits:
        d0 = dist_start[int(e[0])][int(e[1])]
        if d0 == -1:
            continue
        dist_e = bfs_dist_cached(grid, (int(e[0]), int(e[1])))
        d_sink = min(
            (
                dist_e[int(sx)][int(sy)]
                for (sx, sy) in exits_next
                if dist_e[int(sx)][int(sy)] != -1
            ),
            default=INF_BIG,
        )
        if d_sink == INF_BIG:
            continue
        score = d0 + d_sink
        if score < best_score:
            best, best_score = (int(e[0]), int(e[1])), score
    if best:
        return best
    reach = [
        (e, dist_start[int(e[0])][int(e[1])])
        for e in exits
        if dist_start[int(e[0])][int(e[1])] != -1
    ]
    if reach:
        return min(reach, key=lambda t: t[1])[0]
    return exits[0]


async def _pick_top_entries_for_child(
    child_map_id: str,
    grid,
    start: tuple[int, int],
    exits_next: Optional[list[tuple[int, int]]],
    limit: Optional[int],
) -> list[tuple[int, int]]:
    exits = await collect_exit_positions_for_target(child_map_id)
    if not exits or not limit or limit <= 0:
        return exits or []
    dist_start = bfs_dist_cached(grid, start)
    astar = pick_a_star()

    def score_entry(e: tuple[int, int]) -> float:
        d0 = dist_start[int(e[0])][int(e[1])]
        if d0 == -1:
            path = astar(grid, start, (int(e[0]), int(e[1])))
            d0 = len(path) - 1 if path else INF_BIG
        if not exits_next:
            return float(d0)
        dist_e = bfs_dist_cached(grid, (int(e[0]), int(e[1])))
        d_sink = min(
            (
                dist_e[int(sx)][int(sy)]
                for (sx, sy) in exits_next
                if dist_e[int(sx)][int(sy)] != -1
            ),
            default=INF_BIG,
        )
        if d_sink == INF_BIG:
            bestd = INF_BIG
            for sx, sy in exits_next:
                path = astar(grid, (int(e[0]), int(e[1])), (int(sx), int(sy)))
                dd = len(path) - 1 if path else INF_BIG
                if dd < bestd:
                    bestd = dd
            d_sink = bestd
        return float(d0) + float(d_sink)

    ranked = sorted(exits, key=score_entry)
    good = [(int(e[0]), int(e[1])) for e in ranked[:limit]]
    if all(score_entry(e) >= INF_BIG for e in good):
        good = [(int(e[0]), int(e[1])) for e in exits[:limit]]
    return good


async def list_unique_entry_sublocations(
    hero: str,
    parent_map_id: str,
    graph,
    rev_graph,
    grid,
    start: tuple[int, int],
    exits_next: Optional[list[tuple[int, int]]],
    forced_children: Optional[set[str]] = None,
    include_anchors: bool = False,
):
    parent = str(parent_map_id)
    neighbors = [str(ch) for ch in graph.get(parent, [])]
    forced_children = {str(x) for x in (forced_children or set())}
    entry_to_child: dict[tuple[int, int], str] = {}

    # 1) Tylko bezpośrednie dzieci z respami (jak dla zwykłych map)
    for ch in neighbors:
        if not has_resp_here(hero, ch):
            continue

        hero_parents = parents_of_for_hero(rev_graph, ch, hero)
        all_parents = parents_of(rev_graph, ch)
        if parent not in all_parents and ch not in forced_children:
            continue

        attach_ok = False
        if ch in forced_children:
            attach_ok = True
        else:
            if hero_parents == {parent}:
                attach_ok = True
            elif (
                not HERO_STRICT_SINGLE_PARENT
                and not hero_parents
                and parent in all_parents
            ):
                attach_ok = True

        if not attach_ok:
            continue

        try:
            top_entries = await _pick_top_entries_for_child(
                ch, grid, start, exits_next, SUB_ENTRY_LIMIT
            )
            for e in top_entries or []:
                entry_to_child[(int(e[0]), int(e[1]))] = ch
        except Exception:
            continue

    # 2) Anchory (pośrednie wejścia bez respów) – tylko gdy jesteśmy w HUBIE
    if include_anchors:
        try:
            hero_map_set = hero_maps_set(hero)
            g = graph
            rg = rev_graph
            for deep in hero_map_set:
                if deep == parent:
                    continue
                anc = _anchor_child_to_hub(parent, deep, g, rg, max_depth=8)
                if (
                    anc
                    and anc in neighbors
                    and not is_region_map(hero, anc)
                    and anc not in entry_to_child.values()
                ):
                    try:
                        top_entries = await _pick_top_entries_for_child(
                            anc, grid, start, exits_next, SUB_ENTRY_LIMIT
                        )
                        if top_entries:
                            for e in top_entries or []:
                                entry_to_child[(int(e[0]), int(e[1]))] = str(anc)
                    except Exception:
                        continue
        except Exception:
            pass

    return entry_to_child


async def scan_single_leaf_sublocation(
    hero: str,
    parent_map_id: str,
    sub_map_id: str,
    heal_event,
    graph,
    rev_graph,
    remaining_set: Optional[set[str]] = None,
    scanned_maps: Optional[set[str]] = None,
):
    avoid_nodes = hero_avoid_region_nodes(hero) | {str(parent_map_id)}
    ok = await travel_multi_step_between_maps(
        str(parent_map_id), str(sub_map_id), graph, avoid_nodes=avoid_nodes
    )
    if not ok:
        return None
    res = await scan_map_respawns_to_exit(
        hero,
        str(sub_map_id),
        str(parent_map_id),
        heal_event,
        graph=graph,
        rev_graph=rev_graph,
        allow_single_leaf_sub=False,
        remaining_set=remaining_set,
        scanned_maps=scanned_maps,
        avoid_maps={str(parent_map_id)} | hero_avoid_region_nodes(hero),
        hub_context=True,
    )
    if isinstance(res, tuple) and res and res[0] == RESTART_CYCLE_SIGNAL:
        return res
    await travel_multi_step_between_maps(
        str(sub_map_id), str(parent_map_id), graph, avoid_nodes=avoid_nodes
    )
    if remaining_set is not None:
        remaining_set.discard(str(sub_map_id))
    if scanned_maps is not None:
        scanned_maps.add(str(sub_map_id))
    return None


async def scan_sublocation(
    hero: str,
    parent_map_id: str,
    child_map_id: str,
    heal_event,
    graph,
    rev_graph,
    remaining_set: Optional[set[str]] = None,
    scanned_maps: Optional[set[str]] = None,
    avoid_maps: Optional[set[str]] = None,
):
    avoid_ctx = (
        set(avoid_maps or set()) | hero_avoid_region_nodes(hero) | {str(parent_map_id)}
    )
    ok = await travel_multi_step_between_maps(
        str(parent_map_id), str(child_map_id), graph, avoid_nodes=avoid_ctx
    )
    if not ok:
        return None
    res = await scan_map_respawns_to_exit(
        hero,
        str(child_map_id),
        str(parent_map_id),
        heal_event,
        graph=graph,
        rev_graph=rev_graph,
        allow_single_leaf_sub=True,
        remaining_set=remaining_set,
        scanned_maps=scanned_maps,
        avoid_maps=avoid_ctx,
        hub_context=True,
    )
    if isinstance(res, tuple) and res and res[0] == RESTART_CYCLE_SIGNAL:
        return res
    await travel_multi_step_between_maps(
        str(child_map_id), str(parent_map_id), graph, avoid_nodes=avoid_ctx
    )
    if remaining_set is not None:
        remaining_set.discard(str(child_map_id))
    if scanned_maps is not None:
        scanned_maps.add(str(child_map_id))
    return None


async def scan_map_respawns_to_exit(
    hero: str,
    map_id: str,
    next_hop_map_id: str | None,
    heal_event,
    graph=None,
    rev_graph=None,
    allow_single_leaf_sub: bool = True,
    remaining_set: Optional[set[str]] = None,
    scanned_maps: Optional[set[str]] = None,
    forced_attach_children: Optional[set[str]] = None,
    avoid_maps: Optional[set[str]] = None,
    hub_context: bool = False,
) -> Optional[tuple]:
    await wait_for_gateways_ready(str(map_id))
    if graph is None:
        graph = load_world_graph(WORLD_JSON_PATH, directed=True)
    if rev_graph is None:
        rev_graph = build_reverse_graph(graph)

    grid = await safe_currentLocationMap()
    avoid = {str(x) for x in (avoid_maps or set())}

    region_mode = is_region_map(hero, str(map_id))
    region_hubs = region_hubs_for(hero, str(map_id), graph=graph, rev_graph=rev_graph)
    has_region_hub = region_mode and bool(region_hubs)

    if region_mode and not has_region_hub:
        # region bez hubów → pełne skanowanie (tylko resp’y na tej mapie)
        force_full_map_scan = True
        single_ok = False
        forced_children_eff = set()
    else:
        # region z hubami albo zwykła mapa → normalna logika
        force_full_map_scan = False
        single_ok = bool(allow_single_leaf_sub) and (
            (not region_mode) or has_region_hub
        )
        forced_children_eff = (
            set() if region_mode else (forced_attach_children or set())
        )

    # Dla regionu bez hubów: NIE dodajemy wyjścia (sink) do TSP
    # disable_sink_in_route = bool(region_mode and not has_region_hub)
    # Dla WSZYSTKICH regionów: NIE dodajemy wyjścia (sink) do TSP (finisz przy wyjściu robimy po trasie)
    disable_sink_in_route = bool(region_mode and not has_region_hub)

    # 1) szybka detekcja herosa
    found_near, npc_id, npc_pos, npc_name, mob_type = (
        await detect_hero_near_any_respawn_on_map(
            hero, str(map_id), HERO_NEAR_RADIUS_TILES, preloaded_grid=grid
        )
    )
    if found_near and npc_id:
        display = HERO_DISPLAY_NAME.get(hero, hero)
        decision = await request_hero_decision_via_webhook(
            display,
            str(map_id),
            npc_pos or (0, 0),
            timeout=DECISION_TIMEOUT_SECONDS,
            default_action="attack",
            wait_seconds=WAIT_ON_CHOOSE_SECONDS,
        )
        if decision == "logout":
            await MyDriver().close_driver()
            raise SystemExit("Logout requested via Discord")
        if decision == "attack":
            pos = await safe_current_position()
            if not pos:
                return None

            start = pos
            final_target = npc_pos

            if not final_target:
                info = await engine_get_npc_by_id(npc_id)
                if info and info.get("x") is not None and info.get("y") is not None:
                    final_target = (int(info["x"]), int(info["y"]))

            if not final_target:
                return None

            # Najpierw BFS -> jeśli nie wyjdzie, fallback A*
            dist2, parent2 = bfs_dist_and_parent(
                grid, start, targets={final_target}, early_stop=True
            )
            path2 = reconstruct_path(parent2, start, final_target)
            if not path2:
                path2 = (pick_a_star())(grid, start, final_target)

            if path2 and len(path2) < 2:
                path2 = [start, final_target]

            # Ostateczny fallback: podejdź na kratke przy herosie i dołóż finisz na tile herosa
            if not path2:
                rows, cols = len(grid), len(grid[0])
                gx, gy = final_target
                adj = [(gx + 1, gy), (gx - 1, gy), (gx, gy + 1), (gx, gy - 1)]
                adj = [
                    (x, y)
                    for (x, y) in adj
                    if 0 <= x < rows and 0 <= y < cols and grid[x][y] != "1"
                ]
                if adj:
                    best_adj = await choose_nearest_by_path(start, adj)
                    if best_adj:
                        p = (pick_a_star())(grid, start, best_adj)
                        if p:
                            path2 = p + [final_target]

            if not path2:
                return None

            if mob_type is None:
                _id2, mob_type = await get_npc_id((final_target,))
            mob_name = display

            result = await go_to_target(path2, npc_id)
            if result:
                await attack_mob(
                    npc_id, mob_name, heroes=True, heal_event=heal_event
                )
            await asyncio.sleep(5)
            min_wait = get_hero_min_respawn_seconds(hero)
            return (RESTART_CYCLE_SIGNAL, min_wait)
        if decision == "wait":
            await asyncio.sleep(WAIT_ON_CHOOSE_SECONDS)

    # 2) sink
    exits_next = None
    if next_hop_map_id:
        cand = await collect_exit_positions_for_target(next_hop_map_id)
        exits_next = cand if cand else None
    # WAŻNE: region bez hubów – trasa tylko po respach (bez sinka)
    if disable_sink_in_route:
        exits_next = None

    # 3) punkty do odwiedzenia
    respawns_raw = list(heroes_dict[hero]["maps"].get(str(map_id), []))

    pos = await safe_current_position()
    if not pos:
        return None
    start = pos

    # normalna logika – respawny + sublokacje
    sub_entries: dict[tuple[int, int], str] = {}
    if force_full_map_scan:
        # pełne skanowanie tej mapy (tylko respawny, bez sub_entries, bez next hop)
        points = unique_points(respawns_raw)
    else:
        # normalna logika – respawny + sublokacje
        entries_set = set(sub_entries.keys())
        points = unique_points(respawns_raw + list(entries_set))
    if single_ok:
        if has_region_hub:
            sub_entries = await list_region_hub_entries(
                hero,
                str(map_id),
                region_hubs,
                grid,
                start,
                exits_next,
                entry_limit=SUB_ENTRY_LIMIT,
                graph=graph,
                rev_graph=rev_graph,
            )
        else:
            sub_entries = await list_unique_entry_sublocations(
                hero,
                str(map_id),
                graph,
                rev_graph,
                grid,
                start,
                exits_next,
                forced_children=forced_children_eff,
                include_anchors=hub_context,
            )

        if scanned_maps is not None:
            sub_entries = {
                e: ch for e, ch in sub_entries.items() if str(ch) not in scanned_maps
            }
        if next_hop_map_id is not None:
            nh = str(next_hop_map_id)
            sub_entries = {e: ch for e, ch in sub_entries.items() if ch != nh}
        if avoid:
            sub_entries = {e: ch for e, ch in sub_entries.items() if ch not in avoid}

    entries_set = set(sub_entries.keys())
    points = unique_points(respawns_raw + list(entries_set))

    if not points:
        if next_hop_map_id:
            await wait_for_gateways_ready(str(map_id), expect_next=str(next_hop_map_id))
            exits = await collect_exit_positions_for_target(next_hop_map_id)
            if exits:
                grid = await safe_currentLocationMap()
                pos = await safe_current_position()
                if not pos:
                    return None
                sx, sy = pos
                ex = build_reachable_choice(grid, (sx, sy), exits)
                path = (pick_a_star())(grid, (int(sx), int(sy)), ex)
                if path:
                    await go_to_target(path, mobType="heroes")
        return None

    async def build_route_from(start_pos: tuple[int, int], pts: list[tuple[int, int]]):
        grid_local = await safe_currentLocationMap()
        if exits_next:
            dm, nodes, S = build_dm_with_sink_finish_near_exit(
                grid_local, start_pos, pts, exits_next
            )
            order = robust_route_indices_points_end_at(dm, S, hk_threshold=18)
            if order:
                # lokalny tuning (ostatnie węzły przed sinkiem)
                order = optimize_tail_end(order, dm, S, tail_k=4)
                return [nodes[i] for i in order if i not in (0, S)]
            pts2 = [start_pos] + pts
            dm2 = calculate_distance_matrix_mixed(grid_local, pts2)
            order2 = robust_route_indices_points(dm2, hk_threshold=18)
            return [pts2[i] for i in order2][1:]
        else:
            pts2 = [start_pos] + pts
            dm2 = calculate_distance_matrix_mixed(grid_local, pts2)
            order = robust_route_indices_points(dm2, hk_threshold=18)
            return [pts2[i] for i in order][1:]

    # 4) realizacja
    points_remaining: set[tuple[int, int]] = set(points)
    visited_children: set[str] = set()

    total_pts = len(points_remaining)
    REPLAN_EVERY_STEPS = _replan_every_steps_by_size(total_pts)
    # huby replanuj po każdym punkcie
    if has_region_hub:
        REPLAN_EVERY_STEPS = 1

    route_cache: list[tuple[int, int]] = []
    replan_left = 0

    route_generation = 0
    precompute_task: Optional[asyncio.Task] = None
    precompute_gen: Optional[int] = None

    while points_remaining:
        grid_now = await safe_currentLocationMap()
        pos = await safe_current_position()
        if not pos:
            await asyncio.sleep(0.1)
            continue
        current_pos = pos
        points_remaining.discard(current_pos)

        if single_ok and (not route_cache or replan_left <= 0):
            if has_region_hub:
                new_sub = await list_region_hub_entries(
                    hero,
                    str(map_id),
                    region_hubs,
                    grid_now,
                    current_pos,
                    exits_next,
                    entry_limit=SUB_ENTRY_LIMIT,
                    graph=graph,
                    rev_graph=rev_graph,
                )
            else:
                new_sub = await list_unique_entry_sublocations(
                    hero,
                    str(map_id),
                    graph,
                    rev_graph,
                    grid_now,
                    current_pos,
                    exits_next,
                    forced_children=forced_children_eff,
                    include_anchors=hub_context,
                )
            if scanned_maps is not None:
                new_sub = {
                    e: ch for e, ch in new_sub.items() if str(ch) not in scanned_maps
                }
            new_sub = {e: ch for e, ch in new_sub.items() if ch not in visited_children}
            if next_hop_map_id is not None:
                nh = str(next_hop_map_id)
                new_sub = {e: ch for e, ch in new_sub.items() if ch != nh}
            if avoid:
                new_sub = {e: ch for e, ch in new_sub.items() if ch not in avoid}

        if single_ok:
            for e, ch in list(sub_entries.items()):
                if (scanned_maps and ch in scanned_maps) or (ch in visited_children):
                    points_remaining.discard(e)
                    sub_entries.pop(e, None)
            for e, ch in new_sub.items() if single_ok else []:
                sub_entries[e] = ch
                points_remaining.add(e)

        if not route_cache or replan_left <= 0:
            route_cache = await build_route_from(current_pos, list(points_remaining))
            replan_left = REPLAN_EVERY_STEPS
            route_generation += 1
            precompute_task = None
            precompute_gen = None

        if not route_cache:
            break

        target = route_cache.pop(0)
        if target not in points_remaining:
            replan_left = 0
            continue

        if target in sub_entries:
            child_id = sub_entries[target]
            res = await scan_sublocation(
                hero,
                str(map_id),
                child_id,
                heal_event,
                graph,
                rev_graph,
                remaining_set=remaining_set,
                scanned_maps=scanned_maps,
                avoid_maps=(avoid | {str(map_id)}),
            )
            if isinstance(res, tuple) and res and res[0] == RESTART_CYCLE_SIGNAL:
                return res
            visited_children.add(child_id)
            for e, ch in list(sub_entries.items()):
                if ch == child_id:
                    points_remaining.discard(e)
                    sub_entries.pop(e, None)
            points_remaining.discard(target)
            route_cache = []
            replan_left = 0
            precompute_task = None
            precompute_gen = None
            await asyncio.sleep(0)
            continue

        if precompute_task is None:
            pts_after = list(points_remaining - {target})
            this_gen = route_generation

            async def _precompute(start_pos, pts):
                return await build_route_from(start_pos, pts)

            precompute_task = asyncio.create_task(_precompute(target, pts_after))
            precompute_gen = this_gen

        grid_now = await safe_currentLocationMap()
        pos = await safe_current_position()
        if not pos:
            await asyncio.sleep(0.1)
            continue
        current_pos = pos
        path = (pick_a_star())(grid_now, current_pos, target)
        if path:
            subpath = build_approach_subpath(path, target, APPROACH_RESP_RADIUS_TILES)
            if len(subpath) >= 2:
                await go_to_target(subpath, mobType="heroes")

        if (
            precompute_task
            and precompute_task.done()
            and precompute_gen == route_generation
        ):
            try:
                next_route = precompute_task.result()
                if isinstance(next_route, list) and next_route:
                    route_cache = [p for p in next_route if p in points_remaining]
            except Exception:
                pass
            finally:
                precompute_task = None
            precompute_gen = None

        grid_now = await safe_currentLocationMap()
        ok, npc_id, npc_pos, npc_name, mob_type = await detect_hero_near_coordinate(
            hero, target, HERO_NEAR_RADIUS_TILES, preloaded_grid=grid_now
        )
        if ok and npc_id:
            display = HERO_DISPLAY_NAME.get(hero, hero)
            decision = await request_hero_decision_via_webhook(
                display,
                str(map_id),
                npc_pos or target,
                timeout=DECISION_TIMEOUT_SECONDS,
                default_action="attack",
                wait_seconds=WAIT_ON_CHOOSE_SECONDS,
            )
            if decision == "logout":
                await MyDriver().close_driver()
                raise SystemExit("Logout requested via Discord")
            if decision == "attack":
                pos = await safe_current_position()
                if not pos:
                    return None
                cx, cy = pos
                start = (cx, cy)

                # BIERZEMY TYLKO DOKŁADNE KORDY HEROSA
                final_target = npc_pos

                if not final_target:
                    info = await engine_get_npc_by_id(npc_id)
                    if info and info.get("x") is not None and info.get("y") is not None:
                        final_target = (int(info["x"]), int(info["y"]))

                if not final_target:
                    continue

                # Najpierw BFS, potem fallback A*
                dist2, parent2 = bfs_dist_and_parent(
                    grid_now, start, targets={final_target}, early_stop=True
                )
                path2 = reconstruct_path(parent2, start, final_target)
                if not path2:
                    path2 = (pick_a_star())(grid_now, start, final_target)

                # Zapewnij min. 2 punkty (moveHeroAndFightWithHeroes używa path[-2])
                if path2 and len(path2) < 2:
                    path2 = [start, final_target]

                # Ostateczny fallback: podejdź na kratkę obok herosa i dołóż finisz na tile herosa
                if not path2:
                    rows, cols = len(grid_now), len(grid_now[0])
                    gx, gy = final_target
                    adj = [(gx + 1, gy), (gx - 1, gy), (gx, gy + 1), (gx, gy - 1)]
                    adj = [
                        (x, y)
                        for (x, y) in adj
                        if 0 <= x < rows and 0 <= y < cols and grid_now[x][y] != "1"
                    ]
                    if adj:
                        best_adj = await choose_nearest_by_path(start, adj)
                        if best_adj:
                            p = (pick_a_star())(grid_now, start, best_adj)
                            if p:
                                path2 = p + [final_target]

                if not path2:
                    continue

                if mob_type is None:
                    _id2, mob_type = await get_npc_id((final_target,))
                mob_name = display

                result = await go_to_target(path2, npc_id)
                if result:
                    await attack_mob(
                        npc_id, mob_name, heroes=True, heal_event=heal_event
                    )
                await asyncio.sleep(5)
                min_wait = get_hero_min_respawn_seconds(hero)
                return (RESTART_CYCLE_SIGNAL, min_wait)
            if decision == "wait":
                await asyncio.sleep(WAIT_ON_CHOOSE_SECONDS)

        points_remaining.discard(target)
        route_cache = [p for p in route_cache if p in points_remaining]
        replan_left -= 1
        await asyncio.sleep(0)

    # 5) fallback forced
    if forced_attach_children_eff := forced_children_eff:
        for ch in (str(x) for x in forced_attach_children_eff):
            if ch in visited_children:
                continue
            res = await scan_sublocation(
                hero,
                str(map_id),
                ch,
                heal_event,
                graph=graph,
                rev_graph=rev_graph,
                remaining_set=remaining_set,
                scanned_maps=scanned_maps,
            )
            if isinstance(res, tuple) and res and res[0] == RESTART_CYCLE_SIGNAL:
                return res

    # 6) podejście pod bramkę next_hop
    if next_hop_map_id:
        await wait_for_gateways_ready(str(map_id), expect_next=str(next_hop_map_id))
        exits = await collect_exit_positions_for_target(next_hop_map_id)
        if exits:
            grid = await safe_currentLocationMap()
            pos = await safe_current_position()
            if not pos:
                return None
            sx, sy = pos
            ex = build_reachable_choice(grid, (sx, sy), exits)
            path = (pick_a_star())(grid, (int(sx), int(sy)), ex)
            if path:
                await go_to_target(path, mobType="heroes")
    return None
