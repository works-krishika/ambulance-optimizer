import pytest
from graph import Graph, from_table


def make_small():
    g = Graph()
    g.add_location(0, "A")
    g.add_location(1, "B", "hospital")
    g.add_road(0, 1, 2.0, 5, "high")
    return g


def test_neighbors_and_blocking():
    g = make_small()
    assert list(g.neighbors(0)) == [(1, 2.0)]
    g.block_road(0, 1)
    assert list(g.neighbors(0)) == []
    g.unblock_road(1, 0)          # order must not matter
    assert list(g.neighbors(0)) == [(1, 2.0)]


def test_weight_modes():
    g = make_small()
    g.weight_mode = "time"
    assert list(g.neighbors(0)) == [(1, 5)]
    g.weight_mode = "combined"
    assert list(g.neighbors(0)) == [(1, 12.5)]   # 5 * 2.5


def test_negative_weight_rejected():
    g = Graph(); g.add_location(0, "A"); g.add_location(1, "B")
    with pytest.raises(ValueError):
        g.add_road(0, 1, -5, 3)


def test_unknown_location_rejected():
    g = Graph(); g.add_location(0, "A")
    with pytest.raises(ValueError):
        g.add_road(0, 9, 1, 1)


def test_hospitals_and_counts():
    g = make_small()
    assert g.hospitals() == [1]
    assert g.num_vertices() == 2 and g.num_edges() == 1


def test_matrix_size():
    ids, m = make_small().to_matrix()
    assert len(m) == 2 and m[0][1] == 2.0


def test_from_table_keeps_shorter_duplicate():
    g = from_table([(0, 1, 5, 5, "low"), (1, 0, 3, 4, "low")])
    assert g.adj[0][1]["distance"] == 3

def test_public_add_road_keep_shorter():
    g = Graph(); g.add_location(0, "A"); g.add_location(1, "B")
    g.add_road_keep_shorter(0, 1, 5, 5, "low")
    g.add_road_keep_shorter(1, 0, 9, 9, "low")      # longer duplicate is ignored
    assert g.adj[0][1]["distance"] == 5


def test_from_table_with_locations_and_hospital():
    g = from_table([(0, 1, 2, 5, "low")],
                   locations=[(0, "A", "junction", 0, 0), (1, "B", "hospital", 1, 1)],
                   require_hospital=True)
    assert g.hospitals() == [1]


def test_from_table_requires_hospital_when_asked():
    with pytest.raises(ValueError, match="no hospital"):
        from_table([(0, 1, 2, 5, "low")], require_hospital=True)


def test_from_table_bad_type_and_bad_road_messages():
    with pytest.raises(ValueError, match="unknown type"):
        from_table([], locations=[(0, "A", "shop", 0, 0)])
    with pytest.raises(ValueError, match="road row 1"):
        from_table([(0, 1, -3, 5, "low")])          # negative distance
    with pytest.raises(ValueError, match="road row 1"):
        from_table([(0, 1, 3, 5, "heavy")])         # unknown traffic
