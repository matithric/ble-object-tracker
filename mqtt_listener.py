"""
Subscribes to ble_tracker/<node_id>/scan and maintains a live table of
the most recent reading per (node, target_mac).

Expected message payload (JSON), published by each ESP32 per scan:
{
  "target": "AA:BB:CC:DD:EE:FF",
  "rssi": -67
}

The node_id is taken from the topic itself, e.g. ble_tracker/node1/scan.
Adjust this if your ESP32 sketch publishes a different shape.
"""

import json
import time
import threading
import paho.mqtt.client as mqtt

from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, READING_TIMEOUT_S


class ReadingsStore:
    """Thread-safe store of latest RSSI readings: {target: {node: (rssi, timestamp)}}"""

    def __init__(self):
        self._lock = threading.Lock()
        self._data = {}

    def update(self, node_id, target, rssi):
        with self._lock:
            self._data.setdefault(target, {})[node_id] = (rssi, time.time())

    def fresh_readings_for(self, target, timeout=READING_TIMEOUT_S):
        """Return {node_id: rssi} for readings newer than `timeout` seconds."""
        now = time.time()
        with self._lock:
            entries = self._data.get(target, {})
            return {
                node: rssi
                for node, (rssi, ts) in entries.items()
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
            node_id = msg.topic.split("/")[1]
            payload = json.loads(msg.payload.decode())
            target = payload["target"]
            rssi = float(payload["rssi"])
            store.update(node_id, target, rssi)
        except (IndexError, KeyError, ValueError, json.JSONDecodeError) as e:
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
