// Found in example sketches
#define MQTT_MAX_PACKET_SIZE 256  // Reserve space for the JSON payload.
#include <WiFi.h>
#include <PubSubClient.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <PubSubClient.h>

const char* nodeID = "node1";
const float nodeX = 0.0;
const float nodeY = 3.048;
const char* ssid = "wifiName";
const char* wifiPassword = "wifiPassword";

const char* mqttServer = "192.168.1.117";
const int mqttPort = 1883;

int scanTime = 10;
BLEScan* pBLEScan;

WiFiClient espClient;
PubSubClient mqttClient(espClient);

bool haveSmoothedRSSI = false;
float smoothedRSSI = 0;
const float smoothingFactor = 0.2;  // Lower values smooth more but respond more slowly.

void setup() {
  Serial.begin(115200);
  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan();

  WiFi.begin(ssid, wifiPassword);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");

  mqttClient.setServer(mqttServer, mqttPort);
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Connecting to MQTT...");
    if (mqttClient.connect(nodeID)) {
      Serial.println("connected");
    } else {
      delay(2000);
    }
  }
}

void loop() {
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();

  BLEScanResults* foundDevices = pBLEScan->start(scanTime, false);
  Serial.println(foundDevices->getCount());

  for (int i = 0; i < foundDevices->getCount(); i++) {
    BLEAdvertisedDevice device = foundDevices->getDevice(i);
    int rssi = device.getRSSI();

    float txPower = -60;  // RSSI measured at one meter.
    float n = 3.14;       // Calibrate signal loss for the room.
    float distance = pow(10, (txPower - rssi) / (10 * n));

    Serial.print("Device: ");
    Serial.print(device.getAddress().toString().c_str());
    Serial.print(" RSSI: ");
    Serial.println(rssi);
    Serial.print(" Distance: ");
    Serial.println(distance);

    if (device.getAddress().toString() == "macAddress") {
      // Smooth signal fluctuations before estimating distance.
      if (!haveSmoothedRSSI) {
        smoothedRSSI = rssi;
        haveSmoothedRSSI = true;
      } else {
        smoothedRSSI = smoothingFactor * rssi + (1 - smoothingFactor) * smoothedRSSI;
      }
      float smoothedDistance = pow(10, (txPower - smoothedRSSI) / (10 * n));

      Serial.println("MATCH FOUND - attempting publish");
      Serial.print("Smoothed RSSI: ");
      Serial.print(smoothedRSSI);
      Serial.print(" Smoothed Distance: ");
      Serial.println(smoothedDistance);

      char payload[128];
      snprintf(payload, sizeof(payload),
               "{\"node_id\":\"%s\",\"x\":%.2f,\"y\":%.2f,\"distance\":%.2f}",
               nodeID, nodeX, nodeY, smoothedDistance);
      bool result = mqttClient.publish("tracker/distance", payload);
      Serial.print("Publish result: ");
      Serial.println(result ? "SUCCESS" : "FAILED");
    }
  }

  pBLEScan->clearResults();
}
