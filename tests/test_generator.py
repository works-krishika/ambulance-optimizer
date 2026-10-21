import pytest
from generator import generate_city, generate_dense_city
from algorithms.bfs_dfs import connected_components


@pytest.mark.parametrize("n", [1, 100, 1000, 10000])
def test_generated_city_is_connected(n):
    g = generate_city(n)
    assert g.num_vertices() == n
    assert len(connected_components(g)) == 1


def test_same_seed_same_city():
    a, b = generate_city(200, seed=5), generate_city(200, seed=5)
    assert a.adj == b.adj


def test_dense_has_more_edges():
    assert generate_dense_city(300).num_edges() > generate_city(300).num_edges()

@pytest.mark.parametrize("n,expected", [(1, 1), (10, 1), (30, 3), (100, 5), (1000, 5)])
def test_hospital_count_is_a_small_share(n, expected):
    g = generate_city(n)
    assert len(g.hospitals()) == expected
