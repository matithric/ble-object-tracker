# BLE Object Tracker
Local indoor position system using ESP32 nodes and BLE RSSI trilateration, with a live python dashboard.

## Demo
<img width="1082" height="809" alt="image" src="https://github.com/user-attachments/assets/0a7de196-40a8-446c-9d22-f1dbea6dfbe6" />
<img width="1081" height="813" alt="image" src="https://github.com/user-attachments/assets/78d09aef-70a3-41b0-a3f7-e3cfe0a2fadd" />
<img width="1069" height="804" alt="image" src="https://github.com/user-attachments/assets/88322252-8736-4ff9-b6a3-ca565d5dc33e" />

## How it works
- 3 ESP32 nodes scan for a target BLE device and estimate the distance via RSSI
- Distances are published over MQTT (Mosquitto broker)
- A python script subscribes, calculates the position, and plots it live on a diagram

## Tech stack
- C++ (ESP32/Arduino)
- Python (paho-mqtt, matplotlib)
- MQTT (Mosquitto)

## Architecture
ESP32 nodes → MQTT broker → Python listener → trilateration → live dashboard

## Setup
1. Flash `node.ino` to each ESP32 (update the `nodeID`, `nodeX`, `nodeY`, `txPower`, and `n`)
2. Run Mosquitto broker
3. `pip install -r requirements.txt`
4. `python dashboard.py`

## Known limitations
- RSSI-based distance estimation has inherent noise (~0.5-1.5m accuracy)
- Two-point calibration is rough; multi-point regression would improve accuracy
- Only 3 nodes are used, which constrains position to a 2D plane (x, y) — no height/z-axis tracking

## Improvements
- Kalman filtering instead of simple exponential smoothing
- Multi-point RSSI calibration per node meaning (would help find a more accurate txpower and n value)
- Add a 4th node (or more) at a different height to enable full 3D (x, y, z) positioning
