"""app.py - Student 3. Streamlit UI + integration of Student 1 and 2 modules.
Run:  streamlit run app.py
ASSUMPTIONS are marked  # ASSUME  - confirm each with the owner (see notes)."""
import os
import tempfile
import time

import pandas as pd
import streamlit as st

from graph import load_from_csv                                  # Student 1
from algorithms.dijkstra import dijkstra_heap, dijkstra_array, nearest_hospital  # Student 2
from algorithms.bfs_dfs import bfs, connected_components, zones_without_hospital  # Student 1
from visualize import draw_city, MAX_DRAW_NODES

st.set_page_config(page_title="Ambulance Route Optimizer", layout="wide")
st.title("Smart Emergency Ambulance Route Optimizer")

LOC = os.path.join("data", "city_locations.csv")
ROAD = os.path.join("data", "city_roads.csv")


# ---------------------------------------------------------------- data source
def load_graph():
    """Build the graph from the chosen source. Errors are shown, never crash."""
    src = st.sidebar.radio("Data source", ["Sample city", "Upload CSV",
                                           "Enter manually", "Random city"])
    try:
        if src == "Sample city":
            return load_from_csv(LOC, ROAD)
        if src == "Upload CSV":
            fl = st.sidebar.file_uploader("Locations CSV", type="csv")
            fr = st.sidebar.file_uploader("Roads CSV", type="csv")
            if not (fl and fr):
                st.info("Upload both files (id,name,type,x,y and from,to,distance_km,time_min,traffic).")
                return None
            tmp = tempfile.mkdtemp()
            pl, pr = os.path.join(tmp, "l.csv"), os.path.join(tmp, "r.csv")
            open(pl, "wb").write(fl.getvalue())
            open(pr, "wb").write(fr.getvalue())
            return load_from_csv(pl, pr)
        if src == "Enter manually":
            from graph import from_table                          # ASSUME from_table(loc_df, road_df)
            n = st.sidebar.number_input("Number of locations", 2, 30, 5)
            loc0 = pd.DataFrame({"id": range(int(n)), "name": [f"L{i}" for i in range(int(n))],
                                 "type": ["junction"] * int(n), "x": [float(i % 5) for i in range(int(n))],
                                 "y": [float(i // 5) for i in range(int(n))]})
            road0 = pd.DataFrame({"from": [0], "to": [1], "distance_km": [1.0],
                                  "time_min": [2.0], "traffic": ["low"]})
            st.subheader("Locations (type: hospital / junction / landmark)")
            loc = st.data_editor(loc0, num_rows="dynamic", key="loc_ed")
            st.subheader("Roads (traffic: low / medium / high)")
            road = st.data_editor(road0, num_rows="dynamic", key="road_ed")
            return from_table(loc, road)
        from generator import generate_city                      # ASSUME generate_city(V)
        v = st.sidebar.slider("Number of locations (V)", 10, 5000, 100)
        return generate_city(v)
    except Exception as e:  # loader validation errors -> friendly message
        st.error(f"Could not load the city: {e}")
        return None


g = load_graph()
if g is None:
    st.stop()
names = {lid: d["name"] for lid, d in g.locations.items()}
drawable = len(g.locations) <= MAX_DRAW_NODES

# -------------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Emergency details")
    start = st.selectbox("Ambulance location", list(names), format_func=names.get)
    hosp = st.multiselect("Hospitals", list(names), default=g.hospitals(), format_func=names.get)
    roads = [(u, v) for u in g.adj for v in g.adj[u] if str(u) < str(v)]
    if len(roads) > 2000:
        st.caption("Too many roads to list; use 'Block 3 random roads'.")
    blocked = st.multiselect("Blocked roads", roads[:2000], key="blocked_sel",
                             format_func=lambda r: f"{names[r[0]]} - {names[r[1]]}")
    g.weight_mode = st.radio("Optimise for", ["distance", "time", "combined"])
    algo_name = st.radio("Algorithm", ["Dijkstra (heap)", "Dijkstra (array)"])
    go = st.button("Find route", type="primary")

for lid in g.locations:  # apply hospital choice
    if lid in hosp:
        g.locations[lid]["type"] = "hospital"
    elif g.locations[lid]["type"] == "hospital":
        g.locations[lid]["type"] = "junction"
g.blocked = {frozenset(r) for r in blocked}  # apply blockages (neighbors() skips them)


# -------------------------------------------------------------------- helpers
def solve(graph, algo):
    t0 = time.perf_counter()
    best, res = nearest_hospital(graph, start, algo)  # ASSUME -> (best{hospital,cost,path}, res)
    return best, res, (time.perf_counter() - t0) * 1000


def totals(path):
    """Total km and minutes along a path, read straight from g.adj."""
    km = sum(g.adj[a][b]["distance"] for a, b in zip(path, path[1:]))
    mn = sum(g.adj[a][b]["time"] for a, b in zip(path, path[1:]))
    return km, mn


def pair(fs):
    return tuple(sorted(fs, key=str))


algo = dijkstra_heap if algo_name == "Dijkstra (heap)" else dijkstra_array
if go:
    st.session_state.result = solve(g, algo)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Route Map", "Algorithm Steps",
                                        "Blockage Simulation", "Performance", "About"])
has = "result" in st.session_state
if has:
    best, res, ms = st.session_state.result

# ---------------------------------------------------------------------- tab 1
with tab1:
    if not has:
        st.info("Choose the ambulance location in the sidebar and press Find route.")
    elif best is None:
        st.error("No hospital is reachable - all routes are blocked!")
    else:
        km, mn = totals(best["path"])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Nearest hospital", names[best["hospital"]])
        c2.metric(f"Total {g.weight_mode}", round(best["cost"], 2))
        c3.metric("Distance / time", f"{km:.2f} km / {mn:.1f} min")
        c4.metric("Execution time", f"{ms:.3f} ms")
        st.write(" -> ".join(names[i] for i in best["path"]))
        if drawable:
            st.pyplot(draw_city(g, best["path"], "Selected ambulance route"))
        else:
            st.warning(f"Map hidden: {len(g.locations)} locations is too many to draw legibly. "
                       f"The route has {len(best['path'])} stops (see text above).")
        st.subheader("Hospital ranking")
        rank = [{"Hospital": names[h], f"Cost ({g.weight_mode})": res["dist"].get(h, float("inf"))}
                for h in hosp]
        st.dataframe(sorted(rank, key=lambda r: r[f"Cost ({g.weight_mode})"]), use_container_width=True)

# ---------------------------------------------------------------------- tab 2
with tab2:
    if not has:
        st.info("Run Find route first.")
    else:
        steps = res.get("steps") or []
        st.subheader("Dijkstra step table")
        if not steps:
            st.warning("No steps recorded - nearest_hospital must call the algorithm with record_steps=True.")
        else:
            st.dataframe([{"Step": s["step"], "Selected node": names.get(s["selected"], s["selected"]),
                           "Distance": s["dist"],
                           "Nodes updated": ", ".join(str(names.get(u, u)) for u in s["updated"])}
                          for s in steps], use_container_width=True)
            if drawable:
                k = st.slider("Step k", 1, len(steps), len(steps))
                done = {s["selected"] for s in steps[:k]}
                st.pyplot(draw_city(g, best["path"] if best else None, f"Settled after step {k}", settled=done))
        st.subheader("BFS visit order (connectivity from the ambulance)")
        b = bfs(g, start)  # ASSUME dict with 'order' (and optional 'level') or a plain list
        order = b["order"] if isinstance(b, dict) and "order" in b else b
        lvl = b.get("level", {}) if isinstance(b, dict) else {}
        st.dataframe([{"Visit #": i + 1, "Location": names[n], "Level": lvl.get(n, "")}
                      for i, n in enumerate(order)], use_container_width=True)
        st.write("Reachable hospitals:", ", ".join(names[h] for h in hosp if h in set(order)) or "none")

# ---------------------------------------------------------------------- tab 3
with tab3:
    st.button("Block 3 random roads", on_click=lambda: (
        g.block_random_roads(3),  # ASSUME method on graph, updates g.blocked
        st.session_state.update(blocked_sel=[pair(f) for f in g.blocked if pair(f) in roads])))
    if not has:
        st.info("Run Find route first.")
    else:
        saved = set(g.blocked)
        g.blocked = set()
        b0, _, _ = solve(g, algo)
        g.blocked = saved
        b1, _, _ = solve(g, algo)
        left, right = st.columns(2)
        for col, bb, ttl in ((left, b0, "No blockages"), (right, b1, "With selected blockages")):
            with col:
                if drawable:
                    st.pyplot(draw_city(g, bb["path"] if bb else None, ttl))
                st.caption(ttl + (": no route" if bb is None else f": {names[bb['hospital']]}, cost {bb['cost']:.2f}"))
        if b0 and b1:
            st.metric("Change in cost", f"{b1['cost'] - b0['cost']:+.2f}")
            st.write("Hospital changed." if b0["hospital"] != b1["hospital"] else "Same hospital.")
        comps = connected_components(g)  # ASSUME list of node collections
        st.write(f"Connected components: **{len(comps)}**")
        for z in zones_without_hospital(g):  # ASSUME iterable of node collections
            st.warning("Zone with no hospital: " + ", ".join(names[n] for n in z))

# ---------------------------------------------------------------------- tab 4
with tab4:
    if st.button("Run both Dijkstra versions on this city"):
        rows = []
        for nm, fn in (("Dijkstra (array)", dijkstra_array), ("Dijkstra (heap)", dijkstra_heap)):
            t0 = time.perf_counter()
            r = fn(g, start)
            rows.append({"Algorithm": nm, "Time (ms)": round((time.perf_counter() - t0) * 1000, 4),
                         "Operations": str(r.get("ops"))})
        st.dataframe(rows, use_container_width=True)
    for img in ("time_vs_v.png", "time_vs_e.png"):
        p = os.path.join("results", img)
        if os.path.exists(p):
            st.image(p)
    csvp = os.path.join("results", "benchmark.csv")
    if os.path.exists(csvp):
        st.dataframe(pd.read_csv(csvp), use_container_width=True)
    else:
        st.caption("Benchmark plots/CSV from Student 2 will appear here once results/ is populated.")

# ---------------------------------------------------------------------- tab 5
with tab5:
    st.markdown("""
**Problem.** Find the best route from an emergency location to the nearest suitable hospital in a city road
network (graph: intersections = vertices, roads = weighted edges), with road blockages.

**How to use.** Pick a data source, set ambulance location, hospitals, blocked roads and weight mode, press *Find route*.

| Algorithm | Time | Space |
|---|---|---|
| BFS / DFS | O(V + E) | O(V) |
| Dijkstra (array) | O(V^2) | O(V) |
| Dijkstra (binary heap) | O((V + E) log V) | O(V) |
| Bellman-Ford | O(V*E) | O(V) |

**Team.** Student 1: graph and BFS/DFS. Student 2: Dijkstra, heap, benchmarks. Student 3: UI, visualisation, report.
""")
