import asyncio
from typing import Optional
from datetime import datetime, timedelta
from bot.game.navigation.helpers import get_current_map
from bot.game.services.heroes.config import RESTART_CYCLE_SIGNAL, WORLD_JSON_PATH
from bot.game.services.heroes.interface import heroes_reload_game_and_prepare
from bot.game.services.heroes.region_helpers import (
    has_resp_here,
    is_region_map,
    region_hubs_for,
)
from bot.game.services.heroes.scanning import (
    compute_attached_children,
    parents_of_for_hero,
    scan_map_respawns_to_exit,
)
from bot.game.services.heroes.travel import travel_one_step
from bot.game.services.heroes.utils import (
    get_hero_min_respawn_seconds,
    random_empty_cycle_wait_seconds,
)
from bot.game.services.heroes.world_graph import (
    bfs_path,
    bfs_path_avoid_nodes,
    build_reverse_graph,
    compute_map_route,
    load_world_graph,
)
from bot.data.heroes_data import heroes_dict


async def heroes_service(selected_heroes: str, heal_event):
    hero = selected_heroes
    graph = load_world_graph(WORLD_JSON_PATH, directed=True)
    rev_graph = build_reverse_graph(graph)

    if not any(pts for pts in heroes_dict[hero]["maps"].values()):
        print(f"[heroes] No respawns for {hero}")
        return

    while True:
        remaining: set[str] = {
            str(m) for m, pts in heroes_dict[hero]["maps"].items() if pts
        }
        blocked_edges: set[tuple[str, str]] = set()
        scanned_maps: set[str] = set()
        print(f"[heroes] New cycle: {hero}, maps to scan: {len(remaining)}")

        cycle_should_restart = False
        pending_wait_seconds: Optional[int] = None

        def _allow_sub_for(mid: str) -> bool:
            return not is_region_map(hero, str(mid))

        while remaining:
            if scanned_maps:
                remaining.difference_update(scanned_maps)
            if not remaining:
                break

            cur = str(await get_current_map())

            attachments_by_parent = await compute_attached_children(
                hero, remaining, graph, rev_graph
            )
            attachments_by_parent = {
                p: s
                for p, s in attachments_by_parent.items()
                if not is_region_map(hero, p)
            }

            attached_children = set()
            for s in attachments_by_parent.values():
                attached_children.update(s)

            if cur in attached_children:
                attached_children.remove(cur)
            if attached_children:
                remaining.difference_update(attached_children)

            route_maps = compute_map_route(graph, cur, remaining, blocked_edges)
            if not route_maps or route_maps[0] != cur:
                route_maps = [cur] + [m for m in route_maps if m != cur]

            # jeśli jedyna mapa to ta, na której stoimy
            if len(remaining) == 1 and cur in remaining and cur not in scanned_maps:
                allow_sub = True if is_region_map(hero, cur) else _allow_sub_for(cur)
                res = await scan_map_respawns_to_exit(
                    hero,
                    cur,
                    None,
                    heal_event,
                    graph=graph,
                    rev_graph=rev_graph,
                    allow_single_leaf_sub=allow_sub,
                    remaining_set=remaining,
                    scanned_maps=scanned_maps,
                    forced_attach_children=(
                        attachments_by_parent.get(cur, set())
                        if _allow_sub_for(cur)
                        else set()
                    ),
                )
                scanned_maps.add(cur)
                if isinstance(res, tuple) and res and res[0] == RESTART_CYCLE_SIGNAL:
                    cycle_should_restart = True
                    pending_wait_seconds = (
                        int(res[1])
                        if len(res) > 1
                        else get_hero_min_respawn_seconds(hero)
                    )
                    break
                remaining.discard(cur)
                continue

            for planned in route_maps[1:]:
                if not remaining:
                    break
                if planned not in remaining or planned in scanned_maps:
                    continue

                while True:
                    cur_now = str(await get_current_map())

                    if cur_now in remaining and cur_now not in scanned_maps:
                        avoid = set(scanned_maps)
                        avoid.discard(cur_now)
                        avoid.discard(planned)
                        p2 = bfs_path_avoid_nodes(
                            graph, cur_now, planned, blocked_edges, avoid_nodes=avoid
                        ) or bfs_path(graph, cur_now, planned, blocked_edges)
                        next_hop_for_scan = p2[1] if p2 and len(p2) >= 2 else None
                        allow_sub = (
                            True
                            if is_region_map(hero, cur_now)
                            else _allow_sub_for(cur_now)
                        )
                        res = await scan_map_respawns_to_exit(
                            hero,
                            cur_now,
                            next_hop_for_scan,
                            heal_event,
                            graph=graph,
                            rev_graph=rev_graph,
                            allow_single_leaf_sub=allow_sub,
                            remaining_set=remaining,
                            scanned_maps=scanned_maps,
                            forced_attach_children=(
                                attachments_by_parent.get(cur_now, set())
                                if _allow_sub_for(cur_now)
                                else set()
                            ),
                        )
                        scanned_maps.add(cur_now)
                        if (
                            isinstance(res, tuple)
                            and res
                            and res[0] == RESTART_CYCLE_SIGNAL
                        ):
                            cycle_should_restart = True
                            pending_wait_seconds = (
                                int(res[1])
                                if len(res) > 1
                                else get_hero_min_respawn_seconds(hero)
                            )
                            break
                        remaining.discard(cur_now)
                        break

                    # Hub regionu bez własnych respów (też skanuj)
                    # Region – jeśli ma HUBY (z heroes_data['region_hubs']), skanuj jak “mapę z hubami”
                    if cur_now not in scanned_maps and is_region_map(hero, cur_now):
                        hubs = region_hubs_for(
                            hero, cur_now, graph=graph, rev_graph=rev_graph
                        )
                        if hubs:
                            avoid = set(scanned_maps)
                            avoid.discard(cur_now)
                            avoid.discard(planned)
                            p2 = bfs_path_avoid_nodes(
                                graph,
                                cur_now,
                                planned,
                                blocked_edges,
                                avoid_nodes=avoid,
                            ) or bfs_path(graph, cur_now, planned, blocked_edges)
                            next_hop_for_scan = p2[1] if p2 and len(p2) >= 2 else None
                            res = await scan_map_respawns_to_exit(
                                hero,
                                cur_now,
                                next_hop_for_scan,
                                heal_event,
                                graph=graph,
                                rev_graph=rev_graph,
                                allow_single_leaf_sub=True,
                                remaining_set=remaining,
                                scanned_maps=scanned_maps,
                                forced_attach_children=set(),
                            )
                            scanned_maps.add(cur_now)
                            if (
                                isinstance(res, tuple)
                                and res
                                and res[0] == RESTART_CYCLE_SIGNAL
                            ):
                                cycle_should_restart = True
                                pending_wait_seconds = (
                                    int(res[1])
                                    if len(res) > 1
                                    else get_hero_min_respawn_seconds(hero)
                                )
                                break
                            break

                    elif cur_now not in scanned_maps and has_resp_here(hero, cur_now):
                        avoid = set(scanned_maps)
                        avoid.discard(cur_now)
                        avoid.discard(planned)
                        p2 = bfs_path_avoid_nodes(
                            graph, cur_now, planned, blocked_edges, avoid_nodes=avoid
                        ) or bfs_path(graph, cur_now, planned, blocked_edges)
                        next_hop_for_scan = p2[1] if p2 and len(p2) >= 2 else None
                        allow_sub = (
                            True
                            if is_region_map(hero, cur_now)
                            else _allow_sub_for(cur_now)
                        )
                        res = await scan_map_respawns_to_exit(
                            hero,
                            cur_now,
                            next_hop_for_scan,
                            heal_event,
                            graph=graph,
                            rev_graph=rev_graph,
                            allow_single_leaf_sub=allow_sub,
                            remaining_set=remaining,
                            scanned_maps=scanned_maps,
                            forced_attach_children=(
                                attachments_by_parent.get(cur_now, set())
                                if _allow_sub_for(cur_now)
                                else set()
                            ),
                        )
                        scanned_maps.add(cur_now)
                        if (
                            isinstance(res, tuple)
                            and res
                            and res[0] == RESTART_CYCLE_SIGNAL
                        ):
                            cycle_should_restart = True
                            pending_wait_seconds = (
                                int(res[1])
                                if len(res) > 1
                                else get_hero_min_respawn_seconds(hero)
                            )
                            break
                        remaining.discard(cur_now)
                        break

                    elif cur_now not in scanned_maps:
                        has_children = any(
                            (parents_of_for_hero(rev_graph, ch, hero) == {cur_now})
                            and has_resp_here(hero, ch)
                            for ch in graph.get(cur_now, [])
                        )
                        if has_children:
                            avoid = set(scanned_maps)
                            avoid.discard(cur_now)
                            avoid.discard(planned)
                            p2 = bfs_path_avoid_nodes(
                                graph,
                                cur_now,
                                planned,
                                blocked_edges,
                                avoid_nodes=avoid,
                            ) or bfs_path(graph, cur_now, planned, blocked_edges)
                            next_hop_for_scan = p2[1] if p2 and len(p2) >= 2 else None
                            allow_sub = (
                                True
                                if is_region_map(hero, cur_now)
                                else _allow_sub_for(cur_now)
                            )
                            res = await scan_map_respawns_to_exit(
                                hero,
                                cur_now,
                                next_hop_for_scan,
                                heal_event,
                                graph=graph,
                                rev_graph=rev_graph,
                                allow_single_leaf_sub=allow_sub,
                                remaining_set=remaining,
                                scanned_maps=scanned_maps,
                                forced_attach_children=set(),
                            )
                            scanned_maps.add(cur_now)
                            if (
                                isinstance(res, tuple)
                                and res
                                and res[0] == RESTART_CYCLE_SIGNAL
                            ):
                                cycle_should_restart = True
                                pending_wait_seconds = (
                                    int(res[1])
                                    if len(res) > 1
                                    else get_hero_min_respawn_seconds(hero)
                                )
                                break

                    if cycle_should_restart or not remaining:
                        break
                    if planned not in remaining or planned in scanned_maps:
                        break

                    avoid = set(scanned_maps)
                    avoid.discard(cur_now)
                    avoid.discard(planned)
                    p = bfs_path_avoid_nodes(
                        graph, cur_now, planned, blocked_edges, avoid_nodes=avoid
                    ) or bfs_path(graph, cur_now, planned, blocked_edges)
                    if not p or len(p) < 2:
                        print(
                            f"[heroes] No path to {planned} (blocked={len(blocked_edges)}) – skipping."
                        )
                        remaining.discard(planned)
                        break

                    prev, nxt = p[0], p[1]
                    ok = await travel_one_step(prev, nxt)
                    if not ok:
                        blocked_edges.add((prev, nxt))
                        print(f"[heroes] Blocked edge {prev} -> {nxt}.")
                        p_alt = bfs_path(graph, cur_now, planned, blocked_edges)
                        if not p_alt:
                            print(
                                f"[heroes] No alternate route to {planned}. Skipping."
                            )
                            remaining.discard(planned)
                            break
                        await asyncio.sleep(0.05)
                        continue
                    await asyncio.sleep(0.05)

                if cycle_should_restart or not remaining:
                    break
                break

            if cycle_should_restart:
                break

        if pending_wait_seconds is not None:
            wait_s = pending_wait_seconds
            next_login_time = datetime.now() + timedelta(seconds=wait_s)
            tstr = next_login_time.strftime("%H:%M:%S")
            print(f"[heroes] Hero killed. Next login ~{tstr}.")
            await heroes_reload_game_and_prepare(next_login_time, hero)
        else:
            wait_s = random_empty_cycle_wait_seconds()
            next_login_time = datetime.now() + timedelta(seconds=wait_s)
            tstr = next_login_time.strftime("%H:%M:%S")
            print(
                f"[heroes] Cycle finished empty. Logout for {wait_s//60} min. Next login ~{tstr}."
            )
            await heroes_reload_game_and_prepare(next_login_time, hero)

        print(f"[heroes] Resuming searches: new cycle for {hero}")
