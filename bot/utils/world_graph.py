import json
from collections import deque, defaultdict


def load_world_graph(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = defaultdict(set)
    for loc in data:
        a = str(loc["location_id"])
        for b in loc.get("gateways", {}).keys():
            b = str(b)
            graph[a].add(b)
            graph[b].add(a)
    return graph


def bfs_path(graph, start: str, goal: str):
    if start == goal:
        return [start]
    q = deque([start])
    visited = {start: None}
    while q:
        u = q.popleft()
        for v in graph.get(u, []):
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


def greedy_visit_order(graph, start: str, targets: list[str]) -> list[str]:
    remaining = set(targets)
    order = []
    cur = start
    while remaining:
        best = None
        best_d = float("inf")
        for t in remaining:
            d = bfs_distance(graph, cur, t)
            if d < best_d:
                best_d = d
                best = t
        if best is None or best_d == float("inf"):
            break
        order.append(best)
        remaining.remove(best)
        cur = best
    return order
