# Smart Emergency Ambulance Route Optimizer

DAA Lab Mini Project 1 - B.Tech Cyber Security, Section C

A working application that finds the best route for an ambulance from an
emergency location to the nearest hospital in a city road network. The city is a
weighted graph (intersections = vertices, roads = edges; weights are distance,
time, or time x traffic factor). Roads can be blocked to simulate closures.

## Team

| Student | Role | Files |
|---|---|---|
| Student 1 - <name> | Graph & Data Engineer | `graph.py`, `generator.py`, `algorithms/bfs_dfs.py`, `data/`, `tests/` |
| Student 2 - <name> | Algorithm & Analysis Engineer | `algorithms/min_heap.py`, `dijkstra.py`, `bellman_ford.py`, `benchmark.py` |
| Student 3 - <name> | UI, Visualization & Documentation | `app.py`, `visualize.py`, `report/` |

## Install

```bash
git clone <repo-url>
cd ambulance-optimizer
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Run the tests

```bash
python -m pytest -v
```

## What the app does

- **Data sources:** sample city (Jaipur, 25 locations), upload CSV, enter manually, random city (up to 5,000 locations)
- **Algorithms (all written from scratch):** Dijkstra with a binary min-heap, Dijkstra with an array, Bellman-Ford, BFS, iterative DFS, connected components
- **Features:** nearest-hospital route, blocked-road simulation, step-by-step Dijkstra table, hospital ranking, before/after blockage maps, zones without a hospital, performance comparison

## Data format

`data/city_locations.csv`: `id,name,type,x,y` - `type` is `hospital`, `junction` or `landmark`; `x,y` are map coordinates used only for drawing.

`data/city_roads.csv`: `from,to,distance_km,time_min,traffic` - `traffic` is `low`, `medium` or `high`; roads are two-way.

## Folder structure

```
app.py              Streamlit user interface
graph.py            Graph class, CSV loader with validation, from_table()
generator.py        random connected city generator (sparse and dense)
visualize.py        drawing the map and route
benchmark.py        timing experiments and plots
algorithms/         bfs_dfs.py, min_heap.py, dijkstra.py, bellman_ford.py
data/               real city, 6-node hand-solved city, boundary and invalid cases
tests/              pytest test cases
results/            benchmark.csv and plots
report/             report, slides, screenshots
```
