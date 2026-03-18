/*
==========================================================
 TTN — ESP32 Destination Node (FINAL DEMO VERSION)
 Taste Data Transmission Network
==========================================================
*/

#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>

// WiFi Configuration for Wokwi
const char* ssid     = "Wokwi-GUEST";
const char* password = "";

// Network Configuration
WiFiUDP udp;
const int listenPort = 7775;

// Actuator Configuration
const int actuatorPin = 5;
const int pwmChannel  = 0;
const int pwmFreq     = 5000;
const int pwmRes      = 8;

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n=================================");
  Serial.println("TTN DESTINATION NODE STARTING...");
  Serial.println("=================================");
  
  pinMode(actuatorPin, OUTPUT);
  ledcSetup(pwmChannel, pwmFreq, pwmRes);
  ledcAttachPin(actuatorPin, pwmChannel);
  ledcWrite(pwmChannel, 0);
  
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi Connected!");
    Serial.print("  IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n✗ WiFi Failed!");
  }
  
  udp.begin(listenPort);
  Serial.print("✓ UDP Port: ");
  Serial.println(listenPort);
  Serial.println("=================================\n");
  Serial.println("Ready to receive taste data...\n");
}

void applyTaste(float sweet, float salty, float sour, float bitter, float umami) {
  // Find dominant taste
  float maxVal = sweet;
  String dominant = "Sweet";
  
  if (salty > maxVal) { maxVal = salty; dominant = "Salty"; }
  if (sour > maxVal) { maxVal = sour; dominant = "Sour"; }
  if (bitter > maxVal) { maxVal = bitter; dominant = "Bitter"; }
  if (umami > maxVal) { maxVal = umami; dominant = "Umami"; }
  
  // Convert to PWM duty cycle (0-255)
  int duty = constrain(maxVal * 255, 0, 255);
  ledcWrite(pwmChannel, duty);
  
  // Display results
  Serial.println("╔════════════════════════════╗");
  Serial.println("║     TASTE DATA RECEIVED    ║");
  Serial.println("╠════════════════════════════╣");
  Serial.print("║ Sweet:  "); Serial.print(sweet, 2); 
  Serial.println("                   ║");
  Serial.print("║ Salty:  "); Serial.print(salty, 2); 
  Serial.println("                   ║");
  Serial.print("║ Sour:   "); Serial.print(sour, 2); 
  Serial.println("                   ║");
  Serial.print("║ Bitter: "); Serial.print(bitter, 2); 
  Serial.println("                   ║");
  Serial.print("║ Umami:  "); Serial.print(umami, 2); 
  Serial.println("                   ║");
  Serial.println("╠────────────────────────────╣");
  Serial.print("║ DOMINANT: "); Serial.print(dominant);
  Serial.println("            ║");
  Serial.print("║ PWM Duty: "); Serial.print(duty);
  Serial.print(" (");
  Serial.print((duty * 100) / 255);
  Serial.println("%)          ║");
  
  // LED bar graph
  Serial.print("║ LED: ");
  int barLength = map(duty, 0, 255, 0, 16);
  for (int i = 0; i < 16; i++) {
    if (i < barLength) Serial.print("█");
    else Serial.print("░");
  }
  Serial.println(" ║");
  Serial.println("╚════════════════════════════╝\n");
}

void loop() {
  int packetSize = udp.parsePacket();
  
  if (packetSize) {
    char incoming[256];
    int len = udp.read(incoming, 255);
    
    if (len > 0) {
      incoming[len] = 0;
      
      Serial.println("\n📦 PACKET RECEIVED!");
      Serial.print("From: ");
      Serial.print(udp.remoteIP());
      Serial.print(":");
      Serial.println(udp.remotePort());
      Serial.print("Data: ");
      Serial.println(incoming);
      
      StaticJsonDocument<256> doc;
      DeserializationError err = deserializeJson(doc, incoming);
      
      if (err) {
        Serial.println("❌ JSON Error!");
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
  
  static unsigned long lastStatus = 0;
  if (millis() - lastStatus > 5000) {
    lastStatus = millis();
    Serial.print("⏳ Waiting for UDP on port ");
    Serial.print(listenPort);
    Serial.print(" (");
    Serial.print(WiFi.localIP());
    Serial.println(")");
  }
  
  delay(100);
}