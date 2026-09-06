"""
Central config for the BLE tracker Python side.
Edit NODE_POSITIONS and RSSI calibration constants once you've
measured them off your 3 ESP32 nodes.
"""

# MQTT broker (Mosquitto)
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "tracker/distance"   # all 3 nodes publish node_id/x/y/distance to this single topic

# Fixed (x, y) positions of each ESP32 node in meters, relative to an origin you pick.
# Replace with your real measured layout.
NODE_POSITIONS = {
    "node1": (0.0, 3.048),      # door
    "node2": (4.914, 3.048),    # in n out
    "node3": (2.457, 0.0),      # soccer
}

# RSSI -> distance calibration (log-distance path loss model):
#   distance = 10 ** ((txPower - rssi) / (10 * n))
# txPower: measured RSSI at 1 meter (dBm), negative number, e.g. -59
# n: path loss exponent, typically 2.0 (free space) to 4.0 (indoors/obstructed)
TX_POWER = -59
PATH_LOSS_EXPONENT = 2.5

# How long (seconds) a node's last reading for a given target is considered "fresh"
# before it's dropped from trilateration.
READING_TIMEOUT_S = 15.0

# Minimum number of nodes with fresh readings needed to attempt a position fix.
MIN_NODES_FOR_FIX = 3

# Room outline as a list of (x, y) corner points in meters, walked in order
# around the perimeter. Drawn on the dashboard as a reference outline.
# Set to None to hide it.
ROOM_POLYGON = [
    (0.0, 3.048),      # top-left (node1 / door)
    (4.914, 3.048),    # top-right (node2 / in n out)
    (4.914, 0.0),      # bottom-right
    (0.711, 0.0),      # bottom edge, right side of notch
    (0.711, 1.245),    # notch corner
    (0.0, 1.245),      # notch corner, back to left wall
]
