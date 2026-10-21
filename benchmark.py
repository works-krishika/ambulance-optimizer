"""benchmark.py - Student 2. Timing + operation-count experiments and plots.

Run from the project root:
    python3 benchmark.py            # full run (a few minutes)
    python3 benchmark.py --quick    # small sizes, ~10 seconds, to check it works

Writes into results/:
    benchmark.csv            all measurements (sparse and dense series)
    time_vs_v_sparse.png     running time vs V, road-like (sparse) graphs
    time_vs_v_dense.png      running time vs V, dense graphs (E close to V^2/10)
    operations_vs_v.png      operation counts vs V (sparse graphs)
Time is the average of several runs measured with time.perf_counter().
Close other apps while it runs for cleaner numbers.
"""
import csv
import os
import statistics
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from generator import generate_city, generate_dense_city  # noqa: E402
from algorithms.dijkstra import dijkstra_heap, dijkstra_array  # noqa: E402
from algorithms.bellman_ford import bellman_ford  # noqa: E402

ALGOS = {"Dijkstra (heap)": dijkstra_heap,
         "Dijkstra (array)": dijkstra_array,
         "Bellman-Ford": bellman_ford}
BF_MAX_V = 2000          # Bellman-Ford is O(V*E): skipped above this (say so in the report)
OUT = "results"

if "--quick" in sys.argv:
    SPARSE_SIZES, DENSE_SIZES, RUNS = [100, 300, 600], [50, 100, 200], 2
else:
    SPARSE_SIZES = [100, 500, 1000, 2000, 5000, 10000]
    DENSE_SIZES = [100, 200, 400, 800, 1200, 1600]
    RUNS = 5


def measure(kind, sizes, make_graph):
    rows = []
    for n in sizes:
        g = make_graph(n)
        for name, fn in ALGOS.items():
            if name == "Bellman-Ford" and n > BF_MAX_V:
                continue
            times = []
            for _ in range(RUNS):
                t0 = time.perf_counter()
                res = fn(g, 0)
                times.append((time.perf_counter() - t0) * 1000)
            ops = res["ops"]
            rows.append({"graph": kind, "V": n, "E": g.num_edges(), "algorithm": name,
                         "avg_ms": round(statistics.mean(times), 3),
                         "relaxations": ops.get("relaxations"),
                         "total_ops": sum(ops.values())})
            print(f"{kind:6} V={n:<6} E={g.num_edges():<7} {name:17} "
                  f"{rows[-1]['avg_ms']:>10.3f} ms   ops={rows[-1]['total_ops']}", flush=True)
    return rows


def plot(rows, kind, ycol, ylabel, title, filename):
    fig, ax = plt.subplots(figsize=(7, 5))
    for name in ALGOS:
        pts = [(r["V"], r[ycol]) for r in rows if r["graph"] == kind and r["algorithm"] == name]
        if pts:
            ax.plot(*zip(*pts), marker="o", label=name)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Number of locations V (log scale)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, filename), dpi=150)
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = measure("sparse", SPARSE_SIZES,
                   lambda n: generate_city(n, extra_edges_per_node=2, seed=n))
    rows += measure("dense", DENSE_SIZES, lambda n: generate_dense_city(n, seed=n))

    with open(os.path.join(OUT, "benchmark.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    plot(rows, "sparse", "avg_ms", "Average time (ms, log scale)",
         "Running time vs V - sparse (road-like) graphs", "time_vs_v_sparse.png")
    plot(rows, "dense", "avg_ms", "Average time (ms, log scale)",
         "Running time vs V - dense graphs", "time_vs_v_dense.png")
    plot(rows, "sparse", "total_ops", "Operations (log scale)",
         "Operation count vs V - sparse graphs", "operations_vs_v.png")
    print(f"\nSaved benchmark.csv and 3 plots in {OUT}/")


if __name__ == "__main__":
    main()
