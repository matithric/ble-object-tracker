"""Broker settings, receiver coordinates, and room layout."""

# MQTT connection
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "tracker/distance"

# Receiver positions in meters, measured from a shared origin.

NODE_POSITIONS = {
    "node1": (0.0, 3.048),
    "node2": (4.914, 3.048),
    "node3": (2.457, 0.0),
}

# Calibration for the offline RSSI conversion helper.

# TX_POWER is the measured RSSI at one meter; n controls signal loss.

TX_POWER = -59
PATH_LOSS_EXPONENT = 2.5

# Ignore readings older than this many seconds.

READING_TIMEOUT_S = 15.0


MIN_NODES_FOR_FIX = 3

# Room corners in perimeter order, in meters. Set to None to hide the outline.


ROOM_POLYGON = [
    (0.0, 3.048),
    (4.914, 3.048),
    (4.914, 0.0),
    (0.711, 0.0),
    (0.711, 1.245),
    (0.0, 1.245),
]
