import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# --- Synthetic Scenarios ---

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

# --- Helper Functions ---

def safe_value(value, suffix=""):
    return "Not available" if value is None else f"{value}{suffix}"

def rag_badge(rag):
    return {"Green":"🟢 Green","Amber":"🟠 Amber","Red":"🔴 Red","Grey":"⚪ Grey"}.get(rag, rag)

# Add your previous RAG calculation functions here...
# [Use the same from the previous full code]

# Function to build marker results with detailed explanations
def build_marker_results(t):
    results = []
    # Compute RAGs and explanations for each marker
    # For brevity, refer to previous code for full function
    # But ensure each marker returns Reason with clear, user-friendly explanation
    # Include specifics like actual measured values and thresholds
    # Example for RSSI:
    rssi_rag, rssi_reason = calculate_rssi_rag(t["rssi"])
    results.append({
        "Marker": "WiFi signal strength",
        "Value": safe_value(t["rssi"], " dBm"),
        "RAG": rssi_rag,
        "Reason": f"Measured RSSI is {safe_value(t['rssi'], ' dBm')}. Thresholds: Green ≥ -67 dBm, Amber -75 to -68 dBm, Red < -75 dBm."
                  f" Interpretation: {rssi_reason}"
    })
    # Repeat the above style for each metric...
    # Build full detailed reasons for Packet Loss, Retransmissions, etc.

    # Add the rest of your markers here similarly

    return results

# Functions to build hypotheses, decide actions, choose hypotheses — same as before

# --- Detailed customer message builder ---
def build_detailed_customer_message(t, marker_results, action):
    lines = []
    for m in marker_results:
        lines.append(f"{m['Marker']}: {m['Value']} — {m['Reason']}")
    lines.append("")
    lines.append(f"Diagnosis outcome: {action['Outcome']}")
    lines.append(f"Recommended action: {action['Action']}")
    lines.append(f"Advice: {action['Customer_message']}")
    return "\n".join(lines)

# --- Detailed advisor message builder ---
def build_detailed_advisor_message(t, marker_results, action, hypotheses):
    lines = ["**Markers and assessed telemetry:**"]
    for m in marker_results:
        lines.append(f"- {m['Marker']}: {m['Value']} — {m['Reason']} [RAG: {m['RAG']}]")
    lines.append("\n**Hypotheses formed:**")
    for h in hypotheses:
        lines.append(f"- {h['Hypothesis']} (Confidence: {h['Confidence']})")
        for ev in h['Evidence']:
            lines.append(f"  • {ev}")
    lines.append("")
    lines.append(f"Chosen hypothesis: {action['Outcome']}")
    lines.append(f"Recommended action: {action['Action']}")
    lines.append(f"Advisor notes: {action['Advisor_message']}")
    lines.append(f"Risk level: {action['Risk']}")
    return "\n".join(lines)

# --- Main agentic test function including historical trends ---
def run_agentic_test(t, scenario_key):
    marker_results = build_marker_results(t)
    overall_rag = rollup_rag(marker_results)
    hypotheses = build_hypotheses(t, marker_results)
    chosen = choose_best_hypothesis(hypotheses)
    action = decide_action(t, chosen, overall_rag)
    detailed_customer_message = build_detailed_customer_message(t, marker_results, action)
    detailed_advisor_message = build_detailed_advisor_message(t, marker_results, action, hypotheses)
    diagnostic_trace_text = f"Chosen hypothesis: {chosen['Hypothesis']} (Confidence: {chosen['Confidence']})\nAction taken: {action['Action']}"
    history = generate_synthetic_history(scenario_key)
    return {
        "marker_results": marker_results,
        "overall_rag": overall_rag,
        "hypotheses": hypotheses,
        "chosen": chosen,
        "action": action,
        "detailed_customer_message": detailed_customer_message,
        "detailed_advisor_message": detailed_advisor_message,
        "diagnostic_trace_text": diagnostic_trace_text,
        "history": history
    }

# --- Streamlit UI start ---
st.title("🛰️ Test SC — Agentic AI Diagnostic Demo")

random_mode = st.sidebar.checkbox("Random scenario every test", True)
selected_scenario = st.sidebar.selectbox("Or select a specific scenario", list(SCENARIOS.keys()))

if st.button("🚀 Run Connection Test"):
    scenario = random.choice(list(SCENARIOS.keys())) if random_mode else selected_scenario
    telemetry = randomise_scenario(SCENARIOS[scenario])
    st.session_state.telemetry = telemetry
    st.session_state.scenario_used = scenario
    st.session_state.result = run_agentic_test(telemetry, scenario)

if "result" in st.session_state and st.session_state.result:
    result = st.session_state.result
    telemetry = st.session_state.telemetry

    # Tabs for organized views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Telemetry", "Agentic Reasoning", "Marker Results", "Advisor View", "Customer View"])

    with tab1:
        st.header("Synthetic Telemetry Details")
        telemetry_data = [
            {"Field": "Product", "Value": telemetry["product"], "Description": "Service area"},
            {"Field": "Device Type", "Value": telemetry["device_type"], "Description": "Device involved"},
            {"Field": "Connection Method", "Value": telemetry["connection_method"], "Description": "Connection usage"},
            {"Field": "RSSI", "Value": safe_value(telemetry["rssi"], " dBm"), "Description": "WiFi signal strength"},
            {"Field": "Packet Loss", "Value": safe_value(telemetry["packet_loss"], "%"), "Description": "Percentage of packets lost"},
            {"Field": "Retransmission Rate", "Value": safe_value(telemetry["retransmission_rate"], "%"), "Description": "Percentage of retransmitted packets"},
            {"Field": "Rapid Reconnects", "Value": safe_value(telemetry["rapid_reconnects"]), "Description": "Number of quick reconnect events"},
            {"Field": "Telemetry Age", "Value": f"{telemetry['telemetry_age_minutes']} minutes", "Description": "Age of latest data"},
            {"Field": "Line Health", "Value": telemetry["line_health"], "Description": "Overall line status"},
            {"Field": "Known Outage", "Value": "Yes" if telemetry["known_outage"] else "No", "Description": "Active service outages"},
            {"Field": "Equipment Health", "Value": telemetry["equipment_health"], "Description": "Device equipment condition"},
            {"Field": "Customer Symptom", "Value": telemetry["customer_symptom"], "Description": "What customer reports"},
            {"Field": "Customer Impact Score", "Value": f"{telemetry['customer_impact_score']}/10", "Description": "Severity rating"},
        ]
        st.write(pd.DataFrame(telemetry_data).set_index("Field"))

    with tab2:
        st.header("Agentic AI Reasoning")
        st.subheader("Diagnostic Reasoning Summary")
        st.write(result["diagnostic_trace_text"])

        st.subheader("Synthetic Connection Metrics Trend")
        df_hist = pd.DataFrame(result["history"]).set_index("timestamp")
        st.line_chart(df_hist[["rssi", "packet_loss", "retransmission_rate", "rapid_reconnects"]].rename(columns={
            "rssi": "RSSI (dBm)",
            "packet_loss": "Packet Loss (%)",
            "retransmission_rate": "Retransmission Rate (%)",
            "rapid_reconnects": "Rapid Reconnects (#)"
        }))

    with tab3:
        st.header("Marker Results")
        marker_df = pd.DataFrame(result["marker_results"])
        marker_df["RAG Status"] = marker_df["RAG"].apply(rag_badge)
        st.dataframe(marker_df[["Marker", "Value", "RAG Status", "Reason"]])

    with tab4:
        st.header("Advisor View")
        st.markdown(result["detailed_advisor_message"].replace('\n', '  \n'))

    with tab5:
        st.header("Customer View")
        st.markdown(result["detailed_customer_message"].replace('\n', '  \n'))

else:
    st.info("Click the 'Run Connection Test' button to start.")

# --- Randomize telemetry function ---

def randomise_scenario(base):
    t = base.copy()
    if t["rssi"] is not None:
        t["rssi"] = max(-95, min(-30, t["rssi"] + random.randint(-6, 6)))
    if t["packet_loss"] is not None:
        t["packet_loss"] = round(max(0, min(20, t["packet_loss"] + random.uniform(-1.8, 1.8))), 1)
    if t["retransmission_rate"] is not None:
        t["retransmission_rate"] = max(0, min(50, t["retransmission_rate"] + random.randint(-5, 5)))
    if t["rapid_reconnects"] is not None:
        t["rapid_reconnects"] = max(0, min(20, t["rapid_reconnects"] + random.randint(-2, 2)))
    t["telemetry_age_minutes"] = max(1, min(600, t["telemetry_age_minutes"] + random.randint(-8, 8)))
    return t
