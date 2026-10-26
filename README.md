# BLE Object Tracker

An indoor tracking project using ESP32 receivers, Bluetooth Low Energy, and a live Python dashboard.

Three fixed ESP32 receivers estimate the distance to one BLE target from its signal
strength. They publish readings over MQTT, and Python uses trilateration to estimate
the target's position in 2D.

## How it works

```text
BLE target → ESP32 receivers → MQTT broker → Python dashboard
```

## Tech Stack

- **Hardware:** three BLE-capable ESP32 boards and a BLE target
- **Firmware:** Arduino C++
- **Desktop:** Python, NumPy, Matplotlib, and Paho MQTT
- **Messaging:** Mosquitto MQTT broker

## Getting started

1. Configure the sketch in `esp32_firmware/` with your Wi-Fi, broker address,
   target BLE address, and a unique ID and position for each receiver. Upload it to each ESP32.
2. Start Mosquitto on your local network.
3. Update the broker address and receiver positions in `python_dashboard/config.py`.
4. From the repository root, install the dependencies and start the dashboard:

```bash
python -m pip install -r requirements.txt
cd python_dashboard
python dashboard.py
```

The broker must be reachable by both the ESP32 receivers and the Python client.
Keep Wi-Fi credentials out of published files.

## Limitations

This prototype tracks one target in 2D. Walls, furniture, and device orientation
affect signal strength, so calibration is needed and positions are approximate.

## Future improvements

- Improve calibration with measurements at several known distances.
- Compare filtering methods to reduce position jitter.
- Evaluate accuracy across different receiver placements.
