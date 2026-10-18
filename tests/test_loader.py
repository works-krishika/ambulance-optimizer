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