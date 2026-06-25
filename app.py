import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# --- Synthetic scenarios ---
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
    }
}

# --- Helper functions ---

def safe_value(value, suffix=""):
    return "Not available" if value is None else f"{value}{suffix}"

def rag_badge(rag):
    return {
        "Green":"🟢 Green",
        "Amber":"🟠 Amber",
        "Red":"🔴 Red",
        "Grey":"⚪ Grey"
    }.get(rag, rag)

# (Include all your other helper functions and diagnostic logic here...)

# Updated telemetry tab with user-friendly descriptions
def render_telemetry_tab(telemetry):
    telemetry_info = [
        {"Field": "Product", "Value": telemetry["product"], "Description": "Type of service being tested"},
        {"Field": "Device Type", "Value": telemetry["device_type"], "Description": "Device you are using"},
        {"Field": "Connection Method", "Value": telemetry["connection_method"], "Description": "How your device connects"},
        {"Field": "RSSI", "Value": safe_value(telemetry["rssi"], " dBm"), "Description": "WiFi signal strength (connection quality)"},
        {"Field": "Packet Loss", "Value": safe_value(telemetry["packet_loss"], "%"), "Description": "Percentage of data packets lost"},
        {"Field": "Retransmission Rate", "Value": safe_value(telemetry["retransmission_rate"], "%"), "Description": "Frequency of data retransmission due to errors"},
        {"Field": "Rapid Reconnects", "Value": safe_value(telemetry["rapid_reconnects"]), "Description": "Number of quick disconnects/reconnects"},
        {"Field": "Telemetry Age", "Value": f"{telemetry['telemetry_age_minutes']} minutes", "Description": "How recent the data is"},
        {"Field": "Line Health", "Value": telemetry["line_health"], "Description": "Overall quality of your broadband line"},
        {"Field": "Known Outage", "Value": "Yes" if telemetry["known_outage"] else "No", "Description": "Is there a known service outage?"},
        {"Field": "Equipment Health", "Value": telemetry["equipment_health"], "Description": "Condition of your equipment"},
        {"Field": "Customer Symptom", "Value": telemetry["customer_symptom"], "Description": "What problem you reported"},
        {"Field": "Customer Impact Score", "Value": f"{telemetry['customer_impact_score']}/10", "Description": "Severity of your connection issue"}
    ]
    st.table(pd.DataFrame(telemetry_info).set_index("Field"))

# Main Streamlit app starts here, your existing diagnostic logic integrated

if "result" not in st.session_state:
    st.session_state.result = None
if "telemetry" not in st.session_state:
    st.session_state.telemetry = None
if "scenario_used" not in st.session_state:
    st.session_state.scenario_used = None

st.title("🛰️ Test SC Agentic AI Demo")

random_mode = st.sidebar.checkbox("Random scenario every test", True)
selected_scenario = st.sidebar.selectbox("Or pick specific scenario", list(SCENARIOS.keys()))

if st.button("🚀 Test my connection"):
    scenario = random.choice(list(SCENARIOS.keys())) if random_mode else selected_scenario
    telemetry = randomise_scenario(SCENARIOS[scenario])
    st.session_state.telemetry = telemetry
    st.session_state.scenario_used = scenario
    st.session_state.result = run_agentic_test(telemetry, scenario)

if st.session_state.result:
    result = st.session_state.result
    action = result["action"]
    telemetry = st.session_state.telemetry

    cols = st.columns(5)
    cols[0].metric("Overall Status", rag_badge(result["overall_rag"]))
    cols[1].metric("Outcome", action.get("Outcome","N/A"))
    cols[2].metric("Confidence", result["chosen"].get("Confidence","N/A"))
    cols[3].metric("Risk", action.get("Risk","N/A"))
    cols[4].metric("Next Step Type", action.get("Agentic_level","N/A"))

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Telemetry",
        "Agentic Reasoning",
        "Marker Results",
        "Advisor View",
        "Customer View"
    ])

    with tab1:
        render_telemetry_tab(telemetry)

    # Insert your Agentic Reasoning, Marker Results, Advisor View, Customer View tab renderings here,
    # as in your existing app code.

else:
    st.info("Click 'Test my connection' to run the test.")



