import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Test SC", layout="wide")

st.title("🛰️ Test SC - Demo")

st.write("This demo uses synthetic telemetry to show how a diagnostic system could work.")

# =====================
# RANDOM TELEMETRY
# =====================

def generate_telemetry():
    return {
        "RSSI": random.randint(-90, -40),
        "Packet Loss (%)": round(random.uniform(0, 10), 1),
        "Retransmission (%)": random.randint(0, 30),
        "Reconnects": random.randint(0, 10),
        "Line Health": random.choice(["OK", "Unstable", "Fail"]),
        "Connection": random.choice(["Ethernet", "5GHz WiFi", "2.4GHz WiFi"]),
        "Customer Symptom": random.choice([
            "Buffering",
            "Slow speed",
            "Drops",
            "No connection"
        ])
    }

telemetry = generate_telemetry()

# =====================
# SHOW TELEMETRY
# =====================

st.subheader("📡 Telemetry")

df = pd.DataFrame(list(telemetry.items()), columns=["Metric", "Value"])
st.dataframe(df, use_container_width=True)

# =====================
# SIMPLE LOGIC
# =====================

def diagnose(t):
    if t["Line Health"] == "Fail":
        return "Line issue", "Escalate to network check"
    if t["RSSI"] < -75:
        return "Poor WiFi signal", "Improve placement / WiFi optimisation"
    if t["Packet Loss (%)"] > 5:
        return "Interference / congestion", "Optimise WiFi channel"
    return "No major issue detected", "Reassure / monitor"

diagnosis, action = diagnose(telemetry)

# =====================
# RESULT
# =====================

st.subheader("🧠 Diagnosis")
st.write(diagnosis)

st.subheader("➡️ Recommended Action")
st.write(action)

# =====================
# EXPLANATION
# =====================

st.subheader("📖 Explanation")

st.write(f"""
Based on the synthetic telemetry:

- RSSI: {telemetry["RSSI"]}
- Packet Loss: {telemetry["Packet Loss (%)"]}%
- Line Health: {telemetry["Line Health"]}

The system determined:

**{diagnosis}**

Next best step:

**{action}**
""")

