"""
Tests for Student 2's algorithms.   Run from the project root:
    python -m pytest -v

FakeGraph is a tiny stand-in for Student 1's Graph class, so these
tests work even before graph.py is ready.
"""

import math
import random

import pytest

from algorithms.min_heap import MinHeap
from algorithms.dijkstra import (dijkstra_heap, dijkstra_array,
                                 nearest_hospital, reconstruct_path)
from algorithms.bellman_ford import bellman_ford


class FakeGraph:
    """Undirected graph: edges = [(u, v, weight), ...]."""

    def __init__(self, edges, nodes=(), hospitals=(), blocked=()):
        self.adj = {n: {} for n in nodes}
        for u, v, w in edges:
            self.adj.setdefault(u, {})[v] = w
            self.adj.setdefault(v, {})[u] = w
        self._hospitals = list(hospitals)
        self.blocked = {frozenset(r) for r in blocked}

    def neighbors(self, u):
        for v, w in self.adj[u].items():
            if frozenset((u, v)) not in self.blocked:
                yield v, w

    def hospitals(self):
        return self._hospitals


def random_graph(n, extra, seed):
    """Connected random graph: a random tree + extra random edges."""
    rng = random.Random(seed)
    edges = [(i, rng.randrange(i), rng.randint(1, 20)) for i in range(1, n)]
    for _ in range(extra):
        u, v = rng.randrange(n), rng.randrange(n)
        if u != v:
            edges.append((u, v, rng.randint(1, 20)))
    return FakeGraph(edges, nodes=range(n))


# The small example to solve by hand (replace with your own paper example)
#
#        A --4-- B
#        |     / |
#        1   2   5
#        | /     |
#        C --8-- D --3-- E(hospital)
#        |
#        6
#        |
#        F(hospital)
SMALL = [("A", "B", 4), ("A", "C", 1), ("C", "B", 2), ("B", "D", 5),
         ("C", "D", 8), ("D", "E", 3), ("C", "F", 6)]
SMALL_ANSWER = {"A": 0, "B": 3, "C": 1, "D": 8, "E": 11, "F": 7}


# ------------------------------------------------------------------ heap
def test_heap_returns_sorted_order():
    nums = [random.randint(0, 1000) for _ in range(1000)]
    h = MinHeap()
    for x in nums:
        h.push((x, x))
    assert [h.pop()[0] for _ in range(len(nums))] == sorted(nums)
    assert len(h) == 0


def test_heap_pop_empty_raises():
    with pytest.raises(IndexError):
        MinHeap().pop()


# ------------------------------------------------------------- dijkstra
@pytest.mark.parametrize("algo", [dijkstra_heap, dijkstra_array, bellman_ford])
def test_small_graph_matches_hand_solution(algo):
    g = FakeGraph(SMALL)
    assert algo(g, "A")["dist"] == SMALL_ANSWER


def test_path_reconstruction():
    res = dijkstra_heap(FakeGraph(SMALL), "A")
    assert reconstruct_path(res["prev"], "E") == ["A", "C", "B", "D", "E"]


def test_steps_are_recorded():
    res = dijkstra_heap(FakeGraph(SMALL), "A", record_steps=True)
    assert [s["selected"] for s in res["steps"]] == ["A", "C", "B", "F", "D", "E"]


@pytest.mark.parametrize("seed", range(50))
def test_all_three_algorithms_agree(seed):
    g = random_graph(60, 120, seed)
    a = dijkstra_heap(g, 0)["dist"]
    b = dijkstra_array(g, 0)["dist"]
    c = bellman_ford(g, 0)["dist"]
    for v in g.adj:
        assert math.isclose(a[v], b[v]) and math.isclose(a[v], c[v])


# -------------------------------------------------------- nearest hospital
def test_nearest_hospital_normal():
    g = FakeGraph(SMALL, hospitals=["E", "F"])
    best, _ = nearest_hospital(g, "A")
    assert best["hospital"] == "F"
    assert best["cost"] == 7
    assert best["path"] == ["A", "C", "F"]


def test_ambulance_already_at_hospital():
    g = FakeGraph(SMALL, hospitals=["E", "F"])
    best, _ = nearest_hospital(g, "F")
    assert best["cost"] == 0 and best["path"] == ["F"]


def test_blocked_road_changes_hospital():
    g = FakeGraph(SMALL, hospitals=["E", "F"], blocked=[("C", "F")])
    best, _ = nearest_hospital(g, "A")
    assert best["hospital"] == "E" and best["cost"] == 11


def test_all_hospitals_blocked():
    g = FakeGraph(SMALL, hospitals=["E", "F"],
                  blocked=[("C", "F"), ("D", "E")])
    best, _ = nearest_hospital(g, "A", algo=dijkstra_array)
    assert best is None


def test_single_node_city():
    g = FakeGraph([], nodes=["X"], hospitals=["X"])
    best, _ = nearest_hospital(g, "X")
    assert best["cost"] == 0


def test_unknown_start_raises():
    with pytest.raises(ValueError):
        dijkstra_heap(FakeGraph(SMALL), "Z")