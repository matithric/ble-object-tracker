"""
Live dashboard: plots the 3 fixed ESP32 node positions and the
estimated (x, y) position of each detected BLE target, refreshed
on a timer via matplotlib animation.

Run with the MQTT broker already up and at least one ESP32 publishing.
"""
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as patches
from config import NODE_POSITIONS, MIN_NODES_FOR_FIX, ROOM_POLYGON
from mqtt_listener import ReadingsStore, start_listener
from trilateration import trilaterate  # rssi_to_distance unused: ESP32 sends distance directly


def compute_positions(store: ReadingsStore):
    """Returns {target: (x, y)} for every target with enough fresh nodes."""
    positions = {}
    for target in store.known_targets():
        readings = store.fresh_readings_for(target)
        usable = {n: r for n, r in readings.items() if n in NODE_POSITIONS}
        if len(usable) < MIN_NODES_FOR_FIX:
            continue  # not enough nodes reporting yet, skip this target for now

        node_pts = [NODE_POSITIONS[n] for n in usable]
        dists = list(usable.values())  # already distances, not RSSI - no conversion needed
        try:
            positions[target] = trilaterate(node_pts, dists)
        except Exception as e:
            print(f"[dashboard] fit failed for {target}: {e}")
    return positions


def run_dashboard():
    store = ReadingsStore()
    mqtt_client = start_listener(store)  # runs on its own background thread
    fig, ax = plt.subplots(figsize=(7, 6))
    node_xs = [p[0] for p in NODE_POSITIONS.values()]
    node_ys = [p[1] for p in NODE_POSITIONS.values()]

    def update(frame):
        ax.clear()  # redraw from scratch each tick, otherwise frames stack on top of each other

        if ROOM_POLYGON is not None:
            room = patches.Polygon(
                ROOM_POLYGON, closed=True,
                linewidth=2, edgecolor="steelblue", facecolor="none",
                label="Room outline",
            )
            ax.add_patch(room)

        ax.scatter(node_xs, node_ys, c="black", marker="^", s=100, label="ESP32 nodes")
        for name, (x, y) in NODE_POSITIONS.items():
            ax.annotate(name, (x, y), textcoords="offset points", xytext=(5, 5))

        targets = compute_positions(store)
        for mac, (x, y) in targets.items():
            ax.scatter(x, y, c="red", marker="o", s=80)
            # mac[-8:]: last 8 chars of the target key (in this project it's always "target",
            # since there's only ever one fixed BLE device tracked)
            ax.annotate(mac[-8:], (x, y), textcoords="offset points", xytext=(5, -10), fontsize=8)

        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.set_title(f"BLE Tracker — {len(targets)} target(s) tracked")
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.3)
        ax.set_aspect("equal", adjustable="box")  # keep room proportions accurate, not stretched

        # auto-fit the view to whatever's currently on screen, with a margin
        margin = 1.5
        all_x = node_xs + [p[0] for p in targets.values()]
        all_y = node_ys + [p[1] for p in targets.values()]
        if ROOM_POLYGON is not None:
            all_x += [p[0] for p in ROOM_POLYGON]
            all_y += [p[1] for p in ROOM_POLYGON]
        ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
        ax.set_ylim(min(all_y) - margin, max(all_y) + margin)

    # interval=1000: redraw every 1s. cache_frame_data=False: don't retain every past
    # frame in memory, since this runs indefinitely
    ani = animation.FuncAnimation(fig, update, interval=1000, cache_frame_data=False)
    plt.tight_layout()
    plt.show()  # blocks until the plot window is closed
    mqtt_client.loop_stop()


if __name__ == "__main__":
    run_dashboard()
