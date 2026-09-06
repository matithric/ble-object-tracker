"""
RSSI -> distance conversion, and multi-node trilateration via
least-squares (handles >3 nodes and noisy RSSI better than pure
geometric 3-circle intersection).
"""

import numpy as np
from config import TX_POWER, PATH_LOSS_EXPONENT


def rssi_to_distance(rssi, tx_power=TX_POWER, n=PATH_LOSS_EXPONENT):
    """Log-distance path loss model. Returns distance in meters."""
    return 10 ** ((tx_power - rssi) / (10 * n))


def trilaterate(node_positions, distances):
    """
    Estimate (x, y) of a target given known node positions and
    estimated distances from each node.

    node_positions: list of (x, y) tuples, len >= 3
    distances: list of distances (meters), same length/order as node_positions

    Uses linear least squares on the circle-equation differences
    (standard trilateration linearization trick).
    """
    if len(node_positions) < 3:
        raise ValueError("Need at least 3 nodes for a 2D fix")

    positions = np.array(node_positions, dtype=float)
    dists = np.array(distances, dtype=float)

    # Linearize by subtracting the last equation from all others:
    # (x - xi)^2 + (y - yi)^2 = di^2
    x_last, y_last = positions[-1]
    d_last = dists[-1]

    A = []
    b = []
    for (xi, yi), di in zip(positions[:-1], dists[:-1]):
        A.append([2 * (x_last - xi), 2 * (y_last - yi)])
        b.append(
            (di**2 - d_last**2)
            - (xi**2 - x_last**2)
            - (yi**2 - y_last**2)
        )

    A = np.array(A)
    b = np.array(b)

    # Least-squares solve (works even with >3 nodes / overdetermined system)
    solution, *_ = np.linalg.lstsq(A, b, rcond=None)
    return float(solution[0]), float(solution[1])


if __name__ == "__main__":
    # Quick sanity check with a known point
    nodes = [(0, 0), (3, 0), (1.5, 2.6)]
    true_point = (1.5, 1.0)
    dists = [
        np.hypot(true_point[0] - x, true_point[1] - y) for x, y in nodes
    ]
    est = trilaterate(nodes, dists)
    print(f"True: {true_point}, Estimated: {est}")
