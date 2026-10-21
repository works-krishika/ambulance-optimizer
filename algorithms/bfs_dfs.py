"""BFS, DFS, connected components and blocked-road helpers."""
import random
from collections import deque


# ---------------- BFS ----------------
def bfs(graph, start):
    """Breadth-first search. Skips blocked roads.

    Returns {"order": visit order, "parent": {node: parent}, "level": {node: hops}}.
    O(V + E) time, O(V) space.
    """
    visited = {start}
    order, parent, level = [], {start: None}, {start: 0}
    q = deque([start])
    while q:
        u = q.popleft()
        order.append(u)
        for v, _ in graph.neighbors(u):
            if v not in visited:
                visited.add(v)
                parent[v] = u
                level[v] = level[u] + 1
                q.append(v)
    return {"order": order, "parent": parent, "level": level}


def path_from_parent(parent, target):
    """Rebuild the path start -> target from a parent dict ([] if unreachable)."""
    if target not in parent:
        return []
    path = []
    while target is not None:
        path.append(target)
        target = parent[target]
    return path[::-1]


def reachable_hospitals(graph, start):
    """List of hospital ids reachable from start."""
    seen = set(bfs(graph, start)["order"])
    return [h for h in graph.hospitals() if h in seen]


def fewest_roads_to_hospital(graph, start):
    """(hospital, path) with the fewest roads, or (None, []) if none reachable."""
    result = bfs(graph, start)
    best = None
    for h in graph.hospitals():
        if h in result["level"]:
            if best is None or result["level"][h] < result["level"][best]:
                best = h
    if best is None:
        return None, []
    return best, path_from_parent(result["parent"], best)


# ---------------- DFS (iterative) ----------------
def dfs_order(graph, start):
    """Iterative DFS visit order (no recursion, safe for huge graphs)."""
    seen, order, stack = set(), [], [start]
    while stack:
        u = stack.pop()
        if u in seen:
            continue
        seen.add(u)
        order.append(u)
        for v, _ in graph.neighbors(u):
            if v not in seen:
                stack.append(v)
    return order


def connected_components(graph):
    """List of components, each a list of node ids. Blocked roads are ignored."""
    seen, components = set(), []
    for s in graph.adj:
        if s not in seen:
            comp = dfs_order(graph, s)
            seen.update(comp)
            components.append(comp)
    return components


def zones_without_hospital(graph):
    """Components that contain no hospital (danger zones)."""
    hosp = set(graph.hospitals())
    return [c for c in connected_components(graph) if not hosp.intersection(c)]


# ---------------- Blocked-road simulation ----------------
def all_roads(graph):
    """Sorted list of unique roads as (u, v) with u < v."""
    return sorted({tuple(sorted((u, v))) for u in graph.adj for v in graph.adj[u]})


def block_random_roads(graph, k, seed=0):
    """Block k random roads (repeatable with seed). Returns the blocked list."""
    rng = random.Random(seed)
    roads = all_roads(graph)
    chosen = rng.sample(roads, min(k, len(roads)))
    for u, v in chosen:
        graph.block_road(u, v)
    return chosen


def critical_roads_on_route(graph, path):
    """Roads on `path` whose closure cuts the start off from every hospital.

    Blocks each road one at a time; graph.blocked is always restored.
    """
    if len(path) < 2:
        return []
    original = set(graph.blocked)
    critical = []
    try:
        for u, v in zip(path, path[1:]):
            graph.block_road(u, v)
            if not reachable_hospitals(graph, path[0]):
                critical.append((u, v))
            graph.blocked = set(original)
    finally:
        graph.blocked = original
    return critical