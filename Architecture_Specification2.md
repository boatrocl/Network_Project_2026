# Architecture Specification: Tastes Through Network (TTN)

**วิชา:** Data Communication and Computer Networks  
**Version:** 4.0  
**Based on:** e-Taste (Chen et al., Science Advances 2025)

---

## สมาชิกในทีม

| ลำดับ | ชื่อ-สกุล | รหัสนักศึกษา |
|---|---|---|
| 1 | นายกรกฎ พรมทอง | 673380025-8 |
| 2 | นายวัชรวิศว์ น้อยเมล์ | 673380059-1 |
| 3 | นายจิณณวัตร โพธิ์ศรีทอง | 673380263-2 |
| 4 | นายสรวิชญ์ ทะมานันท์ | 673380295-9 |
| 5 | นายปกรณ์เกียรติ ศรีจันทร์ | 673380045-2 |

---

## 1. System Overview

TTN (Taste Data Transmission Network) คือระบบ **"ส่งผ่านรสชาติทางไกลแบบ End-to-End"** (Remote Taste Transfer) โดยแปลงข้อมูลทางเคมีของอาหารต้นทางให้กลายเป็นแพ็กเก็ตข้อมูลดิจิทัล (Sensory Digitization) และส่งผ่านโครงข่าย Wireless IoT และ Cloud Platform เพื่อสั่งการอุปกรณ์ไมโครคอนโทรลเลอร์ปลายทาง ให้สังเคราะห์รสชาตินั้นขึ้นมาใหม่บนลิ้นของผู้รับแบบเรียลไทม์

```
Sensor Patch → ESP32-C3 → WiFi AP → IoT Cloud → WiFi AP → ESP32-C3 → EM Actuator
  [SRC]          [SRC]      [AP1]      [IOT]       [AP2]      [DST]       [DST]
192.168.1.10               192.168.1.1  34.120.0.1  10.0.0.1           10.0.0.10
```

Topology ประกอบด้วย 5 Node ได้แก่ SRC (ESP32-C3 + Sensor Patch), AP1 (WiFi 2.4GHz 802.11n), IOT (Blynk/ESPNOW Cloud Relay), AP2 (WiFi 2.4GHz 802.11n) และ DST (ESP32-C3 + EM Pump)

---

## 2. Network Node Specification

| Node ID | Name | IP Address | MAC Address | Type | Hardware |
|---|---|---|---|---|---|
| **SRC** | Sensor + ESP32 | 192.168.1.10 | AA:BB:CC:DD:01:01 | IoT End Device | ESP32-C3 + Sensor Patch |
| **AP1** | WiFi AP (TX) | 192.168.1.1 | AA:BB:CC:DD:02:01 | 802.11 AP | 2.4 GHz 802.11n |
| **IOT** | IoT Cloud | 34.120.0.1 | N/A | Blynk / ESPNOW | Cloud Relay |
| **AP2** | WiFi AP (RX) | 10.0.0.1 | AA:BB:CC:DD:03:01 | 802.11 AP | 2.4 GHz 802.11n |
| **DST** | ESP32 + Actuator | 10.0.0.10 | AA:BB:CC:DD:04:01 | IoT End Device | ESP32-C3 + EM Pump |

---

## 3. Hardware Design

### 3.1 Source Node — ฮาร์ดแวร์ฝั่งต้นทาง

**Sensor Patch (ลิ้นอิเล็กทรอนิกส์)**  
แผงเซนเซอร์เคมีสำหรับแตะสัมผัสอาหารจริง เพื่อตรวจจับระดับสารเคมีพื้นฐาน 5 ช่อง:

| Channel | สารเคมี | รสชาติ |
|---|---|---|
| `ch_sweet` | Glucose | หวาน |
| `ch_salty` | NaCl | เค็ม |
| `ch_sour` | H+ ion | เปรี้ยว |
| `ch_bitter` | Quinine | ขม |
| `ch_umami` | Glutamate | อูมามิ |

**ESP32-C3 Microcontroller (SRC)**  
รับสัญญาณอนาล็อกจากเซนเซอร์ผ่าน **ADC 16-bit** แปลงเป็นพิกัดข้อมูลดิจิทัล `float32[5]` แล้วส่งออกผ่านเครือข่าย WiFi ด้วยโปรโตคอล UDP Port **55100 → 7775**

### 3.2 Destination Node — ฮาร์ดแวร์ฝั่งปลายทาง

**ESP32-C3 Microcontroller (DST)**  
รับข้อมูลจาก IoT Cloud Platform (Blynk / ESPNOW) นำข้อมูลรสชาติมาคำนวณและแปลงเป็น **PWM Duty Cycle**

**EM Actuator (Minipump Injector)**  
มอเตอร์ปั๊มไมโครฟลูอิดิกขนาดจิ๋ว รับสัญญาณ PWM เพื่อฉีด Tastant solution ออกจากตลับลงสู่ลิ้นของผู้ใช้แบบเรียลไทม์

---

## 4. OSI Layer Architecture

### TX PATH — Encapsulation L7 → L1 (Sensor ESP32)

| Layer | ชื่อ | การทำงานใน TTN | ผลลัพธ์ |
|---|---|---|---|
| **L7** | Application | Serialize `float32[5]` → JSON payload | Payload raw KB |
| **L6** | Presentation | Normalize + gzip compress ratio ~1.7× | Compressed ~0.6× |
| **L5** | Session | ESPNOW session / Blynk auth token, seq=XXXX | Session established |
| **L4** | Transport | UDP header 55100→7775 checksum, DSCP=EF | Datagram +8B |
| **L3** | Network | IP header TTL=64 src=192.168.1.10 dst=10.0.0.10 | +20 bytes |
| **L2** | Data Link | WiFi 802.11 frame MAC + FCS, HMAC-SHA256 | Frame queued at AP |
| **L1** | Physical | 2.4 GHz OFDM 802.11n 20MHz channel | Bits transmitted OTA |

### RX PATH — Decapsulation L1 → L7 (Actuator ESP32)

```
L1 → รับสัญญาณ 2.4GHz OTA
L2 → CRC-32 (FCS) Frame Check — PASS
L4 → UDP checksum — PASS
L5 → Sequence in-order, no replay
L6 → Decompress gzip
L7 → Reconstruct taste vector float32[5]
[MCU] แปลง concentration → PWM duty cycle
[EM]  สั่ง minipump inject tastant solution 💧
```

---

## 5. Taste Dataset Specification

| Dataset ID | Label | Sweet | Salty | Sour | Bitter | Umami | Size | Origin | ADC |
|---|---|---|---|---|---|---|---|---|---|
| DS-001 | Wagyu Steak | 0.10 | 0.40 | 0.00 | 0.10 | **0.90** | 2.4 KB | JP | 16-bit |
| DS-002 | Salmon Sushi | 0.20 | 0.50 | 0.30 | 0.00 | **0.70** | 1.8 KB | JP | 16-bit |
| DS-003 | Truffle Risotto | 0.10 | 0.30 | 0.00 | 0.20 | **0.95** | 2.6 KB | IT | 24-bit |
| DS-004 | Tom Yum Soup | 0.20 | 0.40 | **0.80** | 0.00 | 0.60 | 1.5 KB | TH | 16-bit |
| DS-005 | Choc Lava Cake | **0.90** | 0.10 | 0.00 | 0.35 | 0.00 | 1.2 KB | FR | 12-bit |
| DS-006 | Pad Thai | 0.40 | 0.50 | 0.30 | 0.00 | **0.65** | 1.7 KB | TH | 16-bit |
| DS-007 | Caesar Salad | 0.05 | 0.45 | 0.35 | 0.20 | 0.40 | 1.1 KB | US | 12-bit |
| DS-008 | Mango Sticky Rice | **0.85** | 0.15 | 0.10 | 0.00 | 0.05 | 1.0 KB | TH | 12-bit |

---

## 6. Network Profile Specification

| Profile | Latency | Loss | Jitter | MTU | Bandwidth | Range | Protocol | Score |
|---|---|---|---|---|---|---|---|---|
| **ESPNOW (Local)** | 5 ms | 0.5% | ±1 ms | 250 B | 1 Mbps | 200 m | ESPNOW | ~97 |
| **WiFi 802.11n** | 15 ms | 1.5% | ±5 ms | 1500 B | 72 Mbps | 50 m | UDP/IP | ~88 |
| **IoT Cloud (Good)** | 300 ms | 0.5% | ±50 ms | 1500 B | 10 Mbps | Global | Blynk/HTTPS | ~73 |
| **IoT Cloud (Fair)** | 800 ms | 3.0% | ±200 ms | 1500 B | 1 Mbps | Global | Blynk/HTTPS | ~42 |
| **IoT Cloud (Poor)** | 2,000 ms | 10.0% | ±500 ms | 576 B | 256 Kbps | Global | Blynk/HTTPS | ~12 |

Network Score คำนวณจาก:

```
score = max(0, 100 - min(lat/20, 50) - loss*3 - jitter/10)
```

---

## 7. Math Formalization & Quality Metrics

### 7.1 Sensory Digitization

$$V_{taste} = [Sweet, Salty, Sour, Bitter, Umami] \quad \text{โดยแต่ละค่า} \in [0.0, 1.0]$$

### 7.2 Actuation Model

$$PWM_{duty} = (V_{taste}[Channel] \times 100) \pm Jitter_{network}$$

### 7.3 Sensory Fidelity

$$Fidelity = 1 - \frac{Latency}{3000} \pm Noise$$

### 7.4 Domain Mapping Table

| Domain | Layer | Math Formalization | Key Metric |
|---|---|---|---|
| Bio-Chemical | [SRC] Sensor Patch | `V_taste = [Sw, Sa, So, Bi, Um]` ∈ [0.0, 1.0] | ADC 16-bit precision |
| Network & Cyber | [AP1/AP2] WiFi & UDP | `Hash(Payload+Port) == UDP_chk` · `CRC32(Frame) == FCS` | Latency < 20ms, Loss < 5% |
| Security & Session | [IOT] Cloud Session | `Auth = HMAC_SHA256(ID + IP)` · `Session_alive = Δt < 5000ms` | Timeout Guard: Δt ≥ 5s |
| Electro-Mechanical | [DST] EM Actuator | `PWM_duty = (V_taste[Ch] × 100) - f(Jitter)` | Jitter < 5ms (ESPNOW) |
| Physiological/Ethics | QoS Policy Filtering | `If V_taste[Salty] > 0.25 → V_taste[Salty] = 0.25` | Salty ≤ 0.25 (Max) |

---

## 8. Quality Metrics

| Metric | Target | เหตุผล |
|---|---|---|
| End-to-End Latency | **< 20 ms** | ESPNOW ทำได้ต่ำสุด 5ms — ต่ำกว่า threshold การรับรู้ของสมองมนุษย์ |
| Packet Loss | **< 5%** | เพื่อไม่ให้รสชาติขาดหายหรือเกิดความผิดเพี้ยน |
| Network Jitter | **< 5 ms** | ให้มอเตอร์ปั๊มทำงานได้อย่างราบรื่น ไม่กระตุก |
| MTU Size (ESPNOW) | **≤ 250 B** | ข้อจำกัดของโหมด ESPNOW เพื่อความเร็วสูงสุด |
| Salty Safety Cap | **V[Salty] ≤ 0.25** | ป้องกันภาวะโซเดียมเกิน (Hypernatremia) |
| Emergency Stop | **< 10 ms** | Hardware-level power cutoff |
| Cartridge Warning | **< 10%** | แจ้งเตือนก่อนสารละลายหมด |
| IoT Session Timeout | **5 s** | ตัด EM Pump อัตโนมัติเมื่อ Connection Lost |

---

## 9. Dealing with Network Issues

### 9.1 UDP & ESPNOW over WiFi 802.11n

เลือกใช้โปรโตคอล **UDP (Port 55100 → 7775)** ร่วมกับเทคโนโลยี **ESPNOW** แทนการใช้ TCP เพื่อ:
- ตัดกระบวนการ Handshake
- หลีกเลี่ยงการส่งข้อมูลซ้ำเมื่อเกิดข้อผิดพลาด (**No ARQ**)
- ลด Latency ให้ต่ำสุดระดับ **< 5ms** ในเครือข่าย Local

### 9.2 Payload Compression & MTU Optimization

- บีบอัดข้อมูลแบบ **Gzip** (Compression Ratio ~1.7×)
- จำกัดขนาดแพ็กเก็ต **MTU ≤ 250 Bytes** สำหรับ ESPNOW
- ลดความเสี่ยงในการเกิดข้อมูลสูญหาย (Packet Loss)

### 9.3 IoT Session Timeout Guard

หากเกิดปัญหา High Jitter หรือ Connection Lost เกิน **5 วินาที** ระบบจะตัดการทำงานของ EM Actuator ทันที เพื่อป้องกันไม่ให้ปั๊มฉีดสารละลายค้างลงบนลิ้นของผู้ใช้

---

## 10. Security Architecture

| Security Check | Method | ผลลัพธ์เมื่อผ่าน |
|---|---|---|
| **HMAC-SHA256 Authentication** | `HMAC_SHA256(ID + IP)` | PSK match — frame accepted |
| **CRC-32 Frame Check (WiFi FCS)** | `CRC32(Frame) == FCS` | ไม่พบ bit-error — data intact |
| **Sequence Number Validation** | Seq number in-order check | seq in-order, no gap detected |
| **Replay Attack Detection** | Nonce + timestamp | Duplicate discarded |
| **ESPNOW MAC Address Filter** | Paired MAC whitelist | Stranger blocked |
| **Blynk Auth Token Verify** | Token validation | Cloud session open |
| **MTU Size Validation** | Frame ≤ MTU limit | Frame ≤ MTU 1500B — OK |
| **IoT Session Timeout Guard** | Δt < 5000ms | Timeout=5s — session alive |

---

## 11. Ethics, Regulations & HITL

### 11.1 QoS Policy Filtering (L7 DPI)

หาก `V[Salty] > 0.25` ซอฟต์แวร์จะเขียนทับแพ็กเก็ตและลดเพดานลงมาทันที เพื่อป้องกันการจำลองภาวะโซเดียมเกิน (Hypernatremia)

### 11.2 Hardware Absolute Limit

EM Minipump ถูกฮาร์ดโค้ดให้จำกัดปริมาณการฉีดสูงสุดต่อครั้ง หากถูกโจมตีทางไซเบอร์สั่งให้ปั๊มทำงานที่ 100% ต่อเนื่อง ฮาร์ดแวร์จะตัดการทำงาน (Safety Lock) อย่างเด็ดขาด

### 11.3 Human-in-the-Loop (HITL)

| HITL Feature | การทำงาน |
|---|---|
| **Sensory EQ Slider** | ผู้ใช้ปรับความเข้มข้นรสชาติ 5 ช่องแบบ Real-time |
| **RED Emergency Stop** | ตัดการเชื่อมต่อ IoT Session + ปิดไฟ EM Pump ภายใน < 10ms |
| **Cartridge Warning** | Alert + ขออนุมัติจากผู้ใช้เมื่อสารละลายเหลือ < 10% |

---

## 12. Simulation Scenarios

| Scenario | รายละเอียด |
|---|---|
| **[1] TTN Simulation** | จำลอง packet รสชาติผ่าน ESP32 → WiFi → IoT Cloud |
| **[2] Quick Demo** | Tom Yum Soup / ESPNOW Local — 2 packets |
| **[3] Stress Test** | IoT Cloud Poor vs ESPNOW Local เปรียบเทียบ |
| **[4] Security Checks** | HMAC, CRC, ESPNOW MAC filter, Blynk auth token |
| **[5] OSI Walkthrough** | Encapsulation L7→L1 บน WiFi IoT Stack |
| **[6] Network Profiles** | เปรียบเทียบ ESPNOW / WiFi / IoT Cloud (Good–Poor) |
