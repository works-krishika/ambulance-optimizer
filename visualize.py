"""visualize.py - Student 3. Drawing only; no algorithm work happens here."""
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

MAX_DRAW_NODES = 200  # bigger graphs are reported as text, not drawn


def draw_city(g, path=None, title="", settled=None, label_roads=True,
              start=None, blocked=None):
    """Draw the city and return a matplotlib Figure.

    path    : list of node ids of the selected route (drawn thick orange)
    settled : set of nodes already finalised by Dijkstra ('Step k' slider)
    start   : ambulance node. It is drawn red even when there is no route.
              (If omitted, the first node of `path` is used.)
    blocked : set of frozenset({u, v}) to draw as blocked. Defaults to
              g.blocked. Pass set() to draw the city without blockages.

    A Figure is created directly (not with pyplot), so figures are freed
    by Python and Streamlit never warns about too many open figures.
    """
    fig = Figure(figsize=(9, 7))
    ax = fig.subplots()
    path = path or []
    settled = settled or set()
    blocked = g.blocked if blocked is None else blocked
    ambulance = start if start is not None else (path[0] if path else None)
    on_path = set(zip(path, path[1:]))
    small = len(g.locations) <= 40

    for u in g.adj:
        for v, road in g.adj[u].items():
            if str(u) >= str(v):
                continue  # each two-way road once
            x = [g.locations[u]["x"], g.locations[v]["x"]]
            y = [g.locations[u]["y"], g.locations[v]["y"]]
            if frozenset((u, v)) in blocked:
                ax.plot(x, y, "r--", lw=1.5, zorder=1)
            elif (u, v) in on_path or (v, u) in on_path:
                ax.plot(x, y, color="orange", lw=4, zorder=2)
            else:
                ax.plot(x, y, color="lightgray", lw=1, zorder=1)
            if label_roads and small:
                ax.annotate(f"{road['distance']:g}", ((x[0] + x[1]) / 2, (y[0] + y[1]) / 2),
                            fontsize=6, color="dimgray", ha="center")

    for lid, d in g.locations.items():
        color = "green" if d["type"] == "hospital" else "steelblue"
        if lid in settled and d["type"] != "hospital":
            color = "gold"
        if lid == ambulance:
            color = "red"  # ambulance
        ax.scatter(d["x"], d["y"], s=120 if small else 25, c=color, zorder=3,
                   edgecolors="white", linewidths=0.8)
        if small:
            ax.annotate(d["name"], (d["x"], d["y"]), fontsize=7,
                        xytext=(4, 4), textcoords="offset points")

    handles = [
        Line2D([], [], marker="o", ls="", color="red", label="Ambulance"),
        Line2D([], [], marker="o", ls="", color="green", label="Hospital"),
        Line2D([], [], marker="o", ls="", color="steelblue", label="Location"),
        Line2D([], [], marker="o", ls="", color="gold", label="Settled (Dijkstra step)"),
        Line2D([], [], color="orange", lw=4, label="Selected route"),
        Line2D([], [], color="red", ls="--", label="Blocked road"),
        Line2D([], [], color="lightgray", lw=1, label="Road"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=7, framealpha=0.9)
    ax.set_title(title)
    ax.axis("off")
    fig.tight_layout()
    return fig
