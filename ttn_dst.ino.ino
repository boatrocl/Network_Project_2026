/*
==========================================================
 TTN — ESP32 Destination Node (FINAL DEMO VERSION)
 Taste Data Transmission Network
----------------------------------------------------------
 Receive UDP Taste Packet -> Decode -> PWM Output
==========================================================
*/

#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>

/* ================= WIFI CONFIG ================= */

const char* ssid     = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";

/* ================= NETWORK ================= */

WiFiUDP udp;
const int listenPort = 7775;

/* ================= ACTUATOR ================= */

const int actuatorPin = 5;   // ต่อ LED หรือ Pump
const int pwmChannel  = 0;
const int pwmFreq     = 5000;
const int pwmRes      = 8;

/* ================= SETUP ================= */

void setup() {

  Serial.begin(115200);
  delay(1000);

  Serial.println("\nTTN Destination Node Starting...");

  pinMode(actuatorPin, OUTPUT);

  ledcSetup(pwmChannel, pwmFreq, pwmRes);
  ledcAttachPin(actuatorPin, pwmChannel);

  /* WiFi Connect */
  WiFi.begin(ssid, password);

  Serial.print("Connecting WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConnected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  udp.begin(listenPort);

  Serial.println("UDP Listener Ready");
}

/* ================= APPLY TASTE ================= */

void applyTaste(float sweet,
                float salty,
                float sour,
                float bitter,
                float umami)
{
  // หา dominant taste (เหมือน Python simulator)
  float maxVal = sweet;
  String dominant = "Sweet";

  if (salty > maxVal) { maxVal = salty; dominant="Salty"; }
  if (sour  > maxVal) { maxVal = sour;  dominant="Sour"; }
  if (bitter> maxVal) { maxVal = bitter;dominant="Bitter"; }
  if (umami > maxVal) { maxVal = umami; dominant="Umami"; }

  int duty = maxVal * 255;

  ledcWrite(pwmChannel, duty);

  Serial.println("----- ACTUATION -----");
  Serial.print("Dominant Taste: ");
  Serial.println(dominant);

  Serial.print("PWM Duty: ");
  Serial.println(duty);
}

/* ================= LOOP ================= */

void loop() {

  int packetSize = udp.parsePacket();

  if (packetSize) {

    char incoming[256];

    int len = udp.read(incoming, 255);
    if (len > 0) incoming[len] = 0;

    Serial.println("\nPacket Received:");
    Serial.println(incoming);

    StaticJsonDocument<256> doc;

    DeserializationError err =
        deserializeJson(doc, incoming);

    if (err) {
      Serial.println("JSON Parse Failed");
      return;
    }

    float sweet  = doc["sweet"]  | 0.0;
    float salty  = doc["salty"]  | 0.0;
    float sour   = doc["sour"]   | 0.0;
    float bitter = doc["bitter"] | 0.0;
    float umami  = doc["umami"]  | 0.0;

    applyTaste(sweet, salty, sour, bitter, umami);
  }
}