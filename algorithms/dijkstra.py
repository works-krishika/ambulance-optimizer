"""
dijkstra.py  -  Shortest route algorithms (Student 2)

Contains
--------
dijkstra_heap(graph, source, record_steps=False)   O((V + E) log V)
dijkstra_array(graph, source, record_steps=False)  O(V^2)
reconstruct_path(prev, target)
route_totals(graph, path)
nearest_hospital(graph, start, algo=dijkstra_heap)

What the graph must provide (agreed with Student 1)
---------------------------------------------------
graph.adj            dict: node -> {neighbour: road}
graph.neighbors(u)   yields (v, weight) for every NOT-blocked road from u
graph.hospitals()    list of hospital nodes

Every shortest-path function returns the same dict:
    {"dist": {...}, "prev": {...}, "steps": [...], "ops": {...}}
"""

import math

from algorithms.min_heap import MinHeap


def _check_source(graph, source):
    if source not in graph.adj:
        raise ValueError(f"Start location {source!r} is not in the city map")


# ---------------------------------------------------------------------------
# Version 1: Dijkstra with a binary min-heap  ->  O((V + E) log V)
# ---------------------------------------------------------------------------
def dijkstra_heap(graph, source, record_steps=False):
    """Dijkstra using our own MinHeap with 'lazy deletion'.

    Instead of a decrease-key operation, whenever a shorter distance to v
    is found we simply push a NEW entry (dist, v). Older entries for v are
    still in the heap; when one of them is popped later we skip it,
    because v is already finalised ("done").
    """
    _check_source(graph, source)

    dist = {v: math.inf for v in graph.adj}   # best known cost from source
    prev = {v: None for v in graph.adj}       # previous node on best path
    dist[source] = 0

    heap = MinHeap()
    heap.push((0, source))
    done = set()                              # finalised nodes
    steps = []
    relaxations = 0

    while len(heap) > 0:
        d, u = heap.pop()                     # closest unfinished node
        if u in done:                         # stale entry -> skip
            continue
        done.add(u)

        updated = []
        for v, w in graph.neighbors(u):       # blocked roads already skipped
            relaxations += 1
            if d + w < dist[v]:               # relaxation step
                dist[v] = d + w
                prev[v] = u
                heap.push((dist[v], v))
                updated.append((v, round(dist[v], 2)))

        if record_steps:
            steps.append({"step": len(steps) + 1,
                          "selected": u,
                          "dist": round(d, 2),
                          "updated": updated})

    return {"dist": dist, "prev": prev, "steps": steps,
            "ops": {"relaxations": relaxations, "heap_ops": heap.ops}}


# ---------------------------------------------------------------------------
# Version 2: Dijkstra with a simple array (linear scan)  ->  O(V^2)
# ---------------------------------------------------------------------------
def dijkstra_array(graph, source, record_steps=False):
    """Textbook Dijkstra: in each round scan ALL nodes to find the
    unfinished node with the smallest distance."""
    _check_source(graph, source)

    dist = {v: math.inf for v in graph.adj}
    prev = {v: None for v in graph.adj}
    dist[source] = 0
    done = set()
    steps = []
    comparisons = 0
    relaxations = 0

    for _ in range(len(graph.adj)):
        # 1. find the closest unfinished node  -> O(V) scan
        u, best = None, math.inf
        for v in graph.adj:
            comparisons += 1
            if v not in done and dist[v] < best:
                u, best = v, dist[v]
        if u is None:                 # the rest are unreachable
            break
        done.add(u)

        # 2. relax its roads
        updated = []
        for v, w in graph.neighbors(u):
            relaxations += 1
            if v not in done and best + w < dist[v]:
                dist[v] = best + w
                prev[v] = u
                updated.append((v, round(dist[v], 2)))

        if record_steps:
            steps.append({"step": len(steps) + 1,
                          "selected": u,
                          "dist": round(best, 2),
                          "updated": updated})

    return {"dist": dist, "prev": prev, "steps": steps,
            "ops": {"relaxations": relaxations, "comparisons": comparisons}}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def reconstruct_path(prev, target):
    """Follow prev[] backwards from target to the source, then reverse."""
    path = []
    while target is not None:
        path.append(target)
        target = prev[target]
    return path[::-1]


def route_totals(graph, path):
    """Total km and total minutes along a path, whatever the weight mode.

    Works when roads are dicts {"distance", "time", ...} (Student 1's
    Graph). If roads are plain numbers (test graphs), returns None.
    """
    total_km, total_min = 0.0, 0.0
    for u, v in zip(path, path[1:]):
        road = graph.adj[u][v]
        if not isinstance(road, dict):
            return None
        total_km += road["distance"]
        total_min += road["time"]
    return {"distance_km": round(total_km, 2), "time_min": round(total_min, 2)}


def nearest_hospital(graph, start, algo=dijkstra_heap):
    """Run Dijkstra ONCE from the ambulance and pick the cheapest hospital.

    Returns (best, res):
      best = None if there is no reachable hospital, otherwise
             {"hospital", "cost", "path", "totals", "ranking"}
      res  = the full output of the algorithm (for the step table)
    """
    res = algo(graph, start, record_steps=True)
    hospitals = graph.hospitals()
    if not hospitals:
        return None, res

    ranking = sorted((res["dist"][h], h) for h in hospitals
                     if res["dist"][h] != math.inf)
    if not ranking:                         # every hospital is cut off
        return None, res

    cost, hospital = ranking[0]
    path = reconstruct_path(res["prev"], hospital)
    return {"hospital": hospital,
            "cost": cost,
            "path": path,
            "totals": route_totals(graph, path),
            "ranking": ranking}, res