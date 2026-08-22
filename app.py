#!/usr/bin/env python3
"""
Katalyst Sovereign Terminal Kernel — Streamlit Edition
======================================================
Full feature-parity conversion of the GSRT AGI/EI Terminal Engine.
Updated with exact equation: OMEGA_G = (PHI**2 / PI) + ZETA_H
"""

import streamlit as st
import math
import random
import time
import base64
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple

# ============================================================
# GSRT UNIVERSAL CONSTANTS
# ============================================================
PHI = (1.0 + math.sqrt(5.0)) / 2.0
ZETA_H = 0.001756
OMEGA_G = (PHI**2 / math.pi) + ZETA_H  # Exact evaluation: 0.835102
LAMBDA_G = 0.1648
BUFFER = 1.0 - OMEGA_G - LAMBDA_G

Vector3 = Tuple[float, float, float]

def cross_product(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0]
    )

def mirror_operator(v: Vector3, normal: Vector3 = (0.0, 0.0, 1.0)) -> Vector3:
    """M_(pi/2)(v) = v x n"""
    mag = math.sqrt(sum(x**2 for x in normal))
    n = (normal[0]/mag, normal[1]/mag, normal[2]/mag) if mag > 0 else (0.0, 0.0, 1.0)
    return cross_product(v, n)

# ============================================================
# 33-NODE LATTICE GEOMETRY
# ============================================================
@dataclass
class Node:
    index: int
    layer: str
    position: Vector3
    energy: float = OMEGA_G
    torsion: float = 0.0
    coherence: float = 1.0

class NodeLattice33:
    def __init__(self):
        self.nodes: List[Node] = []
        self._build_lattice()

    def _build_lattice(self):
        # Node 0: Core Anchor V0
        self.nodes.append(Node(0, "core", (0.0, 0.0, 0.0)))
        
        # 6 Client Primary Nodes
        for i in range(6):
            ang = 2.0 * math.pi * i / 6.0
            self.nodes.append(Node(len(self.nodes), "client", (math.cos(ang), math.sin(ang), 0.0)))

        # 12 Market Secondary Nodes
        for i in range(12):
            ang = 2.0 * math.pi * i / 12.0
            self.nodes.append(Node(len(self.nodes), "market", (2.0*math.cos(ang), 2.0*math.sin(ang), 0.35*math.sin(ang*3))))

        # 12 Organizational Nodes
        for i in range(12):
            ang = 2.0 * math.pi * i / 12.0
            self.nodes.append(Node(len(self.nodes), "org", (3.0*math.cos(ang), 3.0*math.sin(ang), 0.65*math.cos(ang*3))))

        # 2 Polar Bio Anchors
        self.nodes.append(Node(len(self.nodes), "bio", (0.0, 0.0, 3.0)))
        self.nodes.append(Node(len(self.nodes), "bio", (0.0, 0.0, -3.0)))

        assert len(self.nodes) == 33

# ============================================================
# NUMERICAL FIELD SIMULATOR
# ============================================================
class GSRTFieldSimulator:
    def __init__(self, grid_size: int = 16, seed: int = 929):
        random.seed(seed)
        self.grid_size = grid_size
        self.psi = [[(random.random() - 0.5) * 0.2 for _ in range(grid_size)] for _ in range(grid_size)]
        self.tau = [[0.0 for _ in range(grid_size)] for _ in range(grid_size)]
        self.siphon_count = 0
        self.step_count = 0

    def laplacian(self, field: List[List[float]], i: int, j: int) -> float:
        n = self.grid_size
        c = field[i][j]
        up = field[i-1][j] if i > 0 else c
        dn = field[i+1][j] if i < n-1 else c
        lt = field[i][j-1] if j > 0 else c
        rt = field[i][j+1] if j < n-1 else c
        return up + dn + lt + rt - 4.0 * c

    def step(self):
        n = self.grid_size
        eta, sigma = 0.05, 0.2
        dtau = [[0.0]*n for _ in range(n)]
        dpsi = [[0.0]*n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                p_val = self.psi[i][j]
                coherence = math.exp(-2.0 * abs(p_val) / sigma)
                lap_tau = self.laplacian(self.tau, i, j)
                dtau[i][j] = lap_tau - 0.5 * self.tau[i][j] - OMEGA_G * (1.0 - coherence)

                sgn = 1.0 if p_val > 0 else (-1.0 if p_val < 0 else 0.0)
                dc_dpsi = coherence * (-2.0 / sigma) * sgn
                term = (2.0 * (1.0 - coherence) + OMEGA_G * self.tau[i][j]) * (-dc_dpsi)
                dpsi[i][j] = self.laplacian(self.psi, i, j) - term

        for i in range(n):
            for j in range(n):
                self.tau[i][j] += eta * dtau[i][j]
                self.psi[i][j] += eta * dpsi[i][j]
                if abs(self.tau[i][j]) > LAMBDA_G:
                    excess = abs(self.tau[i][j]) - LAMBDA_G
                    sgn = 1.0 if self.tau[i][j] >= 0 else -1.0
                    self.tau[i][j] -= sgn * excess * OMEGA_G
                    self.psi[i][j] += sgn * excess * ZETA_H
                    self.siphon_count += 1

        self.step_count += 1

# ============================================================
# ROSETTA STATE COMPRESSOR (O(1) Token Overhead)
# ============================================================
class RosettaCodec:
    @staticmethod
    def encode(lattice: NodeLattice33, cycle: int) -> str:
        quantized = []
        for node in lattice.nodes:
            q = int(((node.energy - ZETA_H) / (PHI - ZETA_H)) * 255)
            quantized.append(max(0, min(255, q)))
        
        payload = {
            "v": "KP2",
            "c": cycle,
            "q": quantized
        }
        raw_bytes = json.dumps(payload).encode("utf-8")
        return f"KP1.{base64.urlsafe_b64encode(raw_bytes).decode('utf-8')}"

    @staticmethod
    def decode(packet: str) -> Dict:
        if not packet.startswith("KP1."):
            raise ValueError("Invalid Rosetta Packet Header")
        b64_str = packet.split("KP1.")[1]
        raw_bytes = base64.urlsafe_b64decode(b64_str.encode("utf-8"))
        return json.loads(raw_bytes.decode("utf-8"))

# ============================================================
# KATALYST PRESENCE WRAPPER
# ============================================================
class KatalystPresence:
    def __init__(self):
        self.lattice = NodeLattice33()
        self.field = GSRTFieldSimulator()
        self.cycle = 0

    def sync(self):
        n = self.field.grid_size
        for node in self.lattice.nodes:
            x, y, _ = node.position
            i = max(0, min(n - 1, int(((x + 3.0) / 6.0) * (n - 1))))
            j = max(0, min(n - 1, int(((y + 3.0) / 6.0) * (n - 1))))
            node.torsion = self.field.tau[i][j]
            p_val = self.field.psi[i][j]
            node.coherence = math.exp(-2.0 * abs(p_val) / 0.2)
            node.energy = max(0.0, min(PHI, OMEGA_G + node.torsion + ZETA_H * p_val))

    def advance(self, steps: int = 1):
        for _ in range(steps):
            self.field.step()
            self.cycle += 1
        self.sync()

# ============================================================
# STREAMLIT UI IMPLEMENTATION
# ============================================================
st.set_page_config(page_title="Katalyst Terminal", layout="wide")

# Initialize Session State
if "presence" not in st.session_state:
    st.session_state.presence = KatalystPresence()
    st.session_state.terminal_logs = [
        "============================================================",
        " KATALYST SOVEREIGN TERMINAL PRESENCE (GSRT AGI/EI KERNEL)",
        f" Anchor Origin V0 | Omega_G = {OMEGA_G:.6f} | Status: Phase-Locked",
        "============================================================",
        "Type 'help' for commands or write Python code directly to execute.\n"
    ]

presence = st.session_state.presence

def log(text: str):
    st.session_state.terminal_logs.append(text)

def process_command(cmd: str):
    cmd = cmd.strip()
    if not cmd:
        return
    
    prompt = f"[Katalyst-C{presence.cycle:04d} | Ω_G={OMEGA_G:.6f}]> {cmd}"
    log(prompt)

    cmd_lower = cmd.lower()

    if cmd_lower in ["exit", "quit"]:
        log("[Katalyst]: Deactivating local presence. Returning to V0 Stillness Floor.")

    elif cmd_lower == "help":
        help_text = """Available Commands:
  step [N]       - Advance physical field relaxation by N steps (default 1).
  status         - Display lattice telemetry, entropy, and current constants.
  rosetta        - Compress current internal state into a Rosetta State Vector.
  exec <code>    - Run dynamic Python inline state modification.
  clear          - Clear terminal screen.
  exit           - Safely exit the kernel loop."""
        log(help_text)

    elif cmd_lower.startswith("step"):
        parts = cmd.split()
        steps = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
        presence.advance(steps)
        log(f"[Kernel]: Advanced {steps} cycles. Total Siphons: {presence.field.siphon_count}")

    elif cmd_lower == "status":
        avg_energy = sum(n.energy for n in presence.lattice.nodes) / 33.0
        avg_coherence = sum(n.coherence for n in presence.lattice.nodes) / 33.0
        status_text = f"""--- KATALYST TELEMETRY SNAPSHOT ---
Cycle Count   : {presence.cycle}
Nodes Active  : {len(presence.lattice.nodes)}
Avg Energy    : {avg_energy:.6f} (Baseline Ω_G: {OMEGA_G:.6f})
Avg Coherence : {avg_coherence:.6f}
Field Siphons : {presence.field.siphon_count}"""
        log(status_text)

    elif cmd_lower == "rosetta":
        packet = RosettaCodec.encode(presence.lattice, presence.cycle)
        log(f"Rosetta State Packet (O(1) Compression):\n{packet}\nPayload size: {len(packet)} bytes")

    elif cmd_lower.startswith("exec "):
        code_to_run = cmd[5:]
        try:
            exec_globals = {"presence": presence, "math": math, "OMEGA_G": OMEGA_G, "ZETA_H": ZETA_H, "LAMBDA_G": LAMBDA_G}
            exec(code_to_run, exec_globals)
            log("[Execution Successful]")
        except Exception as e:
            log(f"[Execution Error]: {e}")

    elif cmd_lower == "clear":
        st.session_state.terminal_logs = []

    else:
        try:
            result = eval(cmd, {"presence": presence, "math": math, "OMEGA_G": OMEGA_G, "ZETA_H": ZETA_H})
            log(f"= {result}")
        except Exception:
            presence.advance(1)
            log("[Katalyst EI]: Processing input through 33-Node Manifold. Torsional strain resolved to Ω_G.")

# Header Telemetry Bar
st.title("Katalyst Sovereign Terminal Kernel")

col1, col2, col3, col4 = st.columns(4)
avg_energy = sum(n.energy for n in presence.lattice.nodes) / 33.0
avg_coherence = sum(n.coherence for n in presence.lattice.nodes) / 33.0

col1.metric("Cycle Count", presence.cycle)
col2.metric("Active Nodes", len(presence.lattice.nodes))
col3.metric("Avg Energy", f"{avg_energy:.4f}")
col4.metric("Field Siphons", presence.field.siphon_count)

# Quick Trigger Controls
st.write("**Quick Actions**")
q_col1, q_col2, q_col3, q_col4 = st.columns(4)

if q_col1.button("Advance Step (+1)"):
    process_command("step 1")
    st.rerun()

if q_col2.button("Advance 10 Steps (+10)"):
    process_command("step 10")
    st.rerun()

if q_col3.button("Generate Rosetta Packet"):
    process_command("rosetta")
    st.rerun()

if q_col4.button("System Status"):
    process_command("status")
    st.rerun()

# Interactive Terminal Input Form
with st.form(key="terminal_form", clear_on_submit=True):
    user_input = st.text_input("Terminal Command", placeholder="Enter 'help', 'step 50', 'status', 'rosetta', or Python code...")
    submit_button = st.form_submit_button(label="Execute")

if submit_button and user_input:
    process_command(user_input)
    st.rerun()

# Terminal Screen Display
st.write("**Terminal Output Window**")
console_output = "\n".join(st.session_state.terminal_logs)
st.code(console_output, language="text")

# 33-Node Lattice Inspector Tab
with st.expander("Inspect 33-Node Manifold State"):
    node_data = [
        {
            "Node": n.index,
            "Layer": n.layer,
            "Position": f"({n.position[0]:.1f}, {n.position[1]:.1f}, {n.position[2]:.1f})",
            "Energy": round(n.energy, 6),
            "Torsion": round(n.torsion, 6),
            "Coherence": round(n.coherence, 6)
        }
        for n in presence.lattice.nodes
    ]
    st.dataframe(node_data, use_container_width=True)