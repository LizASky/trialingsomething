import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# --- Synthetic scenarios (as before) ---
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

def safe_value(value, suffix=""):
    return "Not available" if value is None else f"{value}{suffix}"

def rag_badge(rag):
    return {"Green":"🟢 Green","Amber":"🟠 Amber","Red":"🔴 Red","Grey":"⚪ Grey"}.get(rag, rag)

# (All key helper functions, build_marker_results, diagnostics etc. as before...)

# Function to build simplified customer message focused on recommendations  
def build_simplified_customer_advice(action):
    advices = {
        "Weak WiFi signal": "Try moving your device closer to your hub or WiFi booster.",
        "WiFi interference detected": "Optimize your WiFi setup by reducing interference or changing channels.",
        "Unstable connection detected": "Please monitor your connection and retest. If issues continue, contact support.",
        "Engineer visit required": "An engineer visit is recommended to fix your connection issue.",
        "Replacement recommended": "We recommend arranging a replacement for your equipment.",
        "Known outage detected": "There is a known service issue. Please wait for updates.",
        "Test incomplete": "Please retry the test. If it fails again, contact customer support.",
        "No issue found": "Your connection looks healthy. No action needed at the moment."
    }
    return advices.get(action["Outcome"], action["Customer_message"])

# Updated Customer View tab content
def customer_view_tab_content(result):
    st.header("Customer Recommendations")
    advice = build_simplified_customer_advice(result["action"])
    st.success(advice)
    st.markdown(f"**Next step:** {result['action']['Action']}")

# Visual summary below test button
def show_summary(result):
    action = result["action"]
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Overall Status", rag_badge(result["overall_rag"]))
    col2.metric("Outcome", action["Outcome"])
    col3.metric("Confidence", result["chosen"]["Confidence"])
    col4.metric("Risk Level", action["Risk"])
    col5.metric("Next Step Type", action["Agentic_level"])

# (Include rest of your diagnostic logic, helpers, and run_agentic_test as before...)

# Initialize session state as needed
if "result" not in st.session_state:
    st.session_state.result = None
if "telemetry" not in st.session_state:
    st.session_state.telemetry = None
if "scenario_used" not in st.session_state:
    st.session_state.scenario_used = None

# Main UI
st.title("🛰️ Test SC Agentic AI Demo")

random_mode = st.sidebar.checkbox("Random scenario every test", True)
selected_scenario = st.sidebar.selectbox("Or pick scenario", list(SCENARIOS.keys()))

if st.button("🚀 Test my connection"):
    scenario = random.choice(list(SCENARIOS.keys())) if random_mode else selected_scenario
    telemetry = randomise_scenario(SCENARIOS[scenario])
    st.session_state.telemetry = telemetry
    st.session_state.scenario_used = scenario
    st.session_state.result = run_agentic_test(telemetry, scenario)

# Show summary immediately after running test
if st.session_state.result:
    show_summary(st.session_state.result)

# Then show detailed tabs
if st.session_state.result:
    result = st.session_state.result
    telemetry = st.session_state.telemetry

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Telemetry",
        "Agentic Reasoning",
        "Marker Results",
        "Advisor View",
        "Customer View"
    ])

    with tab1:
        st.header("Synthetic Telemetry")
        telemetry_info = [
            {"Field": "Product", "Value": telemetry["product"], "Description": "Service area"},
            {"Field": "Device Type", "Value": telemetry["device_type"], "Description": "Device involved"},
            {"Field": "Connection Method", "Value": telemetry["connection_method"], "Description": "Connection type"},
            {"Field": "RSSI", "Value": safe_value(telemetry["rssi"], " dBm"), "Description": "WiFi signal strength"},
            {"Field": "Packet Loss", "Value": safe_value(telemetry["packet_loss"], "%"), "Description": "Packet drop %"},
            {"Field": "Retransmission Rate", "Value": safe_value(telemetry["retransmission_rate"], "%"), "Description": "Packet retransmissions"},
            {"Field": "Rapid Reconnects", "Value": safe_value(telemetry["rapid_reconnects"]), "Description": "Reconnect events"},
            {"Field": "Telemetry Age", "Value": f"{telemetry['telemetry_age_minutes']} minutes", "Description": "Data age"},
            {"Field": "Line Health", "Value": telemetry["line_health"], "Description": "Line status"},
            {"Field": "Known Outage", "Value": "Yes" if telemetry["known_outage"] else "No", "Description": "Service outage"},
            {"Field": "Equipment Health", "Value": telemetry["equipment_health"], "Description": "Device condition"},
            {"Field": "Customer Symptom", "Value": telemetry["customer_symptom"], "Description": "Reported issue"},
            {"Field": "Customer Impact Score", "Value": f"{telemetry['customer_impact_score']}/10", "Description": "Severity rating"},
        ]
        st.table(pd.DataFrame(telemetry_info).set_index("Field"))

    with tab2:
        st.header("Agentic AI Reasoning & Trends")
        st.subheader("Reasoning Summary")
        st.text_area("Diagnostic Narrative", result["diagnostic_trace_text"], height=250, disabled=True)

        st.subheader("Connection Metrics Trend")
        df_hist = pd.DataFrame(result["history"]).set_index("timestamp")
        st.line_chart(df_hist[["rssi","packet_loss","retransmission_rate","rapid_reconnects"]])
        st.info(summarize_trends(df_hist))

    with tab3:
        st.header("Marker Results")
        marker_df = pd.DataFrame(result["marker_results"])
        marker_df["RAG Status"] = marker_df["RAG"].apply(rag_badge)
        st.table(marker_df[["Marker", "Value", "RAG Status", "Reason"]])

    with tab4:
        st.header("Advisor View")
        st.markdown(result["detailed_advisor_message"].replace("\n", "  \n"))

    with tab5:
        customer_view_tab_content(result)

else:
    st.info("Click the 'Test my connection' button to start.")

# --- Functions needed for updated UI ---

# Use your existing randomise_scenario, run_agentic_test, summarize_trends functions here
# For customer view tab content:

def customer_view_tab_content(result):
    st.header("Customer Recommendations")
    advice = build_simplified_customer_advice(result["action"])
    st.success(advice)
    st.markdown(f"**Next step:** {result['action']['Action']}")

def build_simplified_customer_advice(action):
    advices = {
        "Weak WiFi signal": "Try moving your device closer to your hub or WiFi booster.",
        "WiFi interference detected": "Optimize your WiFi setup to reduce interference or change channels.",
        "Unstable connection detected": "Monitor your connection and retest. Contact support if problems persist.",
        "Engineer visit required": "An engineer visit is recommended to fix your connection issue.",
        "Replacement recommended": "Arranging a replacement for your equipment is advised.",
        "Known outage detected": "There is a known service issue. Please wait for updates.",
        "Test incomplete": "Please rerun the test. If it fails again, contact support.",
        "No issue found": "Your connection looks healthy. No action needed currently."
    }
    return advices.get(action["Outcome"], action["Customer_message"])

