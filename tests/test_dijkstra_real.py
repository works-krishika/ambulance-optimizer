"""Tests on Student 1's real Graph class (the other file uses a FakeGraph)."""
import math
import pytest
from graph import Graph
from generator import generate_city, generate_dense_city
from algorithms.dijkstra import (dijkstra_heap, dijkstra_array,
                                 nearest_hospital, route_totals)
from algorithms.bellman_ford import bellman_ford

MODES = ["distance", "time", "combined"]


@pytest.mark.parametrize("seed", range(50))
def test_three_algorithms_agree_on_real_graph(seed):
    g = generate_city(80, seed=seed)
    g.weight_mode = MODES[seed % 3]
    a = dijkstra_heap(g, 0)["dist"]
    b = dijkstra_array(g, 0)["dist"]
    c = bellman_ford(g, 0)["dist"]
    for v in g.adj:
        assert math.isclose(a[v], b[v], abs_tol=1e-9)
        assert math.isclose(a[v], c[v], abs_tol=1e-9)


def test_agree_on_dense_graph():
    g = generate_dense_city(60, seed=3)
    a = dijkstra_heap(g, 0)["dist"]
    b = dijkstra_array(g, 0)["dist"]
    assert all(math.isclose(a[v], b[v], abs_tol=1e-9) for v in g.adj)


def test_same_result_shape():
    g = generate_city(40, seed=1)
    a = dijkstra_heap(g, 0, record_steps=True)
    b = dijkstra_array(g, 0, record_steps=True)
    assert set(a) == set(b) == {"dist", "prev", "steps", "ops"}
    for s in a["steps"]:
        assert set(s) == {"step", "selected", "dist", "updated"}
        assert all(isinstance(t, tuple) for t in s["updated"])


def test_start_is_hospital_real_graph():
    g = generate_city(40, seed=2)
    h = g.hospitals()[0]
    best, _ = nearest_hospital(g, h)
    assert best["cost"] == 0 and best["path"] == [h]


def test_all_hospitals_blocked_real_graph():
    g = generate_city(40, seed=2)
    hosp = set(g.hospitals())
    for h in hosp:
        for v in list(g.adj[h]):
            g.block_road(h, v)
    start = next(i for i in g.adj if i not in hosp)
    for algo in (dijkstra_heap, dijkstra_array):
        best, _ = nearest_hospital(g, start, algo)
        assert best is None


def test_equal_cost_routes_both_dijkstras_agree():
    g = Graph()
    for i, t in enumerate(["junction", "junction", "junction", "hospital"]):
        g.add_location(i, f"N{i}", t)
    g.add_road(0, 1, 2, 2)
    g.add_road(0, 2, 2, 2)
    g.add_road(1, 3, 2, 2)
    g.add_road(2, 3, 2, 2)          # two routes, both cost 4
    b1, _ = nearest_hospital(g, 0, dijkstra_heap)
    b2, _ = nearest_hospital(g, 0, dijkstra_array)
    assert b1["cost"] == b2["cost"] == 4
    assert b1["path"][0] == 0 and b1["path"][-1] == 3


def test_totals_independent_of_weight_mode():
    g = generate_city(40, seed=5)
    g.weight_mode = "time"
    best, _ = nearest_hospital(g, 0)
    p = best["path"]
    km = sum(g.adj[a][b]["distance"] for a, b in zip(p, p[1:]))
    assert best["totals"]["distance_km"] == round(km, 2)
    assert route_totals(g, p) == best["totals"]
