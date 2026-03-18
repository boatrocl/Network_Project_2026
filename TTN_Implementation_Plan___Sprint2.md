# TTN Implementation Plan & Sprint Roadmap

**Project:** Tastes Through Network (TTN) — v4.0  
**Version:** Sprint Alpha + 1  
**Based on:** e-Taste (Chen et al., Science Advances 2025)  
**วิชา:** Data Communication and Computer Networks

---

## ทีมงาน

| ชื่อ-สกุล | รหัส | บทบาทหลัก |
|---|---|---|
| นายกรกฎ พรมทอง | 673380025-8 | Architecture Lead / Test Coordinator |
| นายวัชรวิศว์ น้อยเมล์ | 673380059-1 | Software Development / Network Layer |
| นายจิณณวัตร โพธิ์ศรีทอง | 673380263-2 | UI Dashboard / System Integration |
| นายสรวิชญ์ ทะมานันท์ | 673380295-9 | Hardware Prototype / ESP32 Programming |
| นายปกรณ์เกียรติ ศรีจันทร์ | 673380045-2 | Presentation Lead / Documentation |

---

## Sprint Overview

| Sprint | สัปดาห์ | Phase | Deliverable |
|---|---|---|---|
| Sprint 0 | Week 1 | ToT / CoT | `Architecture_Specification.md` |
| Sprint 1 | Week 2 | CoT / ReAct | `index.html` + `ttn_demo_gui_3.py` v1 + Hardware v1 |
| Sprint 2 | Week 3 | ReAct / RAG | Test Report 12 Cases + Bug-fixed Simulator |
| Sprint 3 | Week 4 | Finalization | Slide Deck + Final Demo + Code Repository |

---

## Week 1 — Architecture & Design (ToT / CoT Phase)

**เป้าหมาย:** วางรากฐานสถาปัตยกรรมระบบและกำหนด Specification ครบทุกส่วน

### งานที่ทำ

**System Architecture Design**
- ออกแบบ Network Topology: `SRC → AP1 → IOT → AP2 → DST` ตาม e-Taste จริง
- กำหนด Network Node ทั้ง 5 จุด พร้อม IP Address และ MAC Address

**Protocol & Data Structure**
- เลือกใช้ UDP Port 55100 → 7775 แทน TCP (No Handshake, No ARQ)
- กำหนด Taste Vector: `V_taste = float32[5]` — [Sweet, Salty, Sour, Bitter, Umami]
- กำหนด Dataset Specification 8 เมนู (DS-001 ถึง DS-008) พร้อม ADC resolution

**Math Formalization**
- กำหนดสมการ Actuation Model: `PWM_duty = (V_taste[Channel] × 100) ± Jitter_network`
- กำหนด Sensory Fidelity: `Fidelity = 1 - (Latency / 3000) ± Noise`
- กำหนด Network Score: `score = max(0, 100 - min(lat/20,50) - loss*3 - jitter/10)`

**Quality Metrics**
- End-to-End Latency < 20ms (ESPNOW ทำได้ < 5ms)
- Packet Loss < 5%
- Network Jitter < 5ms
- MTU ≤ 250B สำหรับ ESPNOW

**Ethics & Safety Policy**
- Salty Cap: `V[Salty] ≤ 0.25` ป้องกัน Hypernatremia
- Emergency Stop: < 10ms Hardware cutoff
- Cartridge Warning: Alert เมื่อสารเหลือ < 10%
- IoT Session Timeout Guard: ตัด EM Pump เมื่อ Connection Lost > 5s

### Deliverable

- ✅ `Architecture_Specification.md` — ฉบับสมบูรณ์

---

## Week 2 — Mockup & Network Development (CoT / ReAct Phase)

**เป้าหมาย:** พัฒนา Software Simulator และ Hardware Prototype พร้อมกัน

### งานที่ทำ — Software Track

**Terminal Simulation (`ttn_demo_gui_3.py`)**

พัฒนา Python simulation สำหรับจำลอง TTN Pipeline ครบ End-to-End โดยมี 6 Scenarios:

| Scenario | รายละเอียด |
|---|---|
| [1] TTN Simulation | จำลอง packet รสชาติผ่าน ESP32 → WiFi → IoT Cloud |
| [2] Quick Demo | Tom Yum Soup / ESPNOW Local — 2 packets |
| [3] Stress Test | IoT Cloud Poor vs ESPNOW Local เปรียบเทียบ |
| [4] Security Checks | HMAC, CRC, ESPNOW MAC filter, Blynk auth token |
| [5] OSI Walkthrough | Encapsulation L7→L1 บน WiFi IoT Stack |
| [6] Network Profiles | เปรียบเทียบ ESPNOW / WiFi / IoT Cloud (Good–Poor) |

รายละเอียด Packet ที่จำลอง:
- สร้าง `uuid` เป็น Packet ID และ Session ID
- คำนวณ `HMAC-SHA256` จาก ID + IP
- คำนวณ `CRC-32` สำหรับ Frame Check
- กำหนด Dominant taste channel จาก max value ใน V_taste
- แสดง Network Animation ผ่าน Terminal Topology Frame 82 chars โดย Packet เคลื่อนที่ผ่าน SRC → AP1 → IOT → AP2 → DST พร้อม Node Highlight: `idle` / `active` / `lost` / `done`

**Web Dashboard (`index.html`)**

พัฒนา Web UI ที่ประกอบด้วย:

| Component | รายละเอียด |
|---|---|
| **Topology Visualizer** | SVG แสดง 5 Nodes + Packet Animation |
| **Dataset Selector** | Dropdown เลือก 8 เมนู (DS-001 ถึง DS-008) |
| **Network Profile Selector** | Dropdown เลือก 5 Network Profiles |
| **Taste Vector Bars** | แถบแสดง Sweet/Salty/Sour/Bitter/Umami พร้อม Dominant indicator |
| **Sensory EQ Sliders** | HITL Sliders ปรับ 5 ช่องรสชาติ Real-time |
| **EM Actuator Cartridge** | Progress bar + Drop indicators แสดงปริมาณสารละลาย |
| **OSI Layer Walkthrough** | Animation Encapsulation L7→L1 / Decapsulation L1→L7 |
| **Security Check Panel** | แสดง 8 Security Checks พร้อม PASS/FAIL |
| **Network Compare Table** | ตารางเปรียบเทียบ 5 Network Profiles พร้อม Score Bar |
| **Simulation Result Tab** | Report สรุปผลหลัง Simulation จบ |
| **Terminal Log** | Real-time log แสดง packet journey |

**HITL & Safety Features**
- `onEQChange()` — Sensory EQ slider พร้อม Debounce 300ms ป้องกัน DOM Bloat
- `emergencyStop()` — RED Emergency Stop ตัดทุก component
- `showCartridgeWarning()` — Cartridge Modal ขออนุมัติผู้ใช้
- `consumeCartridge()` — ลด Tastant solution ตาม PWM intensity

### งานที่ทำ — Hardware Track

- ประกอบ Toy Model: ESP32-C3 SRC + Sensor Patch (ลิ้นอิเล็กทรอนิกส์)
- ประกอบ ESP32-C3 DST + EM Minipump Injector
- ทดสอบ WiFi 802.11n ESPNOW Pairing ระหว่าง SRC ↔ DST (2.4GHz)
- ต่อวงจร EM Minipump รับสัญญาณ PWM Duty Cycle จาก ESP32

### Deliverable

- ✅ `ttn_demo_gui_3.py` — Terminal Simulation v4.0
- ✅ `index.html` — Web Dashboard Simulator
- ✅ Hardware Prototype v1

---

## Week 3 — System Integration & Testing (ReAct / RAG Phase)

**เป้าหมาย:** เชื่อมต่อทุกส่วนเข้าด้วยกัน รัน Test Scenarios ครบ และแก้ Bug

### System Integration

- เชื่อม Web Dashboard → Python Simulation → ESP32 Hardware
- ทดสอบ End-to-End: Select Dataset → Run Simulation → Packet travels → EM Pump fires
- ปรับแต่ง Latency Progress Bar ให้สะท้อนค่าจริงของแต่ละ Network Profile
- กำหนด `hopDelays` ตาม Network Profile จริง เช่น ESPNOW ไม่รอ, Cloud Poor รอ 800ms ต่อ hop

### Test Scenarios (12 Test Cases)

#### หมวด A — Network Stress Test & Resiliency

| Test ID | Scenario | Input | Expected | Pass Criteria |
|---|---|---|---|---|
| **TC-A01** | Network Profile Comparison | ESPNOW vs Cloud Poor, 3 Packets | ESPNOW < 5ms, Cloud Poor ~2,000ms | ผลต่าง ≥ 400× |
| **TC-A02** | Packet Loss Handling (UDP No-Retransmit) | Cloud Poor Loss=10%, 5 Packets | Skip dropped, ส่ง Packet ถัดไปทันที | Continue < 500ms หลัง Drop |
| **TC-A03** | IoT Session Timeout Guard | จำลอง Connection Lost | EM Pump OFF ภายใน 10ms | Cutoff < 10ms |
| **TC-A04** | MTU Payload Compliance | DS-003 (2.6KB) + ESPNOW (MTU=250B) | Fragment payload, ทุก Frame ≤ 250B | ไม่มี Frame เกิน MTU |

#### หมวด B — IoT Security & Data Integrity

| Test ID | Scenario | Method | Pass Criteria |
|---|---|---|---|
| **TC-B01** | CRC-32 Frame Check (WiFi FCS) | `CRC32(Frame) == FCS` | CRC PASS ทุก Packet ที่ถึงปลายทาง |
| **TC-B02** | HMAC-SHA256 Authentication | `HMAC_SHA256(ID + IP)` PSK match | HMAC ตรงกัน 100% |
| **TC-B03** | Replay Attack Detection | Seq=0001 ซ้ำ | Duplicate Packet ถูกทิ้ง |
| **TC-B04** | ESPNOW MAC Address Filter | MAC แปลกปลอม | Stranger blocked, EM Pump ไม่รับ |
| **TC-B05** | Blynk Auth Token Verify | Token ผิด | 401 Unauthorized, Drop Packet |

#### หมวด C — HITL & Safety Validation

| Test ID | Scenario | Input | Expected | Pass Criteria |
|---|---|---|---|---|
| **TC-C01** | QoS L7 DPI — Salty Cap | Slider SALTY → 0.80 | ระบบ Clamp เป็น 0.25 อัตโนมัติ | V[Salty] ≤ 0.25 ตลอดเวลา |
| **TC-C02** | RED Emergency Stop | กดปุ่มระหว่าง Simulation | UDP Disconnect + EM Pump OFF | Halt < 10ms |
| **TC-C03** | Cartridge Warning Alert | สารเหลือ < 10% | Modal Alert + รอ HITL Approve | Alert ก่อนสารหมด |

### Bug Fixing Log

| Bug | สาเหตุ | การแก้ไข |
|---|---|---|
| Simulation ไม่เริ่ม | `const _origRunSim = runSimulation` สร้าง Infinite Loop | ลบ wrapper ออก เรียก `generateResult()` ตรงๆ |
| `classList.add('')` Error | `vBox.classList.add('')` ใน PASS verdict | ลบบรรทัดนั้น — base class ไม่ต้องเพิ่ม class |
| EQ Slider ทำให้ web ค้าง | `log()` ถูกเรียกทุก pixel ที่ลาก = DOM Bloat | เพิ่ม Debounce 300ms + Terminal log cap 200 บรรทัด |
| `showLatencyWait()` ค้าง | `setInterval` stepMs = 0.125ms browser ไม่รองรับ | เปลี่ยนเป็น CSS transition animation + `sleep()` |
| `simRunning` ค้าง true | ไม่มี try-finally รอบ simulation | เพิ่ม `try...finally` รับประกัน cleanup ทุกกรณี |
| `simTickLog` duplicate | Declare 2 ครั้ง → JS strict mode error | ย้ายไปใน state declarations จุดเดียว |

### Deliverable

- ✅ Test Report — 12 Test Cases (TC-A01 ถึง TC-C03) ทั้งหมด PASS
- ✅ Bug-fixed `index.html` + `ttn_demo_gui_3.py`
- ✅ Simulation Result: Network Profile Comparison + Packet Loss Handling

---

## Week 4 — Finalization & Pitching

**เป้าหมาย:** เตรียมการนำเสนอให้สมบูรณ์และฝึกซ้อม Dry Run

### งานที่ทำ

**Slide Deck (14.5 นาที)**

| สไลด์ | หัวข้อ | เนื้อหา |
|---|---|---|
| 1 | Title | Taste Data Transmission Network — TTN |
| 2 | Concept | Remote Taste Transfer, Sensory Digitization |
| 3 | System Design & Hardware | Source Node + Destination Node |
| 4–5 | Math Formalization & Quality Metrics | V_taste, PWM formula, Domain Mapping Table |
| 6 | Dealing with Network Issues | UDP/ESPNOW, Compression, Timeout Guard |
| 7 | Ethics, Regulations & HITL | QoS DPI, Hardware Limit, Sensory EQ, Emergency Stop |
| 8–9 | System Testing & Validation | Test Case 12 หมวด A + B |
| 10–11 | ขั้นตอนการใช้งานระบบ TTN | Use Case: เชฟกรุงเทพฯ → ลูกค้าโตเกียว (5 ขั้นตอน) |
| 12–13 | Simulation Result | Network Profile Comparison + Packet Loss Handling |
| 14–19 | ประเมินตนเองและสมาชิก | Self-assessment + Peer evaluation |

**Use Case สไลด์ (ขั้นตอนการใช้งานจริง)**

1. **Sensory Digitization** — Sensor Patch แตะต้มยำกุ้ง อ่าน ADC 16-bit @ 1kHz → `V_taste = {Sweet:0.20, Salty:0.40, Sour:0.80, Bitter:0.00, Umami:0.60}`
2. **QoS Policy Filtering** — V[Salty] 0.40 เกินเกณฑ์ → ระบบ Clamp เป็น 0.25 อัตโนมัติ
3. **Network Transmission** — UDP → IoT Cloud → WiFi ฝั่งรับ ภายใน **4.7 ms**
4. **Security Verification** — CRC-32, HMAC-SHA256, Seq Number, MAC Filter ผ่าน 100%
5. **Actuation** — EM Pump ฉีด: Sour 80% + Umami 60% + Salty 25% + Sweet 20%

**Simulation Result**

| หัวข้อ | ผลลัพธ์ |
|---|---|
| Network Profile Comparison | ESPNOW avg 4.7ms vs Cloud Poor avg 1,959ms |
| Packet Loss Handling | Drop 1/5 Packets (20%), Continue < 300ms |
| Security Score | 8/8 checks PASS (100%) |

### Deliverable

- ✅ Slide Deck ฉบับสมบูรณ์ 19 หน้า
- ✅ Final Demo: `index.html` Web Simulator + `ttn_demo_gui_3.py` Terminal Sim
- ✅ Code Repository ครบทุกไฟล์
- ✅ Dry Run ซ้อมนำเสนอครบ 14.5 นาที

---

## สรุป Deliverables ทั้งหมด

| Deliverable | ไฟล์ | สถานะ |
|---|---|---|
| Architecture Specification | `Architecture_Specification.md` | ✅ Complete |
| Terminal Simulation | `ttn_demo_gui_3.py` | ✅ Complete (v4.0) |
| Web Dashboard Simulator | `index.html` | ✅ Complete |
| Test Report (12 Cases) | อยู่ใน Slide + Result Tab | ✅ Complete |
| Presentation Slides | PDF (19 หน้า) | ✅ Complete |
| Implementation Plan | `__TTN_Implementation_Plan___Sprint.md` | ✅ Complete |
