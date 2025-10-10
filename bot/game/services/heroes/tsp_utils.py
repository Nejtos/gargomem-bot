from collections import deque
import itertools
from bot.game.services.heroes.grid_utils import bfs_dist_cached, pick_a_star


def held_karp_shortest_path(dm: list[list[float]]) -> list[int] | None:
    n = len(dm)
    if n == 0:
        return []
    INF = float("inf")
    dp = [[(INF, -1)] * n for _ in range(1 << n)]
    dp[1][0] = (0.0, -1)
    for mask in range(1 << n):
        if not (mask & 1):
            continue
        for j in range(n):
            if not (mask & (1 << j)):
                continue
            cost_j, _ = dp[mask][j]
            if cost_j == INF:
                continue
            for k in range(n):
                if mask & (1 << k):
                    continue
                w = dm[j][k]
                if w == INF:
                    continue
                new_mask = mask | (1 << k)
                new_cost = cost_j + w
                if new_cost < dp[new_mask][k][0]:
                    dp[new_mask][k] = (new_cost, j)
    full = (1 << n) - 1
    best_cost, best_end = float("inf"), -1
    for j in range(n):
        c, _ = dp[full][j]
        if c < best_cost:
            best_cost, best_end = c, j
    if best_end == -1 or best_cost == float("inf"):
        return None
    order = []
    mask, j = full, best_end
    while j != -1:
        order.append(j)
        _, pj = dp[mask][j]
        mask &= ~(1 << j)
        j = pj
    order.reverse()
    return order


def held_karp_short_path_end(dm: list[list[float]], end_idx: int) -> list[int] | None:
    n = len(dm)
    if n == 0:
        return []
    INF = float("inf")
    dp = [[(INF, -1)] * n for _ in range(1 << n)]
    dp[1][0] = (0.0, -1)
    for mask in range(1 << n):
        if not (mask & 1):
            continue
        for j in range(n):
            if not (mask & (1 << j)):
                continue
            cost_j, _ = dp[mask][j]
            if cost_j == INF:
                continue
            for k in range(n):
                if mask & (1 << k):
                    continue
                w = dm[j][k]
                if w == INF:
                    continue
                new_mask = mask | (1 << k)
                new_cost = cost_j + w
                if new_cost < dp[new_mask][k][0]:
                    dp[new_mask][k] = (new_cost, j)
    full = (1 << n) - 1
    best_cost, best_end = dp[full][end_idx][0], end_idx
    if best_end == -1 or best_cost == float("inf"):
        return None
    order = []
    mask, j = full, best_end
    while j != -1:
        order.append(j)
        _, pj = dp[mask][j]
        mask &= ~(1 << j)
        j = pj
    order.reverse()
    return order


def two_opt(route, distance_matrix):
    if not route:
        return route
    best_route = route[:]

    def route_cost(r):
        return sum(distance_matrix[r[i]][r[i + 1]] for i in range(len(r) - 1))

    best_cost = route_cost(best_route)
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best_route) - 2):
            for j in range(i + 1, len(best_route) - 1):
                if j - i == 1:
                    continue
                new_route = best_route[:i] + best_route[i:j][::-1] + best_route[j:]
                new_cost = route_cost(new_route)
                if new_cost < best_cost:
                    best_route, best_cost, improved = new_route, new_cost, True
                    break
            if improved:
                break
    return best_route


def two_opt_end(route, distance_matrix, sink_idx):
    if not route:
        return route
    n = len(route)
    end = n - 1

    def route_cost(r):
        return sum(distance_matrix[r[i]][r[i + 1]] for i in range(n - 1))

    best_route = route[:]
    best_cost = route_cost(best_route)
    improved = True
    while improved:
        improved = False
        for i in range(1, end - 1):
            for j in range(i + 1, end):
                if j - i == 1:
                    continue
                new_route = best_route[:i] + best_route[i:j][::-1] + best_route[j:]
                new_cost = sum(
                    distance_matrix[new_route[k]][new_route[k + 1]]
                    for k in range(n - 1)
                )
                if new_cost < best_cost:
                    best_route, best_cost, improved = new_route, new_cost, True
                    break
            if improved:
                break
    return best_route


def nearest_neighbor(distance_matrix):
    n = len(distance_matrix)
    if n == 0:
        return []
    visited = [False] * n
    order = [0]
    visited[0] = True
    for _ in range(n - 1):
        last = order[-1]
        best, bestd = None, float("inf")
        for j in range(n):
            if not visited[j] and distance_matrix[last][j] < bestd:
                best, bestd = j, distance_matrix[last][j]
        if best is None:
            best = next((j for j in range(n) if not visited[j]), None)
            if best is None:
                break
        order.append(best)
        visited[best] = True
    return order


def robust_route_indices_points(distance_matrix, hk_threshold: int = 16):
    n = len(distance_matrix)
    if n <= 1:
        return [0] if n == 1 else []
    try:
        if n <= hk_threshold:
            order = held_karp_shortest_path(distance_matrix)
            if order:
                return order
    except Exception:
        pass
    try:
        order = nearest_neighbor(distance_matrix)
        order = two_opt(order, distance_matrix)
        if order and order[0] == 0:
            return order
    except Exception:
        pass
    return list(range(n))


def robust_route_indices_points_end_at(
    distance_matrix, sink_idx: int, hk_threshold: int = 16
):
    n = len(distance_matrix)
    if n == 0:
        return []
    try:
        if n <= hk_threshold:
            order = held_karp_short_path_end(distance_matrix, sink_idx)
            if order:
                return order
    except Exception:
        pass
    start = 0
    unvisited = set(range(n))
    unvisited.discard(start)
    unvisited.discard(sink_idx)
    route = [start]
    cur = start
    while unvisited:
        best, bestd = None, float("inf")
        for j in unvisited:
            d = distance_matrix[cur][j]
            if d < bestd:
                best, bestd = j, d
        if best is None:
            best = unvisited.pop()
            route.append(best)
        else:
            route.append(best)
            unvisited.remove(best)
            cur = best
    route.append(sink_idx)
    route = two_opt_end(route, distance_matrix, sink_idx)
    return route


def calculate_distance_matrix_mixed(grid, points):
    n = len(points)
    INF = float("inf")
    dm = [[INF] * n for _ in range(n)]
    for i in range(n):
        dm[i][i] = 0.0
    astar = pick_a_star()
    for i in range(n):
        dist_i = bfs_dist_cached(grid, points[i])
        for j in range(i + 1, n):
            d = dist_i[int(points[j][0])][int(points[j][1])]
            if d == -1:
                path = astar(grid, points[i], points[j])
                dd = float(len(path) - 1) if path else INF
            else:
                dd = float(d)
            dm[i][j] = dd
            dm[j][i] = dd
    return dm


def bfs_multisource_dist(grid, sources: list[tuple[int, int]]) -> list[list[int]]:
    rows, cols = len(grid), len(grid[0])
    dist = [[-1] * cols for _ in range(rows)]
    q = deque()

    def passable(x, y):
        return 0 <= x < rows and 0 <= y < cols and grid[x][y] != "1"

    for sx, sy in sources or []:
        sx, sy = int(sx), int(sy)
        if 0 <= sx < rows and 0 <= sy < cols:
            dist[sx][sy] = 0
            q.append((sx, sy))
    while q:
        x, y = q.popleft()
        nd = dist[x][y] + 1
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if passable(nx, ny) and dist[nx][ny] == -1:
                dist[nx][ny] = nd
                q.append((nx, ny))
    return dist


def _route_cost_end(order, dm):
    if not order or len(order) < 2:
        return 0.0
    return sum(dm[order[i]][order[i + 1]] for i in range(len(order) - 1))


def optimize_tail_end(order, dm, sink_idx, tail_k: int = 4):
    # bruteforce permutacje ostatnich K węzłów przed sinkiem
    if not order or len(order) < 4:
        return order
    n = len(order)
    tail_start = max(1, n - 1 - max(2, min(tail_k, n - 2)))
    head = order[:tail_start]
    tail = order[tail_start : n - 1]
    end = order[-1]
    best_order = order[:]
    best_cost = _route_cost_end(order, dm)
    limit = min(len(tail), tail_k)
    for perm in itertools.permutations(tail, r=len(tail)):
        cand = head + list(perm) + [end]
        cost = _route_cost_end(cand, dm)
        if cost < best_cost:
            best_cost = cost
            best_order = cand
    return best_order
