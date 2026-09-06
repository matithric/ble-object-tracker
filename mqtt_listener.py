"""
Subscribes to tracker/distance and maintains a live table of the most
recent distance reading per node, for the single fixed BLE target the
ESP32 sketches are hardcoded to look for.

Expected message payload (JSON), published by each ESP32 per scan:
{
  "node_id": "node1",
  "x": 0.00,
  "y": 3.05,
  "distance": 2.93
}

The ESP32 already converts RSSI to distance on-device (see the sketch's
txPower/n path-loss calculation), so this listener stores distance
directly rather than RSSI. There's only ever one target tracked system-
wide (matched by hardcoded MAC in the sketch), so readings are stored
under a single fixed key instead of per-target-MAC.
"""
import json
import time
import threading
import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, READING_TIMEOUT_S

TARGET_NAME = "target"  # only one target is ever tracked, so use a fixed key

class ReadingsStore:
    """Thread-safe store of latest distance readings: {target: {node: (distance, timestamp)}}"""
    def __init__(self):
        self._lock = threading.Lock()
        self._data = {}

    def update(self, node_id, distance):
        with self._lock:
            self._data.setdefault(TARGET_NAME, {})[node_id] = (distance, time.time())

    def fresh_readings_for(self, target, timeout=READING_TIMEOUT_S):
        """Return {node_id: distance} for readings newer than `timeout` seconds."""
        now = time.time()
        with self._lock:
            entries = self._data.get(target, {})
            return {
                node: distance
                for node, (distance, ts) in entries.items()
                if now - ts <= timeout
            }

    def known_targets(self):
        with self._lock:
            return list(self._data.keys())

def start_listener(store: ReadingsStore):
    """Starts the MQTT client on a background thread. Returns the client."""
    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print(f"[mqtt] connected to {MQTT_BROKER}:{MQTT_PORT}")
            client.subscribe(MQTT_TOPIC)
        else:
            print(f"[mqtt] connection failed, rc={rc}")

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            node_id = payload["node_id"]
            distance = float(payload["distance"])
            store.update(node_id, distance)
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            print(f"[mqtt] skipped malformed message on {msg.topic}: {e}")

    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=30)
    client.loop_start()
    return client

if __name__ == "__main__":
    # Standalone test: just print incoming readings
    store = ReadingsStore()
    client = start_listener(store)
    try:
        while True:
            time.sleep(2)
            for target in store.known_targets():
                print(target, store.fresh_readings_for(target))
    except KeyboardInterrupt:
        client.loop_stop()