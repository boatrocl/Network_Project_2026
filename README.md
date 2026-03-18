# Taste Data Transmission Network (TTN)

## Abstract

Taste Data Transmission Network (TTN) เป็นระบบจำลอง Cyber-Physical System สำหรับการส่งผ่านข้อมูลรสชาติผ่านเครือข่ายคอมพิวเตอร์แบบ End-to-End โครงการนี้พัฒนาขึ้นเพื่อศึกษาหลักการของ Data Communication, IoT Networking และ OSI Layer Interaction ผ่านกรณีศึกษา Internet of Senses

ระบบแปลงข้อมูลรสชาติจากแหล่งกำเนิดให้อยู่ในรูปแบบเวกเตอร์ดิจิทัล จากนั้นส่งผ่านเครือข่ายไร้สายและ IoT Cloud ก่อนนำไปสร้างการตอบสนองทางกายภาพที่ปลายทางแบบ Real-Time

แนวคิดอ้างอิงจากงานวิจัย e-Taste (Science Advances, 2025)

---

## 1. System Overview

TTN จำลองกระบวนการส่งข้อมูลรสชาติผ่าน network pipeline ดังนี้

```
Sensor Patch → ESP32 → WiFi AP → IoT Cloud → WiFi AP → ESP32 → EM Actuator
     SRC          AP1          IOT           AP2          DST
```

ข้อมูลรสชาติถูกนิยามเป็นเวกเตอร์

```
V_taste = [Sweet, Salty, Sour, Bitter, Umami]
```

โดยแต่ละค่าอยู่ในช่วง [0.0, 1.0]

---

## 2. Objectives

1. ศึกษาการทำงานของ OSI Model ผ่านระบบจริง
2. จำลอง End-to-End packet transmission
3. วิเคราะห์ latency, packet loss และ network jitter
4. ผสานระบบ IoT กับ Cyber-Physical Actuation
5. ออกแบบระบบที่มีความปลอดภัยและ Human-in-the-Loop control

---

## 3. System Architecture

### 3.1 Network Nodes

| Node | Function                            |
| ---- | ----------------------------------- |
| SRC  | Sensor acquisition and digitization |
| AP1  | Wireless access point               |
| IOT  | Cloud relay and session control     |
| AP2  | Wireless access point               |
| DST  | Actuation controller                |

### 3.2 OSI Layer Mapping

| Layer           | Role in TTN                   |
| --------------- | ----------------------------- |
| L7 Application  | Serialize taste vector        |
| L6 Presentation | Normalization and compression |
| L5 Session      | Authentication and sequencing |
| L4 Transport    | UDP transmission              |
| L3 Network      | IP routing                    |
| L2 Data Link    | WiFi frame + integrity check  |
| L1 Physical     | 2.4 GHz wireless transmission |

---

## 4. Methodology

### 4.1 Sensory Digitization

Sensor readings ถูกแปลงเป็น:

```
float32[5] taste vector
```

### 4.2 Transmission Protocol

* Transport Protocol: UDP
* Ports: 55100 → 7775
* Wireless Standard: IEEE 802.11n / ESPNOW

### 4.3 Security Mechanisms

* CRC-32 Frame Integrity
* HMAC-SHA256 Authentication
* Sequence Number Validation
* MAC Address Filtering

### 4.4 Actuation Model

ค่ารสชาติถูกแปลงเป็น PWM duty cycle เพื่อควบคุม EM Minipump actuator

---

## 5. Software Components

| Component                  | Description                     |
| -------------------------- | ------------------------------- |
| index.html                 | Interactive web-based simulator |
| ttn_demo_gui.py            | Terminal network simulation     |
| Architecture Specification | System design documentation     |
| Implementation Plan        | Development roadmap             |

---

## 6. Simulation Features

* End-to-End packet visualization
* OSI encapsulation walkthrough
* Network profile comparison
* Taste vector monitoring
* Security validation dashboard
* Human-in-the-Loop control interface

---

## 7. Experimental Evaluation

### Network Profiles

| Profile          | Latency  | Loss | Jitter  |
| ---------------- | -------- | ---- | ------- |
| ESPNOW Local     | ~5 ms    | 0.5% | ±1 ms   |
| WiFi 802.11n     | ~15 ms   | 1.5% | ±5 ms   |
| IoT Cloud (Poor) | ~2000 ms | 10%  | ±500 ms |

### Example Result

```
Average ESPNOW latency: 4.7 ms
Cloud poor latency:     1959 ms
```

---

## 8. Safety and Control Design

* Salty concentration capped at 0.25
* Emergency shutdown < 10 ms
* Cartridge level monitoring
* Session timeout protection

ระบบออกแบบให้รองรับ Human-in-the-Loop (HITL) เพื่อเพิ่มความปลอดภัยของผู้ใช้งาน

---

## 9. Repository Usage

### Run Web Simulator

```
python -m http.server
```

Open:

```
http://localhost:8000
```

### Run Terminal Simulation

```
python ttn_demo_gui.py
```

---

## 10. Course Information

Course: Data Communication and Computer Networks
Project: Taste Data Transmission Network (TTN)
Version: 4.0

---

## 11. Team Members

| Name                   | Role                |
| ---------------------- | ------------------- |
| กรกฎ พรมทอง            | Architecture Lead   |
| วัชรวิศว์ น้อยเมล์     | Network Development |
| จิณณวัตร โพธิ์ศรีทอง   | UI Integration      |
| สรวิชญ์ ทะมานันท์      | Hardware Prototype  |
| ปกรณ์เกียรติ ศรีจันทร์ | Documentation       |

---

## 12. References

1. Chen, X. et al. (2025). e-Taste: Remote Taste Interface. Science Advances.
2. IEEE Standard for Wireless LAN (IEEE 802.11).
3. Postel, J. User Datagram Protocol, RFC 768.
4. Espressif Systems. ESP32-C3 Technical Reference Manual.
5. Lee, E. A. Cyber-Physical Systems: Design Challenges.

---

## 13. Educational Contribution

โครงการนี้แสดงให้เห็นการเชื่อมโยงระหว่าง

* Computer Networks
* IoT Systems
* Embedded Systems
* Cyber-Physical Interaction

ผ่านกรณีศึกษาเชิงปฏิบัติที่สามารถสังเกตพฤติกรรมของ network stack ได้อย่างชัดเจน
