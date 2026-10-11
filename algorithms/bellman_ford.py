"""
bellman_ford.py  -  Comparison algorithm (Student 2)

Bellman-Ford relaxes EVERY road, V-1 times.  O(V * E).
It is slower than Dijkstra, but it also works with negative weights.
We use it to (1) check Dijkstra's answers and (2) compare running times.
Returns the same dict format as the Dijkstra functions.
"""

import math


def bellman_ford(graph, source, record_steps=False):
    if source not in graph.adj:
        raise ValueError(f"Start location {source!r} is not in the city map")

    dist = {v: math.inf for v in graph.adj}
    prev = {v: None for v in graph.adj}
    dist[source] = 0
    steps = []
    relaxations = 0
    rounds = 0

    for _ in range(len(graph.adj) - 1):
        rounds += 1
        changed = False
        for u in graph.adj:
            if dist[u] == math.inf:
                continue
            for v, w in graph.neighbors(u):
                relaxations += 1
                if dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    prev[v] = u
                    changed = True
        if record_steps:
            steps.append({"step": rounds,
                          "dist": {k: round(x, 2) for k, x in dist.items()}})
        if not changed:          # early stop: nothing improved this round
            break

    return {"dist": dist, "prev": prev, "steps": steps,
            "ops": {"relaxations": relaxations, "rounds": rounds}}