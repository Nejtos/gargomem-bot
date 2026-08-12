import asyncio
from collections import defaultdict
import json
import random

from bot.core.driver import MyDriver
from bot.game.entities.map import Map
from bot.game.entities.player import Player
from bot.game.services.heroes.world_graph import load_world_graph
from bot.game.services.merchant_service import find_nearest_service_npc
from bot.game.services.move_service import a_star, bfs_path, go_to_gateway, go_to_target
from bot.game.services.map_services import current_location_map
from bot.data.map_order_data import maps_dict

GRAPH = load_world_graph("bot/data/world_maps.json")

import bot.globals as globals


class Tree:
    def __init__(self, value):
        self.value = value
        self.children = []


def build_tree(data):
    if not data:
        return None

    root = Tree(data[0])

    for child_data in data[1:]:
        if isinstance(child_data, list):
            child_tree = build_tree(child_data)
            root.children.append(child_tree)
        else:
            root.children.append(Tree(child_data))

    return root


def find_element(node, target_value):
    if node:
        if node.value == target_value:
            return node

        for child in node.children:
            result = find_element(child, target_value)
            if result:
                return result

    return None


def traverse_to_leaf(node, arr):
    if node:
        path = [node.value]

        last_child = None

        current_node = node
        while current_node.children:
            children = [
                child
                for child in current_node.children
                if child != last_child and child.value not in arr
            ]
            if not children:
                break

            last_child = random.choice(children)
            current_node = last_child
            path.append(current_node.value)

        if path == [node.value]:
            return None

        del path[0]
        return path


def display_tree(root, level=0, prefix="Root: "):
    if root:
        print(" " * (level * 4) + prefix + str(root.value))
        for child in root.children:
            display_tree(child, level + 1, "L--- ")


def traverse_to_root(tree, target_value):
    def _find_path(node, target, current_path):
        if not node:
            return None

        current_path.append(node.value)

        if node.value == target:
            return current_path

        for child in node.children:
            result = _find_path(child, target, current_path.copy())
            if result:
                return result

        return None

    return _find_path(tree, target_value, [])


def traverse_tree(node, path=None):
    if path is None:
        path = []

    if globals.all_paths[0] is None:
        globals.all_paths[0] = []

    path.append(node.value)

    if not node.children:
        current_path = path.copy()
        if current_path not in globals.all_paths[0]:
            globals.all_paths[0].append(current_path)

    for child in node.children:
        traverse_tree(child, path=path.copy(), all_paths=globals.all_paths[0])

    return globals.all_paths[0]


def flatten_maps(tree):
    result = []
    if not tree:
        return result
    first = tree[0]
    if isinstance(first, str):
        result.append(first)
    for sub in tree[1:]:
        result.extend(flatten_maps(sub))
    return result


async def navigate_to_service_npc(hero_lvl, current_map, npc_type, GRAPH):
    target_service_npc = await find_nearest_service_npc(
        hero_lvl, current_map, npc_type, GRAPH
    )
    if not target_service_npc:
        return

    target_service_npc_map_id = str(target_service_npc["npc_location_id"])

    if current_map != target_service_npc_map_id:
        arrived = await travel_to_target_map(current_map, [target_service_npc_map_id])
        if not arrived:
            print(
                f"⚠️ navigate_to_service_npc: nie udało się dotrzeć na mapę {target_service_npc_map_id}"
            )
            return None

    goal = tuple(target_service_npc["npc_coords"])
    reached = await reach_position_on_current_map(goal)
    if not reached:
        return None

    return target_service_npc


async def navigate_tree(selected_exp, current_map, gateway, map_2d, start):
    driver = await MyDriver().get_driver()
    map = Map()

    if selected_exp in maps_dict and maps_dict[selected_exp] is not None:
        root_node = build_tree(maps_dict[selected_exp])
        display_tree(root_node)
        target_value = str(current_map)
        node_to_start_from = find_element(root_node, target_value)

        if (
            str(current_map) == str(root_node.value)
            or globals.direction[0] == "bottom"
            or (
                globals.direction[0] == ""
                and node_to_start_from
                and node_to_start_from.children
            )
        ):
            print("Last visited node: " + str(globals.last_visited_node[0]))
            path_to_leaf = traverse_to_leaf(node_to_start_from, [])
            if (
                str(current_map) == str(root_node.value)
                and globals.last_visited_node[0] != ""
            ):
                if globals.last_visited_node[0] not in globals.last_visited_arr[0]:
                    globals.last_visited_arr[0].append(globals.last_visited_node[0])
                path_to_leaf = traverse_to_leaf(
                    node_to_start_from, globals.last_visited_arr[0]
                )
            if len(globals.last_visited_arr[0]) == 3 and str(current_map) == str(
                root_node.value
            ):
                tmp = globals.last_visited_arr[0].pop(0)
                path_to_leaf = traverse_to_leaf(
                    node_to_start_from, globals.last_visited_arr[0]
                )
                globals.last_visited_arr[0].append(tmp)
            if len(root_node.children) == 1:
                path_to_leaf = traverse_to_leaf(node_to_start_from, [])
            print("Arr: " + str(globals.last_visited_arr[0]))
            print("Path to leaf: " + str(path_to_leaf))

            if path_to_leaf is not None:
                if len(path_to_leaf) > 0:
                    holder = int(path_to_leaf[0])
                    gateway_pos = await map.get_current_map_gateway_pos(gateway, holder)
                    # gateway_pos = await get_gateway_pos(gateway, holder)
                    print("Gateway position: " + str(gateway_pos))
                    goal = (gateway_pos[0], gateway_pos[1])
                    result = a_star(map_2d, start, goal)
                    path = result
                    await asyncio.sleep(random.uniform(0.71, 0.9))
                    globals.direction[0] = "bottom"

                    for i in path:
                        resultX, resultY = i
                        script = f"""
                                () => window.Engine.hero.searchPath({{
                                    x: {resultX},
                                    y: {resultY}
                                }}, !1);
                            """
                        await driver.evaluate(script, isolated_context=False)

                    while True:
                        await asyncio.sleep(random.uniform(0.44, 0.49))
                        new_map = await map.get_current_map_id()
                        # new_map = await get_current_map()
                        if new_map != current_map:
                            print("Map has changed.")
                            break
                    await asyncio.sleep(random.uniform(0.47, 0.62))

        if (
            globals.direction[0] == "top"
            or (node_to_start_from and not node_to_start_from.children)
            or (globals.direction[0] == "" and not node_to_start_from.children)
        ):
            globals.last_visited_node[0] = str(current_map)
            path_to_root = traverse_to_root(root_node, str(current_map))
            if path_to_root and len(path_to_root) > 1:
                holder = path_to_root[-2]
                print(path_to_root)
                gateway_pos = await map.get_current_map_gateway_pos(gateway, holder)
                # gateway_pos = await get_gateway_pos(gateway, holder)
                print("Gateway position: " + str(gateway_pos))
                goal = (gateway_pos[0], gateway_pos[1])
                result = a_star(map_2d, start, goal)
                path = result
                await asyncio.sleep(random.uniform(0.65, 0.86))
                globals.direction[0] = "top"

                for i in path:
                    resultX, resultY = i
                    script = f"""
                            () => window.Engine.hero.searchPath({{
                                x: {resultX},
                                y: {resultY}
                            }}, !1);
                        """
                    await driver.evaluate(script, isolated_context=False)

                while True:
                    await asyncio.sleep(random.uniform(0.43, 0.49))
                    new_map = await map.get_current_map_id()
                    # new_map = await get_current_map()
                    if new_map != current_map:
                        print("Map has changed.")
                        break
                await asyncio.sleep(random.uniform(0.46, 0.62))


async def travel_to_target_map(curr_map: str, target_maps: list[str], ui=None) -> bool:
    map_entity = Map()
    blocked_edges: set[tuple[str, str]] = set()

    if curr_map in target_maps:
        return True

    max_replans = 20
    replans = 0

    while replans < max_replans:
        replans += 1

        best_path = None
        for target in target_maps:
            p = bfs_path(GRAPH, curr_map, target, blocked_edges)
            if p and (best_path is None or len(p) < len(best_path)):
                best_path = p

        if not best_path or len(best_path) < 2:
            print(f"⚠️ travel_to_target_map: brak trasy z {curr_map} do {target_maps}")
            return False

        next_map = best_path[1]

        moved = await _reach_gateway_to_map(map_entity, next_map)
        if not moved:
            print(
                f"⚠️ travel_to_target_map: nie udało się dotrzeć do {next_map} (nawet przez znane cykle), blokuję krawędź {curr_map} -> {next_map} i przeliczam trasę."
            )
            blocked_edges.add((curr_map, next_map))
            continue

        new_map = str(await map_entity.get_current_map_id())
        curr_map = new_map
        if curr_map in target_maps:
            return True

    print("⚠️ travel_to_target_map: przekroczono limit przeliczeń trasy.")
    return False


async def change_exp_map(
    selected_exp,
    curr_map,
    gateways,
    map_2d,
    start,
):
    await navigate_tree(
        selected_exp,
        curr_map,
        gateways,
        map_2d,
        start,
    )


async def is_in_proximity_via_path(path, threshold=3):
    return len(path) <= threshold


async def _get_gateway_pos_with_retry(map_entity, target_map_id, retries=5, delay=0.3):
    for _ in range(retries):
        gateways = await map_entity.get_current_map_gateways()
        gw_loc = await map_entity.get_current_map_gateway_pos(gateways, target_map_id)
        if gw_loc:
            return gw_loc
        await asyncio.sleep(delay)
    return None


async def _pick_reachable_gateway_pos(
    map_entity,
    target_map_id: str,
    retries: int = 5,
    delay: float = 0.3,
) -> tuple[int, int] | None:
    """
    Zwraca najbliższą (wg a_star) bramkę prowadzącą do target_map_id, spośród
    WSZYSTKICH bramek na bieżącej mapie prowadzących tam (może być ich kilka).
    Bierze pod uwagę tylko te faktycznie osiągalne z obecnej pozycji.
    """
    player = Player()

    for _ in range(retries):
        gateways = await map_entity.get_current_map_gateways()
        flat = await map_entity.get_current_map_gateway_pos(gateways, target_map_id)

        if flat and len(flat) >= 2:
            pairs = [(flat[i], flat[i + 1]) for i in range(0, len(flat) - 1, 2)]

            map_2d = await current_location_map()
            pos = await player.position()
            start = (pos[0], pos[1])

            reachable: list[tuple[tuple[int, int], int]] = []
            for gx, gy in pairs:
                path = a_star(map_2d, start, (gx, gy))
                if path:
                    reachable.append(((gx, gy), len(path)))

            if reachable:
                reachable.sort(key=lambda t: t[1])
                return reachable[0][0]

            return None

        await asyncio.sleep(delay)

    return None


def find_cycles_back_to_start(
    graph: dict[str, set[str]],
    start_map_id: str,
    max_depth: int = 6,
) -> list[list[str]]:
    """
    Znajduje cykle start_map_id -> ... -> start_map_id w grafie, o długości
    (liczbie kroków) od 2 do max_depth. W przeciwieństwie do prostego DFS,
    dopuszcza ponowne odwiedzenie tej samej mapy pośredniej w ramach jednego
    cyklu (np. 1 -> 15 -> 16 -> 15 -> 1, gdy trzeba wejść głębiej w jaskinię
    i wrócić, zanim bramka powrotna stanie się osiągalna). Odrzuca mapy typu
    "ślepy zaułek" (łączą się wyłącznie ze start_map_id) jako pośrednie kroki,
    bo wejście/wyjście z nich nie przybliża do celu. Wynik posortowany od
    najkrótszego cyklu.
    """

    def is_dead_end(node: str) -> bool:
        neighbors = graph.get(node, set())
        return neighbors <= {start_map_id}

    cycles: list[list[str]] = []
    seen_cycle_signatures: set[tuple[str, ...]] = set()

    def dfs(current: str, path: list[str], depth: int, last: str | None):
        if depth >= max_depth:
            return
        for neighbor in graph.get(current, []):
            if neighbor == last:
                # nie cofaj się natychmiast tam skąd przyszliśmy (unikamy trywialnego drgania)
                continue
            if neighbor == start_map_id and depth >= 1:
                candidate = tuple(path + [neighbor])
                if candidate not in seen_cycle_signatures:
                    seen_cycle_signatures.add(candidate)
                    cycles.append(list(candidate))
                continue
            if neighbor != start_map_id and is_dead_end(neighbor):
                continue
            dfs(neighbor, path + [neighbor], depth + 1, current)

    dfs(start_map_id, [start_map_id], 0, None)
    cycles.sort(key=len)
    return cycles


async def reach_position_on_current_map(
    goal: tuple[int, int],
    max_depth: int = 6,
) -> bool:
    map_entity = Map()
    player = Player()
    start_map_id = str(await map_entity.get_current_map_id())

    async def try_direct() -> bool:
        map_2d = await current_location_map()
        pos = await player.position()
        start = (pos[0], pos[1])
        path = a_star(map_2d, start, goal)
        if path and len(path) > 1:
            await go_to_target(path, mobType="quest")
            return True
        return False

    if await try_direct():
        return True

    known_cycles = find_cycles_back_to_start(GRAPH, start_map_id, max_depth)
    if not known_cycles:
        print(
            f"⚠️ reach_position_on_current_map: brak znanego cyklu z powrotem na {start_map_id}"
        )
        return False

    for cycle in known_cycles:
        steps = cycle[1:]
        cycle_succeeded = True

        for step_map in steps:
            gw_loc = await _pick_reachable_gateway_pos(map_entity, step_map)
            if not gw_loc:
                print(
                    f"⚠️ reach_position_on_current_map: brak osiągalnej bramki do {step_map} w cyklu {cycle}, przerywam ten cykl."
                )
                cycle_succeeded = False
                break

            moved = await go_to_gateway(gw_loc)
            if not moved:
                print(
                    f"⚠️ reach_position_on_current_map: nie udało się fizycznie dotrzeć do {step_map}, przerywam ten cykl {cycle}."
                )
                cycle_succeeded = False
                break

            actual_map = str(await map_entity.get_current_map_id())
            if actual_map != step_map:
                print(
                    f"⚠️ reach_position_on_current_map: po ruchu jesteśmy na {actual_map}, oczekiwano {step_map} — przerywam cykl {cycle}."
                )
                cycle_succeeded = False
                break

        if not cycle_succeeded:
            current_after_fail = str(await map_entity.get_current_map_id())
            if current_after_fail != start_map_id:
                print(
                    f"⚠️ reach_position_on_current_map: wracam z {current_after_fail} na {start_map_id} przed kolejną próbą."
                )
                await travel_to_target_map(current_after_fail, [start_map_id])
            continue

        if await try_direct():
            return True

    print(
        f"⚠️ reach_position_on_current_map: nie udało się dotrzeć do {goal} na mapie {start_map_id}"
    )
    return False


async def _reach_gateway_to_map(
    map_entity,
    target_map_id: str,
    max_depth: int = 6,
) -> bool:
    """
    Próbuje dojść i przejść przez bramkę prowadzącą z BIEŻĄCEJ mapy do
    target_map_id. Jeśli żadna bramka nie jest bezpośrednio osiągalna
    (kolizje odcinają dostęp), próbuje znanych cykli NA BIEŻĄCEJ mapie
    (np. przez jaskinię w obie strony), żeby zmienić pozycję, i wtedy
    ponawia próbę. Zwraca True jeśli po wywołaniu jesteśmy już
    na target_map_id.
    """
    start_map_id = str(await map_entity.get_current_map_id())

    async def try_gateway_directly() -> bool:
        gw_loc = await _pick_reachable_gateway_pos(map_entity, target_map_id)
        if not gw_loc:
            return False
        moved = await go_to_gateway(gw_loc)
        if not moved:
            return False
        actual_map = str(await map_entity.get_current_map_id())
        return actual_map == target_map_id

    if await try_gateway_directly():
        return True

    known_cycles = find_cycles_back_to_start(GRAPH, start_map_id, max_depth)
    if not known_cycles:
        return False

    for cycle in known_cycles:
        steps = cycle[1:]
        cycle_succeeded = True

        for step_map in steps:
            gw_loc = await _pick_reachable_gateway_pos(map_entity, step_map)
            if not gw_loc:
                cycle_succeeded = False
                break

            moved = await go_to_gateway(gw_loc)
            if not moved:
                cycle_succeeded = False
                break

            actual_map = str(await map_entity.get_current_map_id())
            if actual_map != step_map:
                cycle_succeeded = False
                break

        if not cycle_succeeded:
            current_after_fail = str(await map_entity.get_current_map_id())
            if current_after_fail != start_map_id:
                await travel_to_target_map(current_after_fail, [start_map_id])
            continue

        if await try_gateway_directly():
            return True

    return False
