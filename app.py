import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime, timedelta

# ===============================
# Synthetic Scenarios
# ===============================
SCENARIOS = {
    "Healthy connection": {
        "product": "Streaming TV",
        "device_type": "Streaming device",
        "connection_method": "5GHz WiFi",
        "rssi": -55,
        "packet_loss": 0.3,
        "retransmission_rate": 3,
        "rapid_reconnects": 0,
        "telemetry_age_minutes": 12,
        "line_health": "OK",
        "known_outage": False,
        "repeat_issue_7_days": False,
        "previous_outcome": "No previous journey",
        "hub_model": "Hub 6",
        "pod_present": False,
        "customer_symptom": "No issue reported",
        "customer_impact_score": 1,
        "equipment_health": "OK"
    },
    "Buffering on streaming device": {
        "product": "Streaming TV",
        "device_type": "Streaming device",
        "connection_method": "2.4GHz WiFi",
        "rssi": -82,
        "packet_loss": 2.8,
        "retransmission_rate": 14,
        "rapid_reconnects": 3,
        "telemetry_age_minutes": 15,
        "line_health": "OK",
        "known_outage": False,
        "repeat_issue_7_days": True,
        "previous_outcome": "Self-serve guidance shown",
        "hub_model": "Hub 6",
        "pod_present": True,
        "customer_symptom": "Buffering or poor picture quality",
        "customer_impact_score": 7,
        "equipment_health": "OK"
    },
}

# ===============================
# Helper Functions
# ===============================
def safe_value(value, suffix=""):
    if value is None:
        return "Not available"
    return f"{value}{suffix}"

def rag_badge(rag):
    return {"Green":"🟢 Green","Amber":"🟠 Amber","Red":"🔴 Red","Grey":"⚪ Grey"}.get(rag, rag)

def calculate_rssi_rag(rssi):
    if rssi is None:
        return "Grey", "WiFi signal telemetry unavailable"
    if rssi >= -67:
        return "Green", "WiFi signal strength looks healthy"
    elif -75 <= rssi < -67:
        return "Amber", "WiFi signal strength is degraded"
    else:
        return "Red", "WiFi signal strength is poor"

def calculate_packet_loss_rag(packet_loss):
    if packet_loss is None:
        return "Grey", "Packet loss telemetry unavailable"
    if packet_loss <= 1:
        return "Green", "Packet loss is low"
    elif packet_loss <= 3:
        return "Amber", "Packet loss is elevated"
    else:
        return "Red", "Packet loss is high"

def calculate_retransmission_rag(rate):
    if rate is None:
        return "Grey", "Retransmission telemetry unavailable"
    if rate <= 5:
        return "Green", "Retransmissions are low"
    elif rate <= 15:
        return "Amber", "Retransmissions are elevated"
    else:
        return "Red", "Retransmissions are high"

def calculate_reconnect_rag(rapid_reconnects):
    if rapid_reconnects is None:
        return "Grey", "Reconnect telemetry unavailable"
    if rapid_reconnects <= 1:
        return "Green", "Reconnect behaviour looks stable"
    elif rapid_reconnects <= 4:
        return "Amber", "Some reconnect instability detected"
    else:
        return "Red", "Frequent reconnect instability detected"

def calculate_line_health_rag(line_health):
    if line_health == "OK":
        return "Green", "Line health looks OK"
    if line_health == "Unstable":
        return "Amber", "Line health appears unstable"
    if line_health == "Fail":
        return "Red", "Line health has failed"
    return "Grey", "Line health is unknown"

def calculate_telemetry_age_rag(age):
    if age is None:
        return "Grey", "Telemetry timestamp unavailable"
    if age <= 30:
        return "Green", "Telemetry is fresh"
    elif age <= 120:
        return "Amber", "Telemetry is slightly old"
    else:
        return "Grey", "Telemetry is too old for confident diagnosis"

def calculate_equipment_health_rag(equipment_health):
    if equipment_health == "OK":
        return "Green", "No suspected equipment fault"
    if equipment_health == "Suspected fault":
        return "Red", "Equipment fault suspected"
    return "Grey", "Equipment health unknown"

def build_marker_results(t):
    results = []
    rssi_rag, rssi_reason = calculate_rssi_rag(t["rssi"])
    results.append({"Marker": "WiFi signal strength", "Value": safe_value(t["rssi"], " dBm"), "RAG": rssi_rag, "Reason": rssi_reason})
    packet_rag, packet_reason = calculate_packet_loss_rag(t["packet_loss"])
    results.append({"Marker": "Packet loss", "Value": safe_value(t["packet_loss"], "%"), "RAG": packet_rag, "Reason": packet_reason})
    retrans_rag, retrans_reason = calculate_retransmission_rag(t["retransmission_rate"])
    results.append({"Marker": "Retransmission rate", "Value": safe_value(t["retransmission_rate"], "%"), "RAG": retrans_rag, "Reason": retrans_reason})
    reconnect_rag, reconnect_reason = calculate_reconnect_rag(t["rapid_reconnects"])
    results.append({"Marker": "Rapid reconnects", "Value": safe_value(t["rapid_reconnects"]), "RAG": reconnect_rag, "Reason": reconnect_reason})
    line_rag, line_reason = calculate_line_health_rag(t["line_health"])
    results.append({"Marker": "Line health", "Value": t["line_health"], "RAG": line_rag, "Reason": line_reason})
    age_rag, age_reason = calculate_telemetry_age_rag(t["telemetry_age_minutes"])
    results.append({"Marker": "Telemetry freshness", "Value": f"{t['telemetry_age_minutes']} minutes old", "RAG": age_rag, "Reason": age_reason})
    equipment_rag, equipment_reason = calculate_equipment_health_rag(t["equipment_health"])
    results.append({"Marker": "Equipment health", "Value": t["equipment_health"], "RAG": equipment_rag, "Reason": equipment_reason})
    return results

def rollup_rag(marker_results):
    rags = [m["RAG"] for m in marker_results]
    if "Grey" in rags:
        return "Grey"
    if "Red" in rags:
        return "Red"
    if "Amber" in rags:
        return "Amber"
    return "Green"

# Build hypotheses, choose best hypothesis, decide action functions here (keep your logic)...

def build_hypotheses(t, marker_results):
    # Your logic from above...

    lookup = {m["Marker"]: m for m in marker_results}
    hypotheses = []
    # ... Same as before ...
    # For brevity, copy your existing function here
    # ...

def choose_best_hypothesis(hypotheses):
    # ... existing logic, copy from your code ...
    pass

def decide_action(t, chosen, overall_rag):
    # ... existing logic, copy from your code ...
    pass

# Function to randomise telemetry like yours
def randomise_scenario(base):
    t = base.copy()
    if t["rssi"] is not None:
        t["rssi"] = max(-95, min(-30, t["rssi"] + random.randint(-6,6)))
    if t["packet_loss"] is not None:
        t["packet_loss"] = max(0, min(20, t["packet_loss"] + random.uniform(-1.8,1.8)))
    if t["retransmission_rate"] is not None:
        t["retransmission_rate"] = max(0, min(50, t["retransmission_rate"] + random.randint(-5,5)))
    if t["rapid_reconnects"] is not None:
        t["rapid_reconnects"] = max(0, min(20, t["rapid_reconnects"] + random.randint(-2,2)))
    t["telemetry_age_minutes"] = max(1, min(600, t["telemetry_age_minutes"] + random.randint(-8, 8)))
    return t

# Generate synthetic history for a scenario for trends
def generate_synthetic_history(scenario_key):
    base = SCENARIOS[scenario_key]
    history = []
    now = datetime.now()
    for i in range(10):
        timestamp = now - timedelta(hours=10 - i)
        def jitter(val, low, high, scale=3):
            if val is None:
                return None
            v = val + random.uniform(-scale, scale)
            return max(low, min(high, v))
        history.append({
            "timestamp": timestamp,
            "rssi": jitter(base["rssi"], -95, -30),
            "packet_loss": jitter(base["packet_loss"], 0, 20),
            "retransmission_rate": jitter(base["retransmission_rate"], 0, 50),
            "rapid_reconnects": max(0, int(base["rapid_reconnects"] + random.randint(-1, 1)))
        })
    return history

def plot_trends(history):
    df = pd.DataFrame(history).set_index('timestamp')
    df = df[['rssi', 'packet_loss', 'retransmission_rate', 'rapid_reconnects']]
    st.line_chart(df)
    return df

def summarize_trends(df):
    summaries = []
    if df["rssi"].iloc[-1] < df["rssi"].iloc[0]:
        summaries.append("WiFi signal strength has decreased over time.")
    else:
        summaries.append("WiFi signal strength is stable or improved.")
    if df["packet_loss"].iloc[-1] > df["packet_loss"].iloc[0]:
        summaries.append("Packet loss has increased, possibly impacting quality.")
    else:
        summaries.append("Packet loss is stable or improved.")
    if df["retransmission_rate"].iloc[-1] > df["retransmission_rate"].iloc[0]:
        summaries.append("Retransmission rate has increased, indicating rising errors.")
    else:
        summaries.append("Retransmission rate is stable or improved.")
    if df["rapid_reconnects"].iloc[-1] > df["rapid_reconnects"].iloc[0]:
        summaries.append("Rapid reconnects are more frequent, showing instability.")
    else:
        summaries.append("Rapid reconnects stable or decreased.")
    return " ".join(summaries)

# Your detailed messages builder(s)
# Your run_agentic_test walking through the diagnostic

# Session state initialization

if "result" not in st.session_state:
    st.session_state.result = None
if "telemetry" not in st.session_state:
    st.session_state.telemetry = None
if "scenario_used" not in st.session_state:
    st.session_state.scenario_used = None

# UI Initialization
st.title("🛰️ Test SC Enhanced Agentic AI")

random_mode = st.sidebar.checkbox("Random scenario on each test", True)
selected_scenario = st.sidebar.selectbox("Or pick specific scenario", list(SCENARIOS.keys()))

st.markdown("## Check your connection")

if st.button("🚀 Test my connection"):
    scenario = random.choice(list(SCENARIOS.keys())) if random_mode else selected_scenario
    st.session_state.scenario_used = scenario
    telemetry = randomise_scenario(SCENARIOS[scenario])
    st.session_state.telemetry = telemetry
    # Call your function that runs the test, returns all diagnostics etc.
    st.session_state.result = run_agentic_test(telemetry, scenario)

if st.session_state.result:
    result = st.session_state.result
    action = result["action"]
    cols = st.columns(4)
    cols[0].metric("Overall status", rag_badge(result["overall_rag"]))
    cols[1].metric("Outcome", action["Outcome"])
    cols[2].metric("Confidence", result["chosen"]["Confidence"])
    cols[3].metric("Next step", action["Agentic_level"])

    st.subheader("Customer message")
    st.success(result["detailed_customer_message"])

    st.subheader("Recommended next step")
    st.write(action["Action"])

    st.subheader("Connection metrics trends")
    df_hist = plot_trends(result["history"])
    st.info(summarize_trends(df_hist))

    st.subheader("Telemetry input data")
    telemetry_df = pd.DataFrame([
        {"Field": "Product", "Value": st.session_state.telemetry["product"]},
        {"Field": "Device type", "Value": st.session_state.telemetry["device_type"]},
        {"Field": "Connection method", "Value": st.session_state.telemetry["connection_method"]},
        {"Field": "RSSI", "Value": safe_value(st.session_state.telemetry["rssi"]," dBm")},
        {"Field": "Packet loss", "Value": safe_value(st.session_state.telemetry["packet_loss"],"%")},
        {"Field": "Retransmission rate", "Value": safe_value(st.session_state.telemetry["retransmission_rate"],"%")},
        {"Field": "Rapid reconnects", "Value": safe_value(st.session_state.telemetry["rapid_reconnects"])},
        {"Field": "Telemetry age", "Value": f"{st.session_state.telemetry['telemetry_age_minutes']} minutes"},
        {"Field": "Line health", "Value": st.session_state.telemetry["line_health"]},
        {"Field": "Known outage", "Value": "Yes" if st.session_state.telemetry["known_outage"] else "No"},
        {"Field": "Equipment health", "Value": st.session_state.telemetry["equipment_health"]},
        {"Field": "Customer symptom", "Value": st.session_state.telemetry["customer_symptom"]},
        {"Field": "Customer impact score", "Value": f"{st.session_state.telemetry['customer_impact_score']}/10"},
    ])
    st.dataframe(telemetry_df, use_container_width=True)

    st.subheader("Marker evaluations")
    marker_df = pd.DataFrame(result["marker_results"])
    marker_df["RAG"] = marker_df["RAG"].apply(rag_badge)
    st.dataframe(marker_df, use_container_width=True)

    st.subheader("Diagnostic reasoning narrative")
    st.text_area("Reasoning", result["diagnostic_trace_text"], height=250, disabled=True)

else:
    st.info("Click 'Test my connection' to get started.")




