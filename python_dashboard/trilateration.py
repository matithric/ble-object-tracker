"""Convert RSSI to distance and estimate a 2D position."""

import numpy as np
from config import TX_POWER, PATH_LOSS_EXPONENT


def rssi_to_distance(rssi, tx_power=TX_POWER, n=PATH_LOSS_EXPONENT):
    """Convert RSSI to an estimated distance in meters."""
    return 10 ** ((tx_power - rssi) / (10 * n))


def trilaterate(node_positions, distances):
    """Estimate (x, y) from at least three receiver positions and matching distances."""
    if len(node_positions) < 3:
        raise ValueError("Need at least 3 nodes for a 2D fix")

    positions = np.array(node_positions, dtype=float)
    dists = np.array(distances, dtype=float)

    # Subtract the last circle equation to remove the squared position terms.
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

    # Use all available receivers to estimate the position.
    solution, *_ = np.linalg.lstsq(A, b, rcond=None)
    return float(solution[0]), float(solution[1])


if __name__ == "__main__":
    # Check the estimate against a known point.
    nodes = [(0, 0), (3, 0), (1.5, 2.6)]
    true_point = (1.5, 1.0)
    dists = [
        np.hypot(true_point[0] - x, true_point[1] - y) for x, y in nodes
    ]
    est = trilaterate(nodes, dists)
    print(f"True: {true_point}, Estimated: {est}")
