
import csv

TRAFFIC_FACTOR = {"low": 1.0, "medium": 1.5, "high": 2.5}
VALID_TYPES = {"hospital", "junction", "landmark"}


class Graph:
    def __init__(self):
        self.locations = {}          # id -> {"name", "type", "x", "y"}
        self.adj = {}                # id -> {neighbour_id: road_dict}
        self.blocked = set()         # set of frozenset({u, v})
        self.weight_mode = "distance"  # 'distance' | 'time' | 'combined'

    # ---------- building ----------
    def add_location(self, lid, name, ltype="junction", x=0.0, y=0.0):
        """Add a location (node)."""
        self.locations[lid] = {"name": name, "type": ltype, "x": x, "y": y}
        self.adj.setdefault(lid, {})

    def add_road(self, u, v, distance, time, traffic="low"):
        """Add a two-way road. Raises ValueError on invalid input."""
        if u not in self.adj or v not in self.adj:
            raise ValueError(f"Unknown location in road {u}-{v}")
        if u == v:
            raise ValueError("Self-loop roads are not allowed")
        if distance < 0 or time < 0:
            raise ValueError("Dijkstra needs non-negative weights")
        if traffic not in TRAFFIC_FACTOR:
            raise ValueError(f"Unknown traffic level '{traffic}'")
        road = {"distance": distance, "time": time, "traffic": traffic}
        self.adj[u][v] = road
        self.adj[v][u] = road

    def add_road_keep_shorter(self, u, v, d, t, traffic="low", where=""):
        """Add a road; if it already exists keep the shorter one and warn.

        Public method (used by load_from_csv, from_table and the UI).
        """
        if u in self.adj and v in self.adj[u]:
            print(f"Warning: {where} duplicate road {u}-{v}, keeping the shorter one")
            if self.adj[u][v]["distance"] <= d:
                return
        self.add_road(u, v, d, t, traffic)

    # kept so older code that used the private name still works
    _add_road_keep_shorter = add_road_keep_shorter

    # ---------- blocked roads ----------
    def block_road(self, u, v):
        self.blocked.add(frozenset((u, v)))

    def unblock_road(self, u, v):
        self.blocked.discard(frozenset((u, v)))

    # ---------- queries ----------
    def weight(self, road):
        """Edge weight according to weight_mode."""
        if self.weight_mode == "distance":
            return road["distance"]
        if self.weight_mode == "time":
            return road["time"]
        return road["time"] * TRAFFIC_FACTOR[road["traffic"]]  # combined

    def neighbors(self, u):
        """Yield (v, weight) for every NON-blocked road leaving u."""
        for v, road in self.adj[u].items():
            if frozenset((u, v)) not in self.blocked:
                yield v, self.weight(road)

    def hospitals(self):
        """List of ids whose type is 'hospital'."""
        return [i for i, d in self.locations.items() if d["type"] == "hospital"]

    def num_vertices(self):
        return len(self.adj)

    def num_edges(self):
        return sum(len(n) for n in self.adj.values()) // 2

    def to_matrix(self):
        """Return (ids, matrix). Only used in the report to show V^2 cells."""
        ids = sorted(self.adj)
        idx = {v: i for i, v in enumerate(ids)}
        m = [[0] * len(ids) for _ in ids]
        for u in self.adj:
            for v, road in self.adj[u].items():
                m[idx[u]][idx[v]] = road["distance"]
        return ids, m


def load_from_csv(locations_path, roads_path, require_hospital=True):
    """Load a city from two CSV files with validation.

    Raises ValueError with file name and line number on bad data.
    """
    g = Graph()
    with open(locations_path, newline="", encoding="utf-8") as f:
        for n, row in enumerate(csv.DictReader(f), start=2):
            try:
                lid = int(row["id"])
                x, y = float(row["x"]), float(row["y"])
            except (ValueError, TypeError, KeyError):
                raise ValueError(f"{locations_path} line {n}: bad id/x/y")
            name = (row.get("name") or "").strip()
            ltype = (row.get("type") or "").strip().lower()
            if not name:
                raise ValueError(f"{locations_path} line {n}: empty name")
            if ltype not in VALID_TYPES:
                raise ValueError(f"{locations_path} line {n}: unknown type '{ltype}'")
            if lid in g.locations:
                raise ValueError(f"{locations_path} line {n}: duplicate id {lid}")
            g.add_location(lid, name, ltype, x, y)

    with open(roads_path, newline="", encoding="utf-8") as f:
        for n, row in enumerate(csv.DictReader(f), start=2):
            try:
                u, v = int(row["from"]), int(row["to"])
                d, t = float(row["distance_km"]), float(row["time_min"])
            except (ValueError, TypeError, KeyError):
                raise ValueError(f"{roads_path} line {n}: bad number")
            traffic = (row.get("traffic") or "").strip().lower()
            if u not in g.locations or v not in g.locations:
                raise ValueError(f"{roads_path} line {n}: unknown location in road {u}-{v}")
            if d < 0 or t < 0:
                raise ValueError(f"{roads_path} line {n}: negative distance or time")
            if traffic not in TRAFFIC_FACTOR:
                raise ValueError(f"{roads_path} line {n}: unknown traffic '{traffic}'")
            g.add_road_keep_shorter(u, v, d, t, traffic, where=f"{roads_path} line {n}:")

    if require_hospital and not g.hospitals():
        raise ValueError("City has no hospital")
    return g


def from_table(rows, locations=None, require_hospital=False):
    """Build a graph from tables typed into the UI (Student 3).

    rows      : (from, to, distance, time, traffic) tuples, one per road.
    locations : optional (id, name, type, x, y) tuples. Needed if the user
                wants to mark hospitals; type must be hospital, junction or
                landmark. Locations that appear only in `rows` are created
                automatically as junctions named after their id.
    require_hospital : raise ValueError if the city has no hospital.

    Raises ValueError with a clear message on invalid input.
    """
    g = Graph()
    for i, (lid, name, ltype, x, y) in enumerate(locations or [], start=1):
        ltype = str(ltype).strip().lower()
        if lid in g.locations:
            raise ValueError(f"location row {i}: duplicate id {lid}")
        if not str(name).strip():
            raise ValueError(f"location row {i}: empty name")
        if ltype not in VALID_TYPES:
            raise ValueError(f"location row {i}: unknown type '{ltype}'")
        g.add_location(lid, str(name).strip(), ltype, float(x), float(y))
    for i, (u, v, d, t, traffic) in enumerate(rows, start=1):
        for node in (u, v):
            if node not in g.locations:
                g.add_location(node, str(node))
        try:
            g.add_road_keep_shorter(u, v, float(d), float(t),
                                    str(traffic).strip().lower(), where=f"road row {i}:")
        except ValueError as e:
            raise ValueError(f"road row {i}: {e}")
    if require_hospital and not g.hospitals():
        raise ValueError("City has no hospital")
    return g
