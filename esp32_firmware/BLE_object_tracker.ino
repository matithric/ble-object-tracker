// Found in example sketches
#define MQTT_MAX_PACKET_SIZE 256  // default (128) is too small for the JSON payload
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
const float smoothingFactor = 0.2;  // lower = smoother/slower to react, higher = more responsive/jumpier

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

    float txPower = -60;  // represents what rssi would the device read at 1 meter away
    float n = 3.14;       // how much the signal weakens travelling through air, increase if passing through furniture
    float distance = pow(10, (txPower - rssi) / (10 * n));

    Serial.print("Device: ");
    Serial.print(device.getAddress().toString().c_str());  // turns the bluetooth address to text to be printed
    Serial.print(" RSSI: ");
    Serial.println(rssi);
    Serial.print(" Distance: ");
    Serial.println(distance);

    if (device.getAddress().toString() == "macAddress") {
      // Exponential smoothing to reduce RSSI jitter
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
