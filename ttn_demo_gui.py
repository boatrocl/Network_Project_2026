#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTN — Taste Data Transmission Network v4.0
ถูกหลักการ: Topology ตรงตามงานวิจัย e-Taste (Chen et al., Sci. Adv. 2025)
  Sensor Patch → ESP32 → WiFi/IoT Cloud → ESP32 → EM Actuator
วิชา: Data Communication and Computer Networks
Terminal-only — No GUI
"""

import time, random, hashlib, uuid, sys, os, argparse
from datetime import datetime
import re as _re

# ══════════════════════════════════════════════════════════════════
#  WINDOWS ANSI
# ══════════════════════════════════════════════════════════════════
def _win_ansi():
    if sys.platform == "win32":
        try:
            import ctypes
            k = ctypes.windll.kernel32
            k.SetConsoleMode(k.GetStdHandle(-11), 7)
        except Exception:
            pass
_win_ansi()

# ══════════════════════════════════════════════════════════════════
#  COLORS
# ══════════════════════════════════════════════════════════════════
class C:
    RESET   = "\033[0m";  BOLD    = "\033[1m"
    GRAY    = "\033[90m"; RED     = "\033[91m"; GREEN   = "\033[92m"
    YELLOW  = "\033[93m"; BLUE    = "\033[94m"; MAGENTA = "\033[95m"
    CYAN    = "\033[96m"; WHITE   = "\033[97m"

def c(text, *codes): return "".join(codes) + str(text) + C.RESET
def vis(s): return len(_re.sub(r'\033\[[0-9;]*m', '', str(s)))

# ══════════════════════════════════════════════════════════════════
#  TERMINAL PRIMITIVES
# ══════════════════════════════════════════════════════════════════
def w(s): sys.stdout.write(s); sys.stdout.flush()

def alt_screen_on():  w("\033[?1049h")
def alt_screen_off(): w("\033[?1049l")
def hide_cursor():    w("\033[?25l")
def show_cursor():    w("\033[?25h")
def clear_screen():   w("\033[2J")
def move(r, col):     w(f"\033[{r};{col}H")

def print_at(r, col, text):       move(r, col); w(text)
def print_at_c(r, col, text, *codes):
    print_at(r, col, "".join(codes) + text + C.RESET)

# ══════════════════════════════════════════════════════════════════
#  DATA
# ══════════════════════════════════════════════════════════════════
CHANNELS = ["ch_sweet", "ch_salty", "ch_sour", "ch_bitter", "ch_umami"]
CH_LABEL = {"ch_sweet":"SWEET ","ch_salty":"SALTY ","ch_sour":"SOUR  ",
            "ch_bitter":"BITTER","ch_umami":"UMAMI "}
CH_CHEM  = {"ch_sweet":"Glucose  ","ch_salty":"NaCl     ","ch_sour":"H+ ion   ",
            "ch_bitter":"Quinine  ","ch_umami":"Glutamate"}
CH_COLOR = {"ch_sweet":C.MAGENTA,"ch_salty":C.CYAN,"ch_sour":C.YELLOW,
            "ch_bitter":C.GRAY,"ch_umami":C.GREEN}

# ── Nodes ตรงตามงานวิจัย ──────────────────────────────────────────
#  SRC = Sensor Patch + ESP32 (ฝั่งส่ง)
#  AP1 = WiFi Access Point (ฝั่งส่ง)
#  IOT = IoT Cloud (Blynk / ESPNOW relay)
#  AP2 = WiFi Access Point (ฝั่งรับ)
#  DST = ESP32 + EM Actuator (ฝั่งรับ)
NETWORK_NODES = {
    "SRC": {"name": "Sensor + ESP32",  "ip": "192.168.1.10",  "mac": "AA:BB:CC:DD:01:01",
            "type": "IoT End Device",  "hw": "ESP32-C3 + Sensor Patch"},
    "AP1": {"name": "WiFi AP (TX)",    "ip": "192.168.1.1",   "mac": "AA:BB:CC:DD:02:01",
            "type": "802.11 AP",       "hw": "2.4 GHz 802.11n"},
    "IOT": {"name": "IoT Cloud",       "ip": "34.120.0.1",    "mac": "N/A",
            "type": "Blynk / ESPNOW",  "hw": "Cloud Relay"},
    "AP2": {"name": "WiFi AP (RX)",    "ip": "10.0.0.1",      "mac": "AA:BB:CC:DD:03:01",
            "type": "802.11 AP",       "hw": "2.4 GHz 802.11n"},
    "DST": {"name": "ESP32 + Actuator","ip": "10.0.0.10",     "mac": "AA:BB:CC:DD:04:01",
            "type": "IoT End Device",  "hw": "ESP32-C3 + EM Pump"},
}

DATASETS = {
    "1": {"id":"DS-001","label":"Wagyu Steak",       "ch_sweet":0.10,"ch_salty":0.40,
          "ch_sour":0.00,"ch_bitter":0.10,"ch_umami":0.90,"size_kb":2.4,"origin":"JP",
          "sample_rate":"1 kHz","adc_bits":16},
    "2": {"id":"DS-002","label":"Salmon Sushi",      "ch_sweet":0.20,"ch_salty":0.50,
          "ch_sour":0.30,"ch_bitter":0.00,"ch_umami":0.70,"size_kb":1.8,"origin":"JP",
          "sample_rate":"1 kHz","adc_bits":16},
    "3": {"id":"DS-003","label":"Truffle Risotto",   "ch_sweet":0.10,"ch_salty":0.30,
          "ch_sour":0.00,"ch_bitter":0.20,"ch_umami":0.95,"size_kb":2.6,"origin":"IT",
          "sample_rate":"2 kHz","adc_bits":24},
    "4": {"id":"DS-004","label":"Tom Yum Soup",      "ch_sweet":0.20,"ch_salty":0.40,
          "ch_sour":0.80,"ch_bitter":0.00,"ch_umami":0.60,"size_kb":1.5,"origin":"TH",
          "sample_rate":"1 kHz","adc_bits":16},
    "5": {"id":"DS-005","label":"Choc Lava Cake",    "ch_sweet":0.90,"ch_salty":0.10,
          "ch_sour":0.00,"ch_bitter":0.35,"ch_umami":0.00,"size_kb":1.2,"origin":"FR",
          "sample_rate":"500 Hz","adc_bits":12},
    "6": {"id":"DS-006","label":"Pad Thai",          "ch_sweet":0.40,"ch_salty":0.50,
          "ch_sour":0.30,"ch_bitter":0.00,"ch_umami":0.65,"size_kb":1.7,"origin":"TH",
          "sample_rate":"1 kHz","adc_bits":16},
    "7": {"id":"DS-007","label":"Caesar Salad",      "ch_sweet":0.05,"ch_salty":0.45,
          "ch_sour":0.35,"ch_bitter":0.20,"ch_umami":0.40,"size_kb":1.1,"origin":"US",
          "sample_rate":"500 Hz","adc_bits":12},
    "8": {"id":"DS-008","label":"Mango Sticky Rice", "ch_sweet":0.85,"ch_salty":0.15,
          "ch_sour":0.10,"ch_bitter":0.00,"ch_umami":0.05,"size_kb":1.0,"origin":"TH",
          "sample_rate":"500 Hz","adc_bits":12},
}

# ── Network profiles สะท้อนความเป็นจริงของ WiFi / IoT ────────────
NET_PROFILES = {
    "1": {"name":"ESPNOW (Local)",    "lat":5,   "loss":0.5,  "jitter":1,
          "bw":"1 Mbps",   "col":C.CYAN,   "mtu":250,  "range":"200 m",
          "protocol":"ESPNOW"},
    "2": {"name":"WiFi 802.11n",      "lat":15,  "loss":1.5,  "jitter":5,
          "bw":"72 Mbps",  "col":C.GREEN,  "mtu":1500, "range":"50 m",
          "protocol":"UDP/IP"},
    "3": {"name":"IoT Cloud (Good)",  "lat":300, "loss":0.5,  "jitter":50,
          "bw":"10 Mbps",  "col":C.GREEN,  "mtu":1500, "range":"Global",
          "protocol":"Blynk/HTTPS"},
    "4": {"name":"IoT Cloud (Fair)",  "lat":800, "loss":3.0,  "jitter":200,
          "bw":"1 Mbps",   "col":C.YELLOW, "mtu":1500, "range":"Global",
          "protocol":"Blynk/HTTPS"},
    "5": {"name":"IoT Cloud (Poor)",  "lat":2000,"loss":10.0, "jitter":500,
          "bw":"256 Kbps", "col":C.RED,    "mtu":576,  "range":"Global",
          "protocol":"Blynk/HTTPS"},
}

# ══════════════════════════════════════════════════════════════════
#  SCREEN LAYOUT
# ══════════════════════════════════════════════════════════════════
ROW_BANNER_START = 1
ROW_BANNER_END   = 10
ROW_INFO         = 11
ROW_TOPO_START   = 12
TOPO_ROWS        = 21
ROW_TOPO_END     = ROW_TOPO_START + TOPO_ROWS - 1   # 32
ROW_LOG_START    = ROW_TOPO_END + 1                  # 33
LOG_HEIGHT       = 12
ROW_LOG_END      = ROW_LOG_START + LOG_HEIGHT - 1    # 44
ROW_STATUS       = ROW_LOG_END + 1                   # 45
ROW_TASTE_START  = ROW_STATUS + 1                    # 46
TOTAL_ROWS       = ROW_TASTE_START + 7               # 53

# ══════════════════════════════════════════════════════════════════
#  TOPOLOGY FRAME  (82 chars)
#  สะท้อน e-Taste จริง: Sensor → ESP32 → WiFi AP → Cloud → WiFi AP → ESP32 → Actuator
#
#   [SRC] Sensor+ESP32                [IOT] IoT Cloud             [DST] ESP32+Actuator
#   +----------------+  ~~WiFi~~  +----------------+  ~~WiFi~~  +----------------+
#   | 192.168.1.10   | ~~~~~~~~~~>| Blynk / ESPNOW |<~~~~~~~~~~ | 10.0.0.10      |
#   | ADC 16-bit     |            | 34.120.0.1     |            | EM Pump PWM    |
#   +----------------+            +----------------+            +----------------+
#        ↑                              ↑                              ↓
#   Sensor Patch                   Upload/Download               EM Actuator
#   (Electronic tongue)            (IoT Platform)               (Taste delivery)
# ══════════════════════════════════════════════════════════════════
TOPO_FRAME = [
"+================================================================================+",  # 0
"|              e-Taste  IoT  TOPOLOGY  (Chen et al., Sci. Adv. 2025)            |",  # 1
"+================================================================================+",  # 2
"|                                                                                |",  # 3
"|  [SRC] Sensor+ESP32      [AP1] WiFi AP       [IOT] IoT Cloud                  |",  # 4
"|  +---------------+       +-----------+       +---------------+                |",  # 5
"|  | 192.168.1.10  |       |192.168.1.1|       | 34.120.0.1    |                |",  # 6
"|  | ADC 16-bit    |       |802.11n    |       | Blynk/ESPNOW  |                |",  # 7
"|  +-------+-------+       +-----+-----+       +-------+-------+                |",  # 8
"|          |                     |                     |                        |",  # 9
"|   WiFi   +~~~~~2.4GHz~~~~~~~~~~+  UDP/IP             |                        |",  # 10
"|          :                                    HTTPS  :                        |",  # 11
"|          :                                    Upload :                        |",  # 12
"|          :                                           :                        |",  # 13
"|  +-------+-------+       +-----------+       +-------+-------+                |",  # 14
"|  | 10.0.0.10     |       |10.0.0.1   |       |               |                |",  # 15
"|  | EM Pump PWM   |       |802.11n    |       | Download      |                |",  # 16
"|  +---------------+       +-----------+       +---------------+                |",  # 17
"|          |                     |                                               |",  # 18
"|   WiFi   +~~~~~2.4GHz~~~~~~~~~~+  UDP/IP                                      |",  # 19
"|  [DST] ESP32+Actuator    [AP2] WiFi AP                                        |",  # 20
"+================================================================================+",  # 21 (index 21 = last)
]

# Node label positions (frame_row, col 0-based)
NODE_POS = {
    "SRC": (4,  3),
    "AP1": (4,  27),
    "IOT": (4,  48),
    "DST": (20, 3),
    "AP2": (20, 27),
}
NODE_LABELS = {
    "SRC": "[SRC]",
    "AP1": "[AP1]",
    "IOT": "[IOT]",
    "DST": "[DST]",
    "AP2": "[AP2]",
}

# Animation paths — WiFi เป็นเส้นประ (~) ไม่ใช่ link สาย
LINK_PATHS = {
    ("SRC", "AP1"): [("h", 10,  10, 30)],
    ("AP1", "IOT"): [("h", 10,  30, 57)],
    ("IOT", "AP2"): [("v", 57,  10, 16)],   # ลงมาทาง Cloud → AP2
    ("AP2", "DST"): [("h", 19,  30, 10)],
}

# ══════════════════════════════════════════════════════════════════
#  PACKET
# ══════════════════════════════════════════════════════════════════
class Packet:
    def __init__(self, seq, ds):
        self.seq     = seq
        self.id      = str(uuid.uuid4())[:8].upper()
        self.session = str(uuid.uuid4())[:8].upper()
        self.vec     = {ch: ds.get(ch, 0.0) for ch in CHANNELS}
        self.size_kb = ds["size_kb"]
        src = NETWORK_NODES["SRC"]
        dst = NETWORK_NODES["DST"]
        self.src_ip   = src["ip"];  self.dst_ip  = dst["ip"]
        self.src_mac  = src["mac"]; self.dst_mac = dst["mac"]
        self.src_port = 55100;      self.dst_port = 7775
        self.udp_len  = int(self.size_kb * 1024) + 8
        self.ttl      = 64;         self.dscp = "EF"
        self.ip_id    = f"0x{seq:04x}"
        self.crc32    = hashlib.md5(self.id.encode()).hexdigest()[:8].upper()
        self.hmac     = hashlib.sha256(
            f"{self.id}{self.src_ip}".encode()).hexdigest()[:16].upper()
        self.udp_chk  = hashlib.md5(
            f"{self.id}{self.src_port}".encode()).hexdigest()[:8]
        self.dominant       = max(self.vec, key=self.vec.get)
        self.dominant_value = self.vec[self.dominant]

# ══════════════════════════════════════════════════════════════════
#  DRAW STATIC FRAME
# ══════════════════════════════════════════════════════════════════
def draw_static_frame(ds, net, session_id, num_packets):
    clear_screen()
    BW = 82

    # Banner
    print_at_c(1, 1, "+" + "=" * (BW-2) + "+", C.BLUE)
    TTN_ART = [
        r"  ████████╗████████╗███╗   ██╗",
        r"     ██╔══╝╚══██╔══╝████╗  ██║",
        r"     ██║      ██║   ██╔██╗ ██║",
        r"     ██║      ██║   ██║╚██╗██║",
        r"     ██║      ██║   ██║ ╚████║",
        r"     ╚═╝      ╚═╝   ╚═╝  ╚═══╝",
    ]
    for i, line in enumerate(TTN_ART):
        pad = BW - 2 - len(line)
        print_at(2+i, 1, c("|", C.BLUE) + c(line, C.CYAN, C.BOLD) +
                 " "*max(pad,0) + c("|", C.BLUE))

    sub = "T A S T E   D A T A   T R A N S M I S S I O N   N E T W O R K"
    pad = (BW - 2 - len(sub)) // 2
    print_at(8, 1, c("|", C.BLUE) + " "*pad + c(sub, C.WHITE, C.BOLD) +
             " "*(BW-2-pad-len(sub)) + c("|", C.BLUE))
    sub2 = "B A S E D   O N   e - T A S T E   (  C h e n   e t   a l .   2 0 2 5  )"
    pad2 = (BW - 2 - len(sub2)) // 2
    print_at(9, 1, c("|", C.BLUE) + " "*pad2 + c(sub2, C.CYAN) +
             " "*(BW-2-pad2-len(sub2)) + c("|", C.BLUE))
    print_at_c(10, 1, "+" + "=" * (BW-2) + "+", C.BLUE)

    # Info bar
    info = (f"  Dataset: {ds['label']} [{ds['id']}]"
            f"  Protocol: {net['protocol']}"
            f"  lat={net['lat']}ms  loss={net['loss']}%  bw={net['bw']}")
    print_at_c(ROW_INFO, 1, info[:80], C.WHITE)

    # Topology
    for i, line in enumerate(TOPO_FRAME):
        # สีพิเศษสำหรับ ~ (WiFi signal)
        colored = ""
        for ch in line:
            if ch == "~":
                colored += c(ch, C.GREEN)
            elif ch == ":":
                colored += c(ch, C.YELLOW)
            else:
                colored += c(ch, C.CYAN)
        print_at(ROW_TOPO_START + i, 1, colored)

    # Borders
    print_at_c(ROW_LOG_START - 1, 1, "─" * BW, C.GRAY)
    print_at_c(ROW_STATUS,        1, "─" * BW, C.GRAY)

    # Taste placeholder
    print_at_c(ROW_TASTE_START, 1, "  TASTE VECTOR:", C.GREEN, C.BOLD)
    for i, ch in enumerate(CHANNELS):
        print_at_c(ROW_TASTE_START+1+i, 1,
                   f"  {CH_LABEL[ch]} {CH_CHEM[ch]} [" + "·"*34 + "]  -.---",
                   C.GRAY)

    for nid in NODE_POS:
        _set_node_color(nid, "idle")

# ══════════════════════════════════════════════════════════════════
#  NODE HIGHLIGHT
# ══════════════════════════════════════════════════════════════════
def _set_node_color(node_id, state):
    fr, fc = NODE_POS[node_id]
    sr = ROW_TOPO_START + fr
    sc = fc + 1
    lbl = NODE_LABELS[node_id]
    col = {
        "active": (C.YELLOW, C.BOLD),
        "idle":   (C.CYAN,),
        "lost":   (C.RED, C.BOLD),
        "done":   (C.GREEN, C.BOLD),
    }.get(state, (C.CYAN,))
    print_at_c(sr, sc, lbl, *col)

# ══════════════════════════════════════════════════════════════════
#  PACKET ANIMATION  (ใช้ ~ แทนสายเพื่อสื่อ WiFi)
# ══════════════════════════════════════════════════════════════════
def _animate_seg(kind, fixed, frm, to, lost, speed):
    dot  = c("◉", C.RED if lost else C.YELLOW, C.BOLD)
    step = 1 if to >= frm else -1
    prev_sr = prev_sc = prev_char = None

    for pos in range(frm, to + step, step):
        if kind == "h":
            sr, sc = ROW_TOPO_START + fixed, pos + 1
        else:
            sr, sc = ROW_TOPO_START + pos, fixed + 1

        if prev_sr is not None and prev_char is not None:
            # คืน ~ เป็นสีเขียว, : เป็นสีเหลือง, อื่นๆ เป็น cyan
            if prev_char == "~":
                print_at_c(prev_sr, prev_sc, prev_char, C.GREEN)
            elif prev_char == ":":
                print_at_c(prev_sr, prev_sc, prev_char, C.YELLOW)
            else:
                print_at_c(prev_sr, prev_sc, prev_char, C.CYAN)

        frame_row = sr - ROW_TOPO_START
        frame_col = sc - 1
        if 0 <= frame_row < len(TOPO_FRAME):
            line = TOPO_FRAME[frame_row]
            prev_char = line[frame_col] if 0 <= frame_col < len(line) else " "
        else:
            prev_char = " "

        print_at(sr, sc, dot)
        prev_sr, prev_sc = sr, sc
        time.sleep(speed)

    if prev_sr is not None and prev_char is not None:
        if prev_char == "~":
            print_at_c(prev_sr, prev_sc, prev_char, C.GREEN)
        elif prev_char == ":":
            print_at_c(prev_sr, prev_sc, prev_char, C.YELLOW)
        else:
            print_at_c(prev_sr, prev_sc, prev_char, C.CYAN)


def animate_link(src_id, dst_id, net_col, lost, speed):
    key = (src_id, dst_id)
    if key in LINK_PATHS:
        for seg in LINK_PATHS[key]:
            _animate_seg(seg[0], seg[1], seg[2], seg[3], lost, speed)

# ══════════════════════════════════════════════════════════════════
#  LOG AREA
# ══════════════════════════════════════════════════════════════════
_log_buf: list = []

def log_clear():
    global _log_buf
    _log_buf = []
    for i in range(LOG_HEIGHT):
        print_at(ROW_LOG_START + i, 1, " " * 82)

def log_write(msg, col=C.GRAY):
    global _log_buf
    ts    = datetime.now().strftime("%H:%M:%S")
    entry = f"  {c(ts, C.GRAY)}  {c(msg, col)}"
    _log_buf.append(entry)
    if len(_log_buf) > LOG_HEIGHT:
        _log_buf = _log_buf[-LOG_HEIGHT:]
    for i in range(LOG_HEIGHT):
        move(ROW_LOG_START + i, 1)
        if i < len(_log_buf):
            ln = _log_buf[i]
            sys.stdout.write(ln + " " * max(0, 82 - vis(ln)))
        else:
            sys.stdout.write(" " * 82)
    sys.stdout.flush()

def status_write(msg, col=C.WHITE):
    move(ROW_STATUS, 1)
    sys.stdout.write(c(msg, col) + " " * max(0, 80 - vis(msg)))
    sys.stdout.flush()

# ══════════════════════════════════════════════════════════════════
#  NODE PROCESSING LOGS  (สะท้อนการทำงานจริงของ ESP32 + IoT)
# ══════════════════════════════════════════════════════════════════
def node_log(node_id, pkt, net):
    n = NETWORK_NODES[node_id]
    log_write(f"▶ {node_id}  {n['name']}  ({n['ip']})  [{n['type']}]", C.CYAN)

    if node_id == "SRC":
        # ESP32 ฝั่งส่ง — sensor อ่านค่า → encode → ส่งผ่าน WiFi
        steps = [
            ("[Sensor]  อ่านค่าสารเคมี 5 ช่อง ผ่าน ADC " + f"{pkt.vec and '16-bit'}",
             C.MAGENTA),
            ("[L7]  Serialize float32[5] → JSON payload",     C.CYAN),
            ("[L6]  gzip compress  ratio ~1.7×",              C.CYAN),
            ("[L5]  Assign seq=" + f"{pkt.seq:04d}"
             + "  session=" + pkt.session[:6],                C.GREEN),
            (f"[L4]  UDP  {pkt.src_port}→{pkt.dst_port}"
             f"  len={pkt.udp_len}B",                         C.GREEN),
            (f"[L3]  IP  src={pkt.src_ip}  dst={pkt.dst_ip}", C.YELLOW),
            (f"[L2]  WiFi 802.11  HMAC={pkt.hmac[:10]}…",    C.YELLOW),
            (f"[L1]  Transmit  2.4 GHz  {net['bw']}",        C.GRAY),
        ]
    elif node_id == "AP1":
        steps = [
            ("[L2]  รับ WiFi frame จาก ESP32 (SRC)",         C.CYAN),
            ("[L3]  Forward packet → Internet / ESPNOW",      C.GREEN),
            ("[App] Upload sensor data → IoT Platform",       C.GREEN),
        ]
    elif node_id == "IOT":
        # Blynk / ESPNOW Cloud relay
        steps = [
            ("[Cloud]  รับ upload จาก Sensor side",           C.CYAN),
            ("[Cloud]  Store taste vector ชั่วคราว",          C.CYAN),
            ("[Cloud]  Convert voltage → concentration",       C.YELLOW),
            ("[Cloud]  Map concentration → intensity level",   C.YELLOW),
            ("[Cloud]  Generate PWM duty cycle สำหรับ EM pump", C.GREEN),
            (f"[Cloud]  Latency upload+download ~{net['lat']}ms", C.GREEN),
        ]
    elif node_id == "AP2":
        steps = [
            ("[L3]  Download actuator command จาก Cloud",     C.CYAN),
            ("[L2]  Forward WiFi frame → ESP32 (DST)",        C.GREEN),
        ]
    else:  # DST — ESP32 ฝั่งรับ + EM Actuator
        dom = CH_LABEL[pkt.dominant].strip()
        steps = [
            ("[L2]  รับ WiFi frame — CRC PASS",               C.GREEN),
            ("[L4]  UDP checksum — PASS",                     C.GREEN),
            ("[L5]  Sequence in-order",                       C.GREEN),
            ("[L6]  Decompress gzip",                         C.CYAN),
            ("[L7]  Reconstruct taste vector float32[5]",     C.CYAN),
            ("[MCU]  แปลง concentration → PWM duty cycle",    C.YELLOW),
            ("[EM]   สั่ง minipump  inject tastant solution", C.MAGENTA),
            (f"[OK]   Dominant: {dom} = {pkt.dominant_value:.3f}", C.GREEN),
        ]

    for msg, col in steps:
        log_write(f"     {msg}", col)
        time.sleep(0.055)

# ══════════════════════════════════════════════════════════════════
#  TASTE VECTOR DISPLAY
# ══════════════════════════════════════════════════════════════════
def draw_taste(pkt):
    for i, ch in enumerate(CHANNELS):
        v   = pkt.vec.get(ch, 0.0)
        bl  = int(v * 34)
        bar = c("█" * bl, CH_COLOR[ch]) + c("·" * (34 - bl), C.GRAY)
        pre = ">>" if ch == pkt.dominant else "  "
        col = C.YELLOW if ch == pkt.dominant else CH_COLOR[ch]
        move(ROW_TASTE_START + 1 + i, 1)
        sys.stdout.write(
            f"  {c(pre, col)} {c(CH_LABEL[ch], col, C.BOLD)} "
            f"{c(CH_CHEM[ch], C.GRAY)} [{bar}] {c(f'{v:.3f}', col, C.BOLD)}"
            + "   "
        )
    sys.stdout.flush()

# ══════════════════════════════════════════════════════════════════
#  MAIN SIMULATION
# ══════════════════════════════════════════════════════════════════
def run_simulation(dataset_key="1", network_key="1", num_packets=3):
    ds  = DATASETS[dataset_key]
    net = NET_PROFILES[network_key]

    alt_screen_on()
    hide_cursor()

    lr = al = 0.0
    sent = received = 0

    try:
        session_id = str(uuid.uuid4())[:8].upper()
        draw_static_frame(ds, net, session_id, num_packets)
        log_clear()

        # speed ปรับตาม latency — IoT cloud อาจช้า ต้องปรับ
        speed    = max(0.015, 0.06 - (net["lat"] / 1000) * 0.5)
        link_seq = [
            ("SRC", "AP1"),
            ("AP1", "IOT"),
            ("IOT", "AP2"),
            ("AP2", "DST"),
        ]

        latencies: list = []

        for pkt_num in range(1, num_packets + 1):
            pkt = Packet(pkt_num - 1, ds)

            status_write(
                f"  Session:{session_id}  Pkt#{pkt_num}/{num_packets}"
                f"  ID:{pkt.id}  Protocol:{net['protocol']}",
                C.CYAN,
            )

            for nid in NODE_POS:
                _set_node_color(nid, "idle")

            delivered = True

            for src_id, dst_id in link_seq:
                _set_node_color(src_id, "active")
                node_log(src_id, pkt, net)
                time.sleep(0.10)

                if random.random() * 100 < net["loss"]:
                    animate_link(src_id, dst_id, net["col"], lost=True, speed=speed)
                    _set_node_color(src_id, "lost")
                    status_write(
                        f"  !! PACKET LOST  {src_id}→{dst_id}"
                        f"  ({net['protocol']} drop)",
                        C.RED,
                    )
                    log_write(
                        f"  !! DROPPED  {src_id}→{dst_id}"
                        f"  (WiFi interference / cloud timeout)",
                        C.RED,
                    )
                    delivered = False
                    break

                animate_link(src_id, dst_id, net["col"], lost=False, speed=speed)
                _set_node_color(src_id, "idle")
                _set_node_color(dst_id, "active")

            if not delivered:
                for nid in NODE_POS:
                    _set_node_color(nid, "idle")
                sent += 1
                status_write(
                    f"  Pkt#{pkt_num} DROPPED  sent={sent}  recv={received}",
                    C.RED,
                )
                time.sleep(0.6)
                continue

            # DST processing
            node_log("DST", pkt, net)

            if random.random() * 100 < net["loss"] * 0.25:
                _set_node_color("DST", "lost")
                log_write("  !! CRC FAIL at DST — frame discarded", C.RED)
                sent += 1
                status_write(
                    f"  Pkt#{pkt_num} CORRUPTED  sent={sent}  recv={received}",
                    C.RED,
                )
                time.sleep(0.6)
                for nid in NODE_POS:
                    _set_node_color(nid, "idle")
                continue

            _set_node_color("DST", "done")

            lat = max(1.0, net["lat"] + random.uniform(
                -net["jitter"], net["jitter"]))
            latencies.append(lat)
            sent     += 1
            received += 1

            draw_taste(pkt)
            log_write(
                f"  >> DELIVERED  lat={lat:.0f}ms"
                f"  dom={CH_LABEL[pkt.dominant].strip()}={pkt.dominant_value:.3f}",
                C.GREEN,
            )
            status_write(
                f"  Pkt#{pkt_num} DELIVERED  lat={lat:.0f}ms"
                f"  sent={sent}  recv={received}",
                C.GREEN,
            )
            time.sleep(0.35)

        # Summary
        lr  = (1 - received / sent) * 100 if sent > 0 else 0.0
        al  = sum(latencies) / len(latencies) if latencies else 0.0
        col = C.CYAN if lr < 5 else C.YELLOW
        status_write(
            f"  DONE  sent={sent}  recv={received}"
            f"  loss={lr:.1f}%  avg_lat={al:.0f}ms  proto={net['protocol']}",
            col,
        )
        log_write(
            f"  === Complete: {received}/{sent} pkts"
            f"  loss={lr:.1f}%  avg_lat={al:.0f}ms ===",
            C.CYAN,
        )

        move(TOTAL_ROWS, 1)
        show_cursor()
        sys.stdout.write(c("  กด Enter เพื่อดำเนินการต่อ… ", C.GRAY))
        sys.stdout.flush()
        try:    input()
        except EOFError: pass

    finally:
        hide_cursor()
        alt_screen_off()
        show_cursor()

    return {"sent": sent, "received": received, "loss": lr, "latency": al}

# ══════════════════════════════════════════════════════════════════
#  SCENARIO: SECURITY
# ══════════════════════════════════════════════════════════════════
def scenario_security():
    alt_screen_on(); hide_cursor()
    try:
        clear_screen()
        BW = 82
        print_at_c(1, 1, "+" + "="*(BW-2) + "+", C.CYAN)
        print_at_c(2, 1, "|" + " "*27 + "SECURITY & INTEGRITY CHECKS" + " "*26 + "|",
                   C.CYAN, C.BOLD)
        print_at_c(3, 1, "+" + "="*(BW-2) + "+", C.CYAN)

        checks = [
            ("HMAC-SHA256 Authentication",     True, "PSK match — frame accepted"),
            ("CRC-32 Frame Check (WiFi FCS)",  True, "ไม่พบ bit-error — data intact"),
            ("Sequence Number Validation",      True, "seq in-order, no gap detected"),
            ("Replay Attack Detection",         True, "Nonce + timestamp — duplicate discarded"),
            ("ESPNOW MAC Address Filter",       True, "Paired MAC only — stranger blocked"),
            ("Blynk Auth Token Verify",         True, "Token valid — cloud session open"),
            ("MTU Size Validation",             True, f"Frame ≤ MTU 1500B — OK"),
            ("IoT Session Timeout Guard",       True, "Timeout=5s — session alive"),
        ]

        r = 5
        for label, ok, detail in checks:
            time.sleep(0.16)
            icon = c("[PASS]", C.GREEN, C.BOLD) if ok else c("[FAIL]", C.RED, C.BOLD)
            print_at(r, 3, f"{icon}  {c(label, C.WHITE)}")
            r += 1
            print_at_c(r, 12, f"└─ {detail}", C.GRAY)
            r += 2

        passed = sum(1 for _, ok, _ in checks if ok)
        print_at(r, 3,
                 f"Security Score: {c(f'{passed}/{len(checks)} checks passed  (100%)', C.GREEN, C.BOLD)}")

        show_cursor(); move(r+2, 1)
        sys.stdout.write(c("  กด Enter เพื่อดำเนินการต่อ… ", C.GRAY))
        sys.stdout.flush()
        try:    input()
        except EOFError: pass
    finally:
        hide_cursor(); alt_screen_off(); show_cursor()

# ══════════════════════════════════════════════════════════════════
#  SCENARIO: OSI WALKTHROUGH  (แสดง stack จริงของ e-Taste)
# ══════════════════════════════════════════════════════════════════
def scenario_osi():
    ds = DATASETS["3"]
    tx = [
        ("L7","Application", "Serialize float32[5] → JSON",          f"Payload {ds['size_kb']} KB raw"),
        ("L6","Presentation","Normalize + gzip compress",             f"Compressed {ds['size_kb']*0.6:.1f} KB"),
        ("L5","Session",     "ESPNOW session / Blynk auth token",     "Session established"),
        ("L4","Transport",   "UDP header  55100→7775  checksum",      f"Datagram {int(ds['size_kb']*1024)+8}B"),
        ("L3","Network",     "IP header  TTL=64  src→dst IP",        "+20 bytes"),
        ("L2","Data Link",   "WiFi 802.11 frame  MAC + FCS",         "Frame queued at AP"),
        ("L1","Physical",    "2.4 GHz  OFDM  802.11n  20MHz ch",     "Bits transmitted OTA"),
    ]

    alt_screen_on(); hide_cursor()
    try:
        clear_screen()
        BW = 82
        print_at_c(1, 1, "+" + "="*(BW-2) + "+", C.MAGENTA)
        print_at_c(2, 1, "|" + " "*28 + "OSI MODEL WALKTHROUGH" + " "*31 + "|",
                   C.MAGENTA, C.BOLD)
        print_at_c(3, 1, "+" + "="*(BW-2) + "+", C.MAGENTA)

        r = 5
        print_at_c(r, 3, "TX PATH — Encapsulation  L7 → L1  (Sensor ESP32):", C.BLUE, C.BOLD)
        r += 1
        for code, name, action, result in tx:
            time.sleep(0.20)
            print_at(r, 3, f"{c(code, C.CYAN, C.BOLD)}  {c(name+':', C.WHITE):<22}"
                     f" {c(action, C.GRAY)}")
            r += 1
            print_at_c(r, 9, f"  └─ {result}", C.GREEN)
            r += 1

        r += 1
        print_at_c(r, 3, "RX PATH — Decapsulation  L1 → L7  (Actuator ESP32):", C.MAGENTA, C.BOLD)
        r += 1
        for code, name, action, result in reversed(tx):
            time.sleep(0.18)
            print_at(r, 3, f"{c(code, C.CYAN, C.BOLD)}  {c(name+':', C.WHITE):<22}"
                     f" {c(action.replace('→','←'), C.GRAY)}")
            r += 1

        r += 1
        print_at_c(r, 3,
                   "[OK]  float32[5] reconstructed → PWM duty cycle → EM pump inject",
                   C.GREEN, C.BOLD)

        show_cursor(); move(r+2, 1)
        sys.stdout.write(c("  กด Enter เพื่อดำเนินการต่อ… ", C.GRAY))
        sys.stdout.flush()
        try:    input()
        except EOFError: pass
    finally:
        hide_cursor(); alt_screen_off(); show_cursor()

# ══════════════════════════════════════════════════════════════════
#  SCENARIO: NETWORK COMPARE  (WiFi / IoT profiles)
# ══════════════════════════════════════════════════════════════════
def scenario_net_compare():
    alt_screen_on(); hide_cursor()
    try:
        clear_screen()
        BW = 82
        print_at_c(1, 1, "+" + "="*(BW-2) + "+", C.CYAN)
        print_at_c(2, 1, "|" + " "*23 + "NETWORK PROFILE COMPARISON  (WiFi/IoT)" + " "*19 + "|",
                   C.CYAN, C.BOLD)
        print_at_c(3, 1, "+" + "="*(BW-2) + "+", C.CYAN)

        r = 5
        hdr = (f"  {'Profile':<20} {'Lat':>8} {'Loss%':>7}"
               f" {'Jitter':>9} {'MTU':>7}  {'BW':<12}  {'Score':>6}")
        print_at_c(r, 1, hdr, C.WHITE, C.BOLD); r += 1
        print_at_c(r, 1, "  " + "─"*74, C.GRAY); r += 1

        for key, cfg in NET_PROFILES.items():
            # score คำนวณ weighted: latency สำคัญมากสำหรับ taste sync
            score = max(0, 100
                        - min(cfg["lat"] / 20, 50)
                        - cfg["loss"] * 3
                        - cfg["jitter"] / 10)
            sc = C.GREEN if score > 70 else (C.YELLOW if score > 40 else C.RED)
            lc = C.RED if cfg["loss"] > 5 else C.GREEN
            print_at(r, 1,
                     f"  {c('['+key+'] '+cfg['name'], cfg['col'], C.BOLD):<36}"
                     f" {c(str(cfg['lat'])+'ms', C.WHITE):>16}"
                     f" {c(str(cfg['loss'])+'%', lc):>15}"
                     f" {c('±'+str(cfg['jitter'])+'ms', C.CYAN):>16}"
                     f" {c(str(cfg['mtu'])+'B', C.GRAY):>13}"
                     f"  {c(cfg['bw'], C.GREEN):<13}"
                     f"  {c(str(int(score)), sc, C.BOLD)}")
            r += 1

        r += 1
        print_at_c(r, 3, "KEY METRICS (IoT Context):", C.WHITE, C.BOLD); r += 1
        concepts = [
            (C.YELLOW,  "Latency     ",
             "= สำคัญมาก! ถ้า > 1000ms ผู้ใช้รับรสชาติหลัง\"เห็น\"ภาพ VR แล้ว"),
            (C.CYAN,    "Jitter      ",
             "= ความไม่สม่ำเสมอ — ทำให้รสชาติสะดุดระหว่างใช้งาน"),
            (C.GREEN,   "Packet Loss ",
             "= รสชาติหายบางช่อง เช่น ได้แค่หวานแต่ไม่ได้เค็ม"),
            (C.MAGENTA, "MTU         ",
             "= ESPNOW จำกัด 250B — payload ต้องกระชับ"),
            (C.GRAY,    "Protocol    ",
             "= ESPNOW เร็วที่สุด, Blynk ยืดหยุ่นระยะไกล"),
        ]
        for col, term, explain in concepts:
            print_at(r, 3,
                     f"{c('◆', col)} {c(term, col, C.BOLD)} {c(explain, C.GRAY)}")
            r += 1

        show_cursor(); move(r+1, 1)
        sys.stdout.write(c("  กด Enter เพื่อดำเนินการต่อ… ", C.GRAY))
        sys.stdout.flush()
        try:    input()
        except EOFError: pass
    finally:
        hide_cursor(); alt_screen_off(); show_cursor()

# ══════════════════════════════════════════════════════════════════
#  SCENARIO: STRESS TEST
# ══════════════════════════════════════════════════════════════════
def scenario_stress():
    run_simulation("4", "5", 2)   # Tom Yum / IoT Cloud Poor
    run_simulation("4", "1", 2)   # Tom Yum / ESPNOW Local

# ══════════════════════════════════════════════════════════════════
#  MENU
# ══════════════════════════════════════════════════════════════════
BW = 82

def draw_main_menu():
    os.system("cls" if sys.platform == "win32" else "clear")
    print(c("+" + "="*(BW-2) + "+", C.BLUE))
    TTN_ART = [
        r"  ████████╗████████╗███╗   ██╗",
        r"     ██╔══╝╚══██╔══╝████╗  ██║",
        r"     ██║      ██║   ██╔██╗ ██║",
        r"     ██║      ██║   ██║╚██╗██║",
        r"     ██║      ██║   ██║ ╚████║",
        r"     ╚═╝      ╚═╝   ╚═╝  ╚═══╝",
    ]
    for line in TTN_ART:
        pad = BW - 2 - len(line)
        print(c("|", C.BLUE) + c(line, C.CYAN, C.BOLD) +
              " "*max(pad,0) + c("|", C.BLUE))

    sub = "T A S T E   D A T A   T R A N S M I S S I O N   N E T W O R K"
    pad = (BW - 2 - len(sub)) // 2
    print(c("|", C.BLUE) + " "*pad + c(sub, C.WHITE, C.BOLD) +
          " "*(BW-2-pad-len(sub)) + c("|", C.BLUE))

    ref = "Based on  e-Taste  (Chen et al., Science Advances 2025)"
    pad = (BW - 2 - len(ref)) // 2
    print(c("|", C.BLUE) + " "*pad + c(ref, C.CYAN) +
          " "*(BW-2-pad-len(ref)) + c("|", C.BLUE))
    print(c("+" + "="*(BW-2) + "+", C.BLUE))
    print()

    print(c("+" + "="*(BW-2) + "+", C.BLUE))
    print(c("|" + " "*36 + "M A I N   M E N U" + " "*27 + "|", C.BLUE, C.BOLD))
    print(c("+" + "="*(BW-2) + "+", C.BLUE))

    items = [
        ("1","TTN Simulation",       "จำลอง packet รสชาติผ่าน ESP32 → WiFi → IoT Cloud"),
        ("2","Quick Demo",           "Tom Yum Soup / ESPNOW Local — 2 packets"),
        ("3","Stress Test",          "IoT Cloud Poor vs ESPNOW Local เปรียบเทียบ"),
        ("4","Security Checks",      "HMAC, CRC, ESPNOW MAC filter, Blynk auth token"),
        ("5","OSI Walkthrough",      "Encapsulation L7→L1 บน WiFi IoT Stack"),
        ("6","Network Profiles",     "เปรียบเทียบ ESPNOW / WiFi / IoT Cloud (Good-Poor)"),
    ]
    for key, title, desc in items:
        print(f"  {c('['+key+']', C.YELLOW, C.BOLD)}"
              f"  {c(title, C.WHITE):<28} {c(desc, C.GRAY)}")
    print(c("+" + "─"*(BW-2) + "+", C.BLUE))
    print(f"  {c('[0]', C.YELLOW, C.BOLD)}"
          f"  {c('Exit', C.WHITE):<28} {c('ออกจากโปรแกรม', C.GRAY)}")
    print(c("+" + "="*(BW-2) + "+", C.BLUE))
    print()


def pick_dataset():
    print()
    print(c("  ┌─ TASTE DATASETS ──────────────────────────────────────────────┐", C.CYAN))
    for key, d in DATASETS.items():
        dom = max(["ch_sweet","ch_salty","ch_sour","ch_bitter","ch_umami"],
                  key=lambda k: d[k])
        dom_label = CH_LABEL[dom].strip()
        print(f"  {c('['+key+']', C.YELLOW, C.BOLD)}"
              f"  {c(d['label'], C.WHITE):<22}"
              f"  {c(d['id'], C.GRAY):<9}"
              f"  {c(str(d['size_kb'])+' KB', C.CYAN):<8}"
              f"  {d['adc_bits']}-bit @ {c(d['sample_rate'], C.CYAN)}"
              f"  [{c(d['origin'], C.MAGENTA)}]"
              f"  dom:{c(dom_label, C.YELLOW)}")
    print(c("  └───────────────────────────────────────────────────────────────┘", C.CYAN))
    print()
    while True:
        try:
            ch = input(c("  เลือก dataset [1-8]: ", C.YELLOW)).strip()
            if ch in DATASETS:   return ch
            print(c("  กรุณาใส่ 1-8", C.RED))
        except (KeyboardInterrupt, EOFError):
            return "4"


def pick_network():
    print()
    print(c("  ┌─ NETWORK PROFILES ────────────────────────────────────────────┐", C.CYAN))
    for key, cfg in NET_PROFILES.items():
        score = max(0, 100 - min(cfg["lat"]/20,50) - cfg["loss"]*3 - cfg["jitter"]/10)
        sc = C.GREEN if score > 70 else (C.YELLOW if score > 40 else C.RED)
        print(f"  {c('['+key+']', C.YELLOW, C.BOLD)}"
              f"  {c(cfg['name'], cfg['col'], C.BOLD):<22}"
              f"  lat:{c(str(cfg['lat'])+'ms', C.WHITE):<14}"
              f"  loss:{c(str(cfg['loss'])+'%', C.WHITE):<8}"
              f"  score:{c(str(int(score)), sc, C.BOLD)}")
    print(c("  └───────────────────────────────────────────────────────────────┘", C.CYAN))
    print()
    while True:
        try:
            ch = input(c("  เลือก network [1-5]: ", C.YELLOW)).strip()
            if ch in NET_PROFILES: return ch
            print(c("  กรุณาใส่ 1-5", C.RED))
        except (KeyboardInterrupt, EOFError):
            return "1"


def pick_packets():
    while True:
        try:
            n = input(c("  จำนวน packet [1-5, default=3]: ", C.YELLOW)).strip()
            if n == "": return 3
            n = int(n)
            if 1 <= n <= 5: return n
            print(c("  กรุณาใส่ 1-5", C.RED))
        except (ValueError, KeyboardInterrupt, EOFError):
            return 3

# ══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description="TTN v4 — e-Taste Network Simulation (terminal-only)"
    )
    parser.add_argument("--scenario", "-s",
                        choices=["1","2","3","4","5","6"])
    parser.add_argument("--dataset",  "-d",
                        choices=list(DATASETS.keys()), default="4")
    parser.add_argument("--network",  "-n",
                        choices=list(NET_PROFILES.keys()), default="1")
    parser.add_argument("--packets",  "-p",
                        type=int, default=3)
    args = parser.parse_args()

    dispatch = {
        "1": lambda: run_simulation(args.dataset, args.network, args.packets),
        "2": lambda: run_simulation("4", "1", 2),
        "3": scenario_stress,
        "4": scenario_security,
        "5": scenario_osi,
        "6": scenario_net_compare,
    }

    try:
        if args.scenario:
            dispatch[args.scenario]()
            return

        while True:
            draw_main_menu()
            try:
                choice = input(c("  เลือกตัวเลือก: ", C.YELLOW, C.BOLD)).strip()
            except (KeyboardInterrupt, EOFError):
                break

            if choice == "0":
                break
            elif choice == "1":
                os.system("cls" if sys.platform == "win32" else "clear")
                ds_key  = pick_dataset()
                net_key = pick_network()
                pkts    = pick_packets()
                run_simulation(ds_key, net_key, pkts)
            elif choice in dispatch:
                dispatch[choice]()
            else:
                print(c("  ตัวเลือกไม่ถูกต้อง กด Enter แล้วลองใหม่", C.RED))
                try:    input()
                except EOFError: pass

    except KeyboardInterrupt:
        pass
    finally:
        show_cursor()
        os.system("cls" if sys.platform == "win32" else "clear")
        print(c("=" * 66, C.CYAN))
        print(c(" "*10 + "TTN v4 — Taste Data Transmission Network", C.CYAN, C.BOLD))
        print(c(" "*12 + "Based on e-Taste  (Chen et al., Sci. Adv. 2025)", C.CYAN))
        print(c(" "*14 + "Data Communication & Computer Networks", C.CYAN))
        print(c("=" * 66, C.CYAN))
        print()

if __name__ == "__main__":
    main()