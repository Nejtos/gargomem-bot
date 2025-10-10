from collections import deque
import json
from typing import Optional

from bot.game.services.heroes.tsp_utils import held_karp_shortest_path


def load_world_graph(file_path: str, directed: bool = True):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    graph: dict[str, set[str]] = {}
    for loc in data:
        a = str(loc["location_id"])
        nbrs = [str(k) for k in (loc.get("gateways") or {}).keys()]
        graph.setdefault(a, set()).update(nbrs)
        if not directed:
            for b in nbrs:
                graph.setdefault(b, set()).add(a)
        else:
            for b in nbrs:
                graph.setdefault(b, set())
    return graph


def build_reverse_graph(graph: dict[str, set[str]]) -> dict[str, set[str]]:
    rev: dict[str, set[str]] = {}
    for u, nbrs in graph.items():
        for v in nbrs:
            rev.setdefault(v, set()).add(u)
    for u in graph.keys():
        rev.setdefault(u, set())
    return rev


def bfs_all_distances(
    graph: dict[str, set[str]],
    start: str,
    blocked_edges: Optional[set[tuple[str, str]]] = None,
) -> dict[str, int]:
    start = str(start)
    blocked = blocked_edges or set()
    q = deque([start])
    dist = {start: 0}
    while q:
        u = q.popleft()
        for v in graph.get(u, []):
            if (u, v) in blocked:
                continue
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


def build_map_distance_matrix_directed(
    graph: dict[str, set[str]],
    nodes: list[str],
    blocked_edges: Optional[set[tuple[str, str]]] = None,
) -> list[list[float]]:
    n = len(nodes)
    dm = [[float("inf")] * n for _ in range(n)]
    for i, s in enumerate(nodes):
        dists = bfs_all_distances(graph, s, blocked_edges)
        for j, t in enumerate(nodes):
            dm[i][j] = (
                0.0 if i == j else (float(dists[t]) if t in dists else float("inf"))
            )
    return dm


def bfs_path(
    graph: dict[str, set[str]],
    start: str,
    goal: str,
    blocked_edges: Optional[set[tuple[str, str]]] = None,
):
    start = str(start)
    goal = str(goal)
    blocked = blocked_edges or set()
    if start == goal:
        return [start]
    q = deque([start])
    prev = {start: None}
    while q:
        u = q.popleft()
        for v in graph.get(u, []):
            if (u, v) in blocked:
                continue
            if v in prev:
                continue
            prev[v] = u
            if v == goal:
                path = [v]
                cur = u
                while cur is not None:
                    path.append(cur)
                    cur = prev[cur]
                path.reverse()
                return path
            q.append(v)
    return None


def bfs_path_avoid_nodes(
    graph: dict[str, set[str]],
    start: str,
    goal: str,
    blocked_edges: Optional[set[tuple[str, str]]] = None,
    avoid_nodes: Optional[set[str]] = None,
) -> Optional[list[str]]:
    start = str(start)
    goal = str(goal)
    if start == goal:
        return [start]
    blocked = blocked_edges or set()
    avoid = set(str(x) for x in (avoid_nodes or set()))
    q = deque([start])
    prev = {start: None}
    while q:
        u = q.popleft()
        for v in graph.get(u, []):
            if (u, v) in blocked:
                continue
            if v in prev:
                continue
            if v in avoid and v not in (start, goal):
                continue
            prev[v] = u
            if v == goal:
                path = [v]
                cur = u
                while cur is not None:
                    path.append(cur)
                    cur = prev[cur]
                path.reverse()
                return path
            q.append(v)
    return None


def compute_map_route(
    graph,
    current: str,
    remaining: set[str],
    blocked_edges: Optional[set[tuple[str, str]]] = None,
) -> list[str]:
    cur = str(current)
    if not remaining:
        return [cur]
    nodes = [cur] + [str(x) for x in remaining if str(x) != cur]
    d0 = bfs_all_distances(graph, cur, blocked_edges)
    unreachable = [t for t in nodes if t not in d0]
    if unreachable:
        nodes_reachable = [n for n in nodes if n in d0]
        if len(nodes_reachable) <= 1:
            return nodes_reachable + unreachable
        dm = build_map_distance_matrix_directed(graph, nodes_reachable, blocked_edges)
        order_idx = held_karp_shortest_path(dm) if len(nodes_reachable) <= 18 else None
        if not order_idx:
            order_idx = [0]
            unused = set(range(1, len(nodes_reachable)))
            pos = 0
            while unused:
                best, bestd = None, float("inf")
                for j in unused:
                    if dm[pos][j] < bestd:
                        best, bestd = j, dm[pos][j]
                if best is None or bestd == float("inf"):
                    break
                order_idx.append(best)
                unused.remove(best)
                pos = best
            if unused:
                order_idx.extend(sorted(unused))
        return [nodes_reachable[i] for i in order_idx] + unreachable
    dm = build_map_distance_matrix_directed(graph, nodes, blocked_edges)
    order_idx = held_karp_shortest_path(dm) if len(nodes) <= 18 else None
    if order_idx:
        return [nodes[i] for i in order_idx]
    order = [0]
    unused = set(range(1, len(nodes)))
    pos = 0
    while unused:
        best, bestd = None, float("inf")
        for j in unused:
            if dm[pos][j] < bestd:
                best, bestd = j, dm[pos][j]
        if best is None or bestd == float("inf"):
            break
        order.append(best)
        unused.remove(best)
        pos = best
    if unused:
        order.extend(sorted(unused))
    return [nodes[i] for i in order]
