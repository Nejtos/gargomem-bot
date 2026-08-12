import asyncio
import heapq
import random
from bot.game.entities.map import Map
from bot.game.services.helpers import retry

class Node:
    def __init__(self, row, col, cost=0, heuristic=0, parent=None):
        self.row = row
        self.col = col
        self.cost = cost
        self.heuristic = heuristic
        self.parent = parent

    def __lt__(self, other):
        return (self.cost + self.heuristic) < (other.cost + other.heuristic)


def heuristic(node, goal):
    return abs(node.row - goal[0]) + abs(node.col - goal[1])


def a_star(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    visited = [[False for _ in range(cols)] for _ in range(rows)]
    priority_queue = [
        Node(start[0], start[1], 0, heuristic(Node(start[0], start[1]), goal))
    ]

    while priority_queue:
        current_node = heapq.heappop(priority_queue)
        if current_node.row == goal[0] and current_node.col == goal[1]:
            path = [(current_node.row, current_node.col)]
            while current_node.row != start[0] or current_node.col != start[1]:
                current_node = current_node.parent
                path.insert(0, (current_node.row, current_node.col))
            return path
        # if (
        #     abs(current_node.row - goal[0]) <= 1
        #     and abs(current_node.col - goal[1]) <= 1
        # ):
        #     path = [(current_node.row, current_node.col)]
        #     while current_node.row != start[0] or current_node.col != start[1]:
        #         current_node = current_node.parent
        #         path.insert(0, (current_node.row, current_node.col))
        #     return path

        visited[current_node.row][current_node.col] = True
        neighbors = [
            (current_node.row + 1, current_node.col),
            (current_node.row, current_node.col + 1),
            (current_node.row - 1, current_node.col),
            (current_node.row, current_node.col - 1),
        ]

        for row, col in neighbors:
            if (
                0 <= row < rows
                and 0 <= col < cols
                and not visited[row][col]
                and (grid[row][col] != "1" or (row == goal[0] and col == goal[1]))
            ):
                neighbor_node = Node(
                    row,
                    col,
                    current_node.cost + 1,
                    heuristic(Node(row, col), goal),
                    current_node,
                )
                heapq.heappush(priority_queue, neighbor_node)
                visited[row][col] = True
    return None

def _ring_offsets(radius: int):
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if max(abs(dx), abs(dy)) == radius:
                yield dx, dy


def find_path_to_or_near(map_2d, start, goal, max_radius: int = 3):
    """
    Próbuje dojść dokładnie do `goal`. Jeśli cel jest nieprzechodni
    (głaz, drzewo, obiekt questowy na którym nie da się stanąć),
    szuka najbliższego przechodniego pola w promieniu `max_radius`
    wokół celu i liczy ścieżkę do niego.
    """
    path = a_star(map_2d, start, goal)
    if path:
        return path

    gx, gy = goal
    for radius in range(1, max_radius + 1):
        candidates = [(gx + dx, gy + dy) for dx, dy in _ring_offsets(radius)]
        candidates.sort(key=lambda c: (c[0] - start[0]) ** 2 + (c[1] - start[1]) ** 2)
        for cand in candidates:
            candidate_path = a_star(map_2d, start, cand)
            if candidate_path:
                return candidate_path

    return None


@retry(max_attempts=10, delay=3, refresh=False)
async def current_location_map():
    map_obj = Map()
    map_collisions = await map_obj.get_current_map_collisions()
    map_size = await map_obj.get_current_map_size()

    map_w = map_size[0]
    map_2d = [
        list(map_collisions[i : i + map_w + 1])
        for i in range(0, len(map_collisions), map_w + 1)
    ]
    map_2d = [list(column) for column in zip(*map_2d)]
    return map_2d

async def wait_for_map_change(self, current_map: int) -> None:
    while True:
        await asyncio.sleep(random.uniform(0.94, 1.29))
        new_map = await self.get_current_map_id()
        if new_map != current_map:
            print("Map has changed.")
            break
