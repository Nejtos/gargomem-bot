import asyncio
import time
import random
from bot.core.driver import MyDriver
from bot.game.moving.pathfiding import a_star
from bot.game.navigation.helpers import (
    get_current_map,
    get_gateway_pos,
    update_collisions,
    map_size,
)
from bot.game.navigation.maps_dict import (
    build_tree,
    find_element,
    traverse_to_leaf,
    traverse_to_root,
    display_tree,
    maps_dict,
)
from bot.utils.helpers import current_position
import bot.globals as globals


async def follow_path(path, currentMap):
    driver = await MyDriver().get_driver()
    for x, y in path:
        script = f"""() => window.Engine.hero.searchPath({{x: {x}, y: {y}}}, !1);"""
        await driver.evaluate(script, isolated_context=False)

    while True:
        await asyncio.sleep(random.uniform(0.54, 0.89))
        new_map = await get_current_map()
        if new_map != currentMap:
            print("Map has changed.")
            break
    await asyncio.sleep(random.uniform(0.47, 0.62))


async def current_location_map():
    map_str = await update_collisions()
    max_map_size = await map_size()
    max_w = max_map_size[0]
    map_2d = [
        list(map_str[i : i + max_w + 1]) for i in range(0, len(map_str), max_w + 1)
    ]
    map_2d = [list(column) for column in zip(*map_2d)]
    return map_2d


async def move_to_target(target_id, gateway, map_2d, start):
    gateway_pos = await get_gateway_pos(gateway, int(target_id))
    goal = (gateway_pos[0], gateway_pos[1])
    path = a_star(map_2d, start, goal)
    current_map = await get_current_map()
    await follow_path(path, current_map)


async def navigate_tree(selected_exp, current_map, gateway, map_2d, start):
    driver = await MyDriver().get_driver()

    if selected_exp in maps_dict and maps_dict[selected_exp] is not None:
        root_node = build_tree(maps_dict[selected_exp])
        display_tree(root_node)
        target_value = str(current_map)
        node_to_start_from = find_element(root_node, target_value)

        if (
            str(current_map) == str(root_node.value)
            or globals.direction[0] == "bottom"
            or (globals.direction[0] == "" and node_to_start_from and node_to_start_from.children)
        ):
            print("Last visited node: " + str(globals.last_visited_node[0]))
            path_to_leaf = traverse_to_leaf(node_to_start_from, [])
            if str(current_map) == str(root_node.value) and globals.last_visited_node[0] != "":
                if globals.last_visited_node[0] not in globals.last_visited_arr[0]:
                    globals.last_visited_arr[0].append(globals.last_visited_node[0])
                path_to_leaf = traverse_to_leaf(node_to_start_from, globals.last_visited_arr[0])
            if len(globals.last_visited_arr[0]) == 3 and str(current_map) == str(root_node.value):
                tmp = globals.last_visited_arr[0].pop(0)
                path_to_leaf = traverse_to_leaf(node_to_start_from, globals.last_visited_arr[0])
                globals.last_visited_arr[0].append(tmp)
            if len(root_node.children) == 1:
                path_to_leaf = traverse_to_leaf(node_to_start_from, [])
            print("Arr: " + str(globals.last_visited_arr[0]))
            print("Path to leaf: " + str(path_to_leaf))

            if path_to_leaf is not None:
                if len(path_to_leaf) > 0:
                    holder = int(path_to_leaf[0])
                    gateway_pos = await get_gateway_pos(gateway, holder)
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
                        new_map = await get_current_map()
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
                gateway_pos = await get_gateway_pos(gateway, holder)
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
                    new_map = await get_current_map()
                    if new_map != current_map:
                        print("Map has changed.")
                        break
                await asyncio.sleep(random.uniform(0.46, 0.62))


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


async def go_to_gateway(goal):
    start_position = await current_position()
    start = (start_position[0], start_position[1])
    map_2d = await current_location_map()
    current_map = await get_current_map()
    path = a_star(map_2d, start, goal)
    await follow_path(path, current_map)
