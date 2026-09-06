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
from trilateration import rssi_to_distance, trilaterate


def compute_positions(store: ReadingsStore):
    """Returns {target: (x, y)} for every target with enough fresh nodes."""
    positions = {}
    for target in store.known_targets():
        readings = store.fresh_readings_for(target)
        usable = {n: r for n, r in readings.items() if n in NODE_POSITIONS}
        if len(usable) < MIN_NODES_FOR_FIX:
            continue

        node_pts = [NODE_POSITIONS[n] for n in usable]
        dists = [rssi_to_distance(r) for r in usable.values()]
        try:
            positions[target] = trilaterate(node_pts, dists)
        except Exception as e:
            print(f"[dashboard] fit failed for {target}: {e}")
    return positions


def run_dashboard():
    store = ReadingsStore()
    mqtt_client = start_listener(store)

    fig, ax = plt.subplots(figsize=(7, 6))
    node_xs = [p[0] for p in NODE_POSITIONS.values()]
    node_ys = [p[1] for p in NODE_POSITIONS.values()]

    def update(frame):
        ax.clear()

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
            ax.annotate(mac[-8:], (x, y), textcoords="offset points", xytext=(5, -10), fontsize=8)

        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.set_title(f"BLE Tracker — {len(targets)} target(s) tracked")
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.3)
        ax.set_aspect("equal", adjustable="box")

        margin = 1.5
        all_x = node_xs + [p[0] for p in targets.values()]
        all_y = node_ys + [p[1] for p in targets.values()]
        if ROOM_POLYGON is not None:
            all_x += [p[0] for p in ROOM_POLYGON]
            all_y += [p[1] for p in ROOM_POLYGON]
        ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
        ax.set_ylim(min(all_y) - margin, max(all_y) + margin)

    ani = animation.FuncAnimation(fig, update, interval=1000, cache_frame_data=False)
    plt.tight_layout()
    plt.show()

    mqtt_client.loop_stop()


if __name__ == "__main__":
    run_dashboard()
