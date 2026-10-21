"""Random city generator for large test graphs (always connected)."""
import random
from graph import Graph

TRAFFIC = ["low", "medium", "high"]


def generate_city(n, extra_edges_per_node=2, n_hospitals=5, seed=42):
    """Generate a connected random city with n locations.

    A random spanning tree guarantees connectivity; extra random roads add
    cycles. extra_edges_per_node=2 gives ~3V edges (sparse, road-like).
    """
    rng = random.Random(seed)
    g = Graph()
    for i in range(n):
        g.add_location(i, f"L{i}", "junction", rng.random() * 100, rng.random() * 100)
    n_hosp = min(n_hospitals, max(1, n // 10))   # keep hospitals a small share of the city
    for h in rng.sample(range(n), n_hosp):
        g.locations[h]["type"] = "hospital"

    def rand_road(u, v):
        g.add_road(u, v, round(rng.uniform(0.5, 5), 2),
                   round(rng.uniform(1, 12), 1), rng.choice(TRAFFIC))

    order = list(range(n))
    rng.shuffle(order)
    for i in range(1, n):                       # spanning tree -> connected
        rand_road(order[i], order[rng.randrange(i)])
    for _ in range(n * extra_edges_per_node):   # extra roads -> cycles
        u, v = rng.randrange(n), rng.randrange(n)
        if u != v and v not in g.adj[u]:
            rand_road(u, v)
    return g


def generate_dense_city(n, n_hospitals=5, seed=42):
    """Dense variant (~n^2/10 attempts). Use only for n <= about 2000."""
    return generate_city(n, extra_edges_per_node=max(2, n // 10),
                         n_hospitals=n_hospitals, seed=seed)


if __name__ == "__main__":
    for size in (100, 1000, 10000):
        city = generate_city(size)
        print(f"n={size}: V={city.num_vertices()}, E={city.num_edges()}")