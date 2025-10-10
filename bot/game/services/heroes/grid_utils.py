from collections import deque
import heapq

from bot.game.moving.pathfiding import a_star
from bot.game.services.heroes.cache import _BFS_DIST_CACHE
from bot.game.services.heroes.config import BFS_DIST_CACHE_MAX, USE_LOCAL_ASTAR


class Node:
    def __init__(self, row, col, cost=0, heuristic=0, parent=None):
        self.row = row
        self.col = col
        self.cost = cost
        self.heuristic = heuristic
        self.parent = parent

    def __lt__(self, other):
        return (self.cost + self.heuristic) < (other.cost + other.heuristic)


def a_star_fast(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    sx, sy = int(start[0]), int(start[1])
    gx, gy = int(goal[0]), int(goal[1])

    def passable(x, y):
        return (
            0 <= x < rows
            and 0 <= y < cols
            and (grid[x][y] != "1" or (x == gx and y == gy))
        )

    INF = 10**9
    g = [[INF] * cols for _ in range(rows)]
    parent = [[None] * cols for _ in range(rows)]
    g[sx][sy] = 0

    def h(x, y):
        return abs(x - gx) + abs(y - gy)

    pq = [(h(sx, sy), 0, sx, sy)]
    closed = [[False] * cols for _ in range(rows)]
    while pq:
        f, cost, x, y = heapq.heappop(pq)
        if closed[x][y]:
            continue
        closed[x][y] = True
        if x == gx and y == gy:
            path = [(x, y)]
            while (x, y) != (sx, sy):
                x, y = parent[x][y]
                path.append((x, y))
            path.reverse()
            return path
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if not passable(nx, ny) or closed[nx][ny]:
                continue
            ng = cost + 1
            if ng < g[nx][ny]:
                g[nx][ny] = ng
                parent[nx][ny] = (x, y)
                heapq.heappush(pq, (ng + h(nx, ny), ng, nx, ny))
    return None


def unique_points(points):
    seen = set()
    out = []
    for p in points:
        t = (int(p[0]), int(p[1]))
        if t not in seen:
            out.append(t)
            seen.add(t)
    return out


def manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(int(a[0]) - int(b[0])) + abs(int(a[1]) - int(b[1]))


def _grid_is_valid(grid) -> bool:
    if not isinstance(grid, list) or not grid:
        return False
    if not isinstance(grid[0], list) or not grid[0]:
        return False
    w = len(grid[0])
    return all(isinstance(r, list) and len(r) == w for r in grid)


def grid_fingerprint(grid) -> tuple:
    try:
        rows, cols = len(grid), len(grid[0])

        def cell(x, y):
            try:
                return str(grid[x][y])
            except Exception:
                return "#"

        samples_pos = {
            (0, 0),
            (rows - 1, cols - 1),
            (rows // 2, cols // 2),
            (rows // 3, cols // 3),
            (rows - 1, 0),
        }
        samples = tuple(
            cell(x, y) for (x, y) in samples_pos if 0 <= x < rows and 0 <= y < cols
        )
        return ("v1", rows, cols, samples)
    except Exception:
        return ("v1", 0, 0, ())


def pick_a_star():
    return a_star_fast if USE_LOCAL_ASTAR else a_star


def bfs_dist_and_parent(grid, start, targets=None, early_stop=True):
    rows, cols = len(grid), len(grid[0])
    sx, sy = int(start[0]), int(start[1])
    dist = [[-1] * cols for _ in range(rows)]
    parent = [[None] * cols for _ in range(rows)]
    q = deque([(sx, sy)])
    dist[sx][sy] = 0
    remain = set(targets) if targets else None

    def passable(x, y):
        return 0 <= x < rows and 0 <= y < cols and grid[x][y] != "1"

    while q:
        x, y = q.popleft()
        if remain is not None and (x, y) in remain:
            remain.remove((x, y))
            if early_stop and not remain:
                break
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if passable(nx, ny) and dist[nx][ny] == -1:
                dist[nx][ny] = dist[x][y] + 1
                parent[nx][ny] = (x, y)
                q.append((nx, ny))
    return dist, parent


def bfs_dist_cached(grid, start: tuple[int, int]) -> list[list[int]]:
    fp = grid_fingerprint(grid)
    sx, sy = int(start[0]), int(start[1])
    key = (fp, sx, sy)
    if key in _BFS_DIST_CACHE:
        _BFS_DIST_CACHE.move_to_end(key)
        return _BFS_DIST_CACHE[key]
    dist, _ = bfs_dist_and_parent(grid, (sx, sy), targets=None, early_stop=False)
    _BFS_DIST_CACHE[key] = dist
    if len(_BFS_DIST_CACHE) > BFS_DIST_CACHE_MAX:
        _BFS_DIST_CACHE.popitem(last=False)
    return dist
