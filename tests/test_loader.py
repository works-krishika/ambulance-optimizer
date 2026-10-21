import pytest
from pathlib import Path
from graph import load_from_csv

DATA = Path(__file__).resolve().parent.parent / "data"


def test_small_city_loads():
    g = load_from_csv(DATA / "small_city_locations.csv", DATA / "small_city_roads.csv")
    assert g.num_vertices() == 6
    assert g.num_edges() == 7
    assert sorted(g.hospitals()) == [2, 5]


def test_negative_distance_error():
    with pytest.raises(ValueError, match="negative"):
        load_from_csv(DATA / "small_city_locations.csv", DATA / "invalid_negative_roads.csv")


def test_unknown_id_error():
    with pytest.raises(ValueError, match="unknown location"):
        load_from_csv(DATA / "small_city_locations.csv", DATA / "invalid_unknown_id_roads.csv")


def test_no_hospital_error():
    with pytest.raises(ValueError, match="no hospital"):
        load_from_csv(DATA / "single_locations.csv", DATA / "single_roads.csv")


def test_single_location_allowed_without_hospital_check():
    g = load_from_csv(DATA / "single_locations.csv", DATA / "single_roads.csv",
                      require_hospital=False)
    assert g.num_vertices() == 1

# ---------- real city (the one used in the demo) ----------
def real_city():
    return load_from_csv(DATA / "city_locations.csv", DATA / "city_roads.csv")


def test_real_city_loads():
    g = real_city()
    assert g.num_vertices() == 25
    assert g.num_edges() == 39
    assert sorted(g.hospitals()) == [3, 13, 14, 24]


def test_real_city_is_connected_and_hospital_reachable():
    from algorithms.bfs_dfs import connected_components, reachable_hospitals
    g = real_city()
    assert len(connected_components(g)) == 1
    assert reachable_hospitals(g, 0)          # from Railway Station


def test_real_city_only_uses_agreed_location_types():
    g = real_city()
    assert {d["type"] for d in g.locations.values()} <= {"hospital", "junction", "landmark"}


def test_real_city_roads_are_valid():
    g = real_city()
    for u in g.adj:
        for v, road in g.adj[u].items():
            assert road["distance"] >= 0 and road["time"] >= 0
            assert road["traffic"] in ("low", "medium", "high")
