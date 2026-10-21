"""app.py - Student 3. Streamlit UI + integration of Student 1 and 2 modules.
Run:  streamlit run app.py
The UI only collects input and draws results; all algorithm work happens in
graph.py, generator.py and the algorithms/ package."""
import glob
import math
import os
import tempfile
import time

import pandas as pd
import streamlit as st

from graph import load_from_csv, from_table, VALID_TYPES, TRAFFIC_FACTOR        # Student 1
from generator import generate_city                                           # Student 1
from algorithms.bfs_dfs import (bfs, connected_components, zones_without_hospital,  # Student 1
                                reachable_hospitals, fewest_roads_to_hospital,
                                critical_roads_on_route, all_roads, block_random_roads)
from algorithms.dijkstra import dijkstra_heap, dijkstra_array, nearest_hospital      # Student 2
from algorithms.bellman_ford import bellman_ford                                     # Student 2
from visualize import draw_city, MAX_DRAW_NODES

st.set_page_config(page_title="Ambulance Route Optimizer", layout="wide")
st.title("Smart Emergency Ambulance Route Optimizer")

LOC = os.path.join("data", "city_locations.csv")
ROAD = os.path.join("data", "city_roads.csv")
MAX_LISTED_ROADS = 2000   # the 'Blocked roads' list gets unusable beyond this
BF_MAX_V = 2000           # Bellman-Ford is O(V*E): only run it on small cities


# ------------------------------------------------------------ data source
def _load_uploaded(loc_bytes, road_bytes):
    with tempfile.TemporaryDirectory() as tmp:
        pl, pr = os.path.join(tmp, "l.csv"), os.path.join(tmp, "r.csv")
        with open(pl, "wb") as f:
            f.write(loc_bytes)
        with open(pr, "wb") as f:
            f.write(road_bytes)
        return load_from_csv(pl, pr)


def _graph_from_editors(loc, road):
    """Build the Graph from the two editable tables (clear errors, no crash)."""
    loc = loc.dropna(subset=["id", "name", "type"])
    road = road.dropna(subset=["from", "to", "distance_km", "time_min", "traffic"])
    if loc.empty:
        raise ValueError("add at least one location")
    locations = []
    for lid, name, ltype, x, y in loc[["id", "name", "type", "x", "y"]].itertuples(index=False):
        if lid != int(lid):
            raise ValueError(f"location id {lid} must be a whole number")
        locations.append((int(lid), name, ltype,
                          0.0 if pd.isna(x) else float(x), 0.0 if pd.isna(y) else float(y)))
    ids = {row[0] for row in locations}
    rows = []
    for u, v, d, t, traffic in road[["from", "to", "distance_km", "time_min",
                                     "traffic"]].itertuples(index=False):
        if int(u) not in ids or int(v) not in ids:
            raise ValueError(f"road {int(u)} - {int(v)} uses a location id that is not in the "
                             f"locations table")
        rows.append((int(u), int(v), float(d), float(t), traffic))
    return from_table(rows, locations, require_hospital=True)


def _reset_selections():
    for k in ("start_sel", "hosp_sel", "blocked_sel", "result", "perf"):
        st.session_state.pop(k, None)


def get_graph():
    """Return the cached graph bundle for the chosen source, or None.
    The graph is only rebuilt when the source or its input changes."""
    src = st.sidebar.radio("Data source", ["Sample city", "Upload CSV",
                                           "Enter manually", "Random city"], key="src")
    if src == "Sample city":
        key, build = ("sample",), lambda: load_from_csv(LOC, ROAD)
    elif src == "Upload CSV":
        fl = st.sidebar.file_uploader("Locations CSV", type="csv", key="up_loc")
        fr = st.sidebar.file_uploader("Roads CSV", type="csv", key="up_road")
        if not (fl and fr):
            st.info("Upload both files (id,name,type,x,y and from,to,distance_km,time_min,traffic).")
            return None
        bl, br = fl.getvalue(), fr.getvalue()
        key, build = ("upload", hash(bl), hash(br)), lambda: _load_uploaded(bl, br)
    elif src == "Enter manually":
        n = int(st.sidebar.number_input("Number of locations", 2, 30, 5))
        loc0 = pd.DataFrame({"id": range(n), "name": [f"L{i}" for i in range(n)],
                             "type": ["hospital" if i == n - 1 else "junction" for i in range(n)],
                             "x": [float(i % 5) for i in range(n)],
                             "y": [float(i // 5) for i in range(n)]})
        road0 = pd.DataFrame({"from": list(range(n - 1)), "to": list(range(1, n)),
                              "distance_km": [1.0] * (n - 1), "time_min": [2.0] * (n - 1),
                              "traffic": ["low"] * (n - 1)})
        st.subheader("Locations")
        loc = st.data_editor(loc0, num_rows="dynamic", key=f"loc_ed_{n}", column_config={
            "type": st.column_config.SelectboxColumn("type", options=sorted(VALID_TYPES))})
        st.subheader("Roads (two-way)")
        road = st.data_editor(road0, num_rows="dynamic", key=f"road_ed_{n}", column_config={
            "traffic": st.column_config.SelectboxColumn("traffic", options=list(TRAFFIC_FACTOR))})
        key = ("manual", loc.to_json(), road.to_json())
        build = lambda: _graph_from_editors(loc, road)
    else:
        v = st.sidebar.slider("Number of locations (V)", 10, 5000, 100)
        key, build = ("random", v), lambda: generate_city(v)

    cache = st.session_state.get("_gcache")
    if cache is None or cache["key"] != key:
        try:
            g = build()
        except Exception as e:  # loader validation errors -> friendly message
            st.error(f"Could not load the city: {e}")
            return None
        _reset_selections()  # new city -> old selections no longer valid
        cache = {"key": key, "g": g, "hosp0": g.hospitals(),
                 "types0": {lid: d["type"] for lid, d in g.locations.items()}}
        st.session_state["_gcache"] = cache
    return cache


cache = get_graph()
if cache is None:
    st.stop()
g = cache["g"]
names = {lid: d["name"] for lid, d in g.locations.items()}
drawable = len(g.locations) <= MAX_DRAW_NODES


# ------------------------------------------------------------- callbacks
def _block_random():
    """Replace the blocked-road selection with 3 random roads."""
    gg = st.session_state["_gcache"]["g"]
    saved = set(gg.blocked)
    chosen = block_random_roads(gg, 3, seed=time.time_ns())
    gg.blocked = saved  # the sidebar re-applies the selection on the next run
    st.session_state["blocked_sel"] = [tuple(r) for r in chosen]


def _clear_blocked():
    st.session_state["blocked_sel"] = []


# --------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Emergency details")
    start = st.selectbox("Ambulance location", list(names), format_func=names.get, key="start_sel")
    hosp = st.multiselect("Hospitals", list(names), default=cache["hosp0"],
                          format_func=names.get, key="hosp_sel")
    roads = all_roads(g)
    shown = roads[:MAX_LISTED_ROADS]
    shown_set = set(shown)
    extra = [r for r in st.session_state.get("blocked_sel", []) if r not in shown_set]
    if len(roads) > MAX_LISTED_ROADS:
        st.caption(f"Only the first {MAX_LISTED_ROADS} roads are listed; "
                   "use 'Block 3 random roads' (Blockage Simulation tab) for the rest.")
    blocked = st.multiselect("Blocked roads", shown + extra, key="blocked_sel",
                             format_func=lambda r: f"{names[r[0]]} - {names[r[1]]}")
    weight_mode = st.radio("Optimise for", ["distance", "time", "combined"])
    algo_name = st.radio("Algorithm", ["Dijkstra (heap)", "Dijkstra (array)"])
    go = st.button("Find route", type="primary")

# apply the sidebar choices to the graph (neighbors() skips blocked roads)
hosp_set = set(hosp)
for lid, d in g.locations.items():
    if lid in hosp_set:
        d["type"] = "hospital"
    else:
        old = cache["types0"][lid]
        d["type"] = "junction" if old == "hospital" else old
g.blocked = {frozenset(r) for r in blocked}
g.weight_mode = weight_mode


# --------------------------------------------------------------- helpers
def solve(graph, algo_fn, src):
    t0 = time.perf_counter()
    best_, res_ = nearest_hospital(graph, src, algo_fn)
    return best_, res_, (time.perf_counter() - t0) * 1000


def totals(path):
    """Total km and minutes along a path, read straight from g.adj."""
    return {"distance_km": round(sum(g.adj[a][b]["distance"] for a, b in zip(path, path[1:])), 2),
            "time_min": round(sum(g.adj[a][b]["time"] for a, b in zip(path, path[1:])), 2)}


def fmt_nodes(nodes, limit=10):
    nodes = list(nodes)
    txt = ", ".join(names[n] for n in nodes[:limit])
    return txt + (f" ... and {len(nodes) - limit} more" if len(nodes) > limit else "")


algo = dijkstra_heap if algo_name == "Dijkstra (heap)" else dijkstra_array

# A result is only valid for the exact settings it was computed with.
sig = (hash(cache["key"]), start, tuple(sorted(hosp)), tuple(sorted(blocked)),
       weight_mode, algo_name)
if go and hosp:
    b_, r_, t_ = solve(g, algo, start)
    st.session_state["result"] = {"sig": sig, "best": b_, "res": r_, "ms": t_}
saved_result = st.session_state.get("result")
has = saved_result is not None and saved_result["sig"] == sig
stale = saved_result is not None and not has
best = res = ms = None
if has:
    best, res, ms = saved_result["best"], saved_result["res"], saved_result["ms"]

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Route Map", "Algorithm Steps",
                                        "Blockage Simulation", "Performance", "About"])

# ----------------------------------------------------------------- tab 1
with tab1:
    if not hosp:
        st.warning("Select at least one hospital in the sidebar.")
    elif not has:
        st.info("Settings changed - press Find route to update the result." if stale else
                "Choose the ambulance location in the sidebar and press Find route.")
    elif best is None:
        st.error("No hospital is reachable - all routes are blocked!")
    else:
        tot = best.get("totals") or totals(best["path"])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Nearest hospital", names[best["hospital"]])
        c2.metric(f"Total cost ({g.weight_mode})", round(best["cost"], 2))
        c3.metric("Distance / time", f"{tot['distance_km']:.2f} km / {tot['time_min']:.1f} min")
        c4.metric("Execution time", f"{ms:.3f} ms")
        st.write("**Dijkstra route:** " + " -> ".join(names[i] for i in best["path"]))

        fh, fpath = fewest_roads_to_hospital(g, start)  # BFS = fewest roads, not shortest
        if fh is not None:
            ft = totals(fpath)
            st.write(f"**Fewest-roads route (BFS):** {' -> '.join(names[i] for i in fpath)} "
                     f"({len(fpath) - 1} roads, {ft['distance_km']:.2f} km) vs Dijkstra "
                     f"({len(best['path']) - 1} roads, {tot['distance_km']:.2f} km)")
        for u, v in critical_roads_on_route(g, best["path"]):
            st.warning(f"Critical road: if {names[u]} - {names[v]} closes, "
                       "no hospital is reachable from the ambulance.")

        if drawable:
            st.pyplot(draw_city(g, best["path"], "Selected ambulance route", start=start))
        else:
            st.warning(f"Map hidden: {len(g.locations)} locations is too many to draw legibly. "
                       f"The route has {len(best['path'])} stops (see text above).")
        st.subheader("Hospital ranking")
        ranked = sorted((res["dist"].get(h, math.inf), h) for h in hosp)
        st.dataframe([{"Hospital": names[h],
                       f"Cost ({g.weight_mode})": "unreachable" if c == math.inf else f"{c:.2f}",
                       "Chosen": "yes" if h == best["hospital"] else ""} for c, h in ranked])
    if not (has and best is not None) and drawable:
        st.pyplot(draw_city(g, None, "City map", start=start))  # ambulance still shown in red

# ----------------------------------------------------------------- tab 2
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
                           "Nodes updated": ", ".join(f"{names.get(u, u)} ({d})"
                                                      for u, d in s["updated"])}
                          for s in steps])
            if drawable:
                k = st.slider("Step k", 1, len(steps), len(steps)) if len(steps) > 1 else 1
                done = {s["selected"] for s in steps[:k]}
                st.pyplot(draw_city(g, best["path"] if best else None,
                                    f"Settled after step {k}", settled=done, start=start))
        st.subheader("BFS visit order (connectivity from the ambulance)")
        b = bfs(g, start)
        st.dataframe([{"Visit #": i + 1, "Location": names[n], "Level": b["level"].get(n, "")}
                      for i, n in enumerate(b["order"])])
        st.write("Reachable hospitals:", fmt_nodes(reachable_hospitals(g, start)) or "none")

# ----------------------------------------------------------------- tab 3
with tab3:
    cb1, cb2 = st.columns(2)
    cb1.button("Block 3 random roads", on_click=_block_random)
    cb2.button("Clear blocked roads", on_click=_clear_blocked)
    st.caption("'Block 3 random roads' replaces the blocked-road selection in the sidebar. "
               "Press Find route afterwards to see the effect.")
    if not has:
        st.info("Run Find route first." if hosp else "Select at least one hospital in the sidebar.")
    else:
        saved = set(g.blocked)
        g.blocked = set()
        b0, _, _ = solve(g, algo, start)   # same trip, no blockages
        g.blocked = saved
        b1 = best                          # the result with the selected blockages
        left, right = st.columns(2)
        for col, bb, ttl, blk in ((left, b0, "No blockages", set()),
                                  (right, b1, "With selected blockages", None)):
            with col:
                if drawable:
                    st.pyplot(draw_city(g, bb["path"] if bb else None, ttl, start=start, blocked=blk))
                st.caption(ttl + (": no route" if bb is None
                                  else f": {names[bb['hospital']]}, cost {bb['cost']:.2f}"))
        if b0 and b1:
            st.metric("Change in cost", f"{b1['cost'] - b0['cost']:+.2f}")
            st.write("Hospital changed." if b0["hospital"] != b1["hospital"] else "Same hospital.")
        elif b0 and not b1:
            st.error("The blockages cut the ambulance off from every selected hospital.")
    comps = connected_components(g)
    st.write(f"Connected components: **{len(comps)}**")
    for z in zones_without_hospital(g):
        st.warning("Zone with no hospital: " + fmt_nodes(z))

# ----------------------------------------------------------------- tab 4
with tab4:
    if st.button("Run the algorithms on this city"):
        runs = [("Dijkstra (array)", dijkstra_array), ("Dijkstra (heap)", dijkstra_heap)]
        note = ""
        if len(g.locations) <= BF_MAX_V:
            runs.append(("Bellman-Ford", bellman_ford))
        else:
            note = f" Bellman-Ford skipped: O(V*E) is too slow above {BF_MAX_V} locations."
        rows = []
        with st.spinner("Running..."):
            for nm, fn in runs:
                t0 = time.perf_counter()
                r = fn(g, start)
                rows.append({"Algorithm": nm,
                             "Time (ms)": round((time.perf_counter() - t0) * 1000, 4),
                             "Operations": str(r.get("ops"))})
        st.session_state["perf"] = {"rows": rows, "caption":
                                    f"{len(g.locations)} locations, {g.num_edges()} roads, "
                                    f"weights = {g.weight_mode}.{note}"}
    perf = st.session_state.get("perf")
    if perf:
        st.dataframe(perf["rows"])
        st.caption(perf["caption"])
    st.subheader("Benchmark results (Student 2)")
    images = sorted(glob.glob(os.path.join("results", "*.png")))
    for p in images:
        st.image(p, caption=os.path.splitext(os.path.basename(p))[0].replace("_", " "))
    csvp = os.path.join("results", "benchmark.csv")
    if os.path.exists(csvp):
        st.dataframe(pd.read_csv(csvp))
    if not images and not os.path.exists(csvp):
        st.caption("Run `python benchmark.py` to fill the results/ folder with plots and a CSV.")

# ----------------------------------------------------------------- tab 5
with tab5:
    st.markdown("""
**Problem.** Find the best route from an emergency location to the nearest suitable hospital in a city road
network (graph: intersections = vertices, roads = weighted edges), with road blockages.

**How to use.** Pick a data source, set ambulance location, hospitals, blocked roads and weight mode,
press *Find route*. If you change any setting afterwards, press *Find route* again.

| Algorithm | Best | Average | Worst | Space |
|---|---|---|---|---|
| Dijkstra (array) | O(V^2) | O(V^2) | O(V^2) | O(V) |
| Dijkstra (binary heap) | O(V log V) | O((V + E) log V) | O((V + E) log V) | O(V + E) |
| Bellman-Ford | O(E) (early stop) | O(V*E) | O(V*E) | O(V) |
| BFS / DFS / components | O(V + E) | O(V + E) | O(V + E) | O(V) |
| Min-heap push / pop | O(1) | O(log n) | O(log n) | - |

**Team.** Student 1: graph and BFS/DFS. Student 2: Dijkstra, heap, benchmarks. Student 3: UI, visualisation, report.
""")
