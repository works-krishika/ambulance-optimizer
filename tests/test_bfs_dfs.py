from pathlib import Path
from graph import load_from_csv
from algorithms.bfs_dfs import (bfs, dfs_order, connected_components,
                                reachable_hospitals, zones_without_hospital,
                                fewest_roads_to_hospital, block_random_roads,
                                critical_roads_on_route)

DATA = Path(__file__).resolve().parent.parent / "data"


def small():
    return load_from_csv(DATA / "small_city_locations.csv", DATA / "small_city_roads.csv")


def test_bfs_levels():
    r = bfs(small(), 0)
    assert r["level"][0] == 0
    assert r["level"][2] == 2
    assert len(r["order"]) == 6


def test_dfs_visits_everything():
    assert sorted(dfs_order(small(), 0)) == [0, 1, 2, 3, 4, 5]


def test_fewest_roads_hospital():
    h, path = fewest_roads_to_hospital(small(), 0)
    assert h == 2 and path == [0, 1, 2]


def test_ambulance_already_at_hospital():
    h, path = fewest_roads_to_hospital(small(), 2)
    assert h == 2 and path == [2]


def test_disconnected_city_two_components():
    g = load_from_csv(DATA / "disconnected_locations.csv", DATA / "disconnected_roads.csv")
    assert len(connected_components(g)) == 2
    assert reachable_hospitals(g, 0) == []
    assert zones_without_hospital(g) == [[0, 1]]


def test_all_hospital_roads_blocked():
    g = small()
    for u, v in [(1, 2), (2, 5), (4, 5)]:
        g.block_road(u, v)
    assert reachable_hospitals(g, 0) == []
    h, path = fewest_roads_to_hospital(g, 0)
    assert h is None and path == []


def test_single_location_no_crash():
    g = load_from_csv(DATA / "single_locations.csv", DATA / "single_roads.csv",
                      require_hospital=False)
    assert bfs(g, 0)["order"] == [0]
    assert connected_components(g) == [[0]]


def test_block_random_roads_repeatable():
    g1, g2 = small(), small()
    assert block_random_roads(g1, 2, seed=7) == block_random_roads(g2, 2, seed=7)


def test_critical_roads_restore_blocked_set():
    g = small()
    g.block_road(2, 5)
    before = set(g.blocked)
    critical_roads_on_route(g, [0, 1, 2])
    assert g.blocked == before