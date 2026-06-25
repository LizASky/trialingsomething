import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# --- Synthetic Telemetry Scenarios ---
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

# --- Helper Functions ---
def safe_value(value, suffix=""):
    return "Not available" if value is None else f"{value}{suffix}"

def rag_badge(rag):
    return {"Green": "🟢 Green", "Amber": "🟠 Amber", "Red": "🔴 Red", "Grey": "⚪ Grey"}.get(rag, rag)

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

# Add all your diagnostic helpers: calculate_*_rag, build_marker_results, rollup_rag,
# build_hypotheses, choose_best_hypothesis, decide_action, generate_synthetic_history,
# summarize_trends, build_detailed_customer_message, build_detailed_advisor_message, run_agentic_test

# --- Streamlit UI ---
if 'result' not in st.session_state:
    st.session_state.result = None
if 'telemetry' not in st.session_state:
    st.session_state.telemetry = None
if 'scenario_used' not in st.session_state:
    st.session_state.scenario_used = None

st.title("🛰️ Test SC Agentic AI Demo")

random_mode = st.sidebar.checkbox("Random scenario every test", True)
selected_scenario = st.sidebar.selectbox("Or select specific scenario", list(SCENARIOS.keys()))

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
    cols[1].metric("Outcome", action.get("Outcome", "N/A"))
    cols[2].metric("Confidence", result["chosen"].get("Confidence", "N/A"))
    cols[3].metric("Risk", action.get("Risk", "N/A"))
    cols[4].metric("Next Step Type", action.get("Agentic_level", "N/A"))

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Telemetry", "Agentic Reasoning", "Marker Results", "Advisor View", "Customer View"])

    with tab1:
        st.header("Synthetic Telemetry")
        telemetry_info = [
            {"Field": "Product", "Value": telemetry["product"], "Meaning": "Type of service being tested"},
            {"Field": "Device Type", "Value": telemetry["device_type"], "Meaning": "Device you are using"},
            {"Field": "Connection Method", "Value": telemetry["connection_method"], "Meaning": "How your device connects"},
            {"Field": "RSSI", "Value": safe_value(telemetry["rssi"], " dBm"), "Meaning": "WiFi signal strength (connection quality)"},
            {"Field": "Packet Loss", "Value": safe_value(telemetry["packet_loss"], "%"), "Meaning": "Percentage of lost data packets"},
            {"Field": "Retransmission Rate", "Value": safe_value(telemetry["retransmission_rate"], "%"), "Meaning": "Frequency of retransmissions"},
            {"Field": "Rapid Reconnects", "Value": safe_value(telemetry["rapid_reconnects"]), "Meaning": "Number of rapid reconnect events"},
            {"Field": "Telemetry Age", "Value": f"{telemetry['telemetry_age_minutes']} minutes", "Meaning": "Recency of telemetry data"},
            {"Field": "Line Health", "Value": telemetry["line_health"], "Meaning": "Broadband line health"},
            {"Field": "Known Outage", "Value": "Yes" if telemetry["known_outage"] else "No", "Meaning": "Known service outages"},
            {"Field": "Equipment Health", "Value": telemetry["equipment_health"], "Meaning": "Equipment condition"},
            {"Field": "Customer Symptom", "Value": telemetry["customer_symptom"], "Meaning": "Customer reported symptom"},
            {"Field": "Customer Impact Score", "Value": f"{telemetry['customer_impact_score']}/10", "Meaning": "Severity of your connection problem"}
        ]
        st.table(pd.DataFrame(telemetry_info).set_index("Field"))

    with tab2:
        st.header("Agentic AI Reasoning")
        st.text_area("Diagnostic Narrative", result["diagnostic_trace_text"], height=250, disabled=True)
        df_hist = pd.DataFrame(result["history"]).set_index("timestamp")
        st.line_chart(df_hist[["rssi", "packet_loss", "retransmission_rate", "rapid_reconnects"]])
        st.info(summarize_trends(df_hist))

    with tab3:
        st.header("Marker Results")
        df_markers = pd.DataFrame(result["marker_results"])
        df_markers["RAG Status"] = df_markers["RAG"].apply(rag_badge)
        st.table(df_markers[["Marker", "Value", "RAG Status", "Reason"]])

    with tab4:
        st.header("Advisor View")
        advisor_summary = {
            "Field": ["Outcome", "Recommended Action", "Chosen Hypothesis", "Confidence Level", "Risk Level"],
            "Value": [action.get("Outcome"), action.get("Action"), result["chosen"].get("Hypothesis"), result["chosen"].get("Confidence"), action.get("Risk")]
        }
        st.table(pd.DataFrame(advisor_summary))
        st.subheader("Hypotheses & Evidence")
        for hyp in result["hypotheses"]:
            st.markdown(f"**{hyp['Hypothesis']}** — Confidence: {hyp['Confidence']}")
            st.write(", ".join(hyp["Evidence"]))
            st.markdown("---")

    with tab5:
        st.header("Customer View")
        advice_map = {
            "Weak WiFi signal": "Try moving your device closer to your router or WiFi booster.",
            "WiFi interference detected": "Optimize your WiFi setup by reducing interference or changing channels.",
            "Unstable connection detected": "Monitor your connection and retest. Contact support if problems persist.",
            "Engineer visit required": "An engineer visit is recommended to resolve your issue.",
            "Replacement recommended": "We recommend you arrange a replacement for faulty equipment.",
            "Known outage detected": "There is a known service outage. Please wait for resolution updates.",
            "Test incomplete": "The test could not complete. Please try again or contact support.",
            "No issue found": "Your connection is healthy. No further action needed."
        }
        advice = advice_map.get(action.get("Outcome", ""), action.get("Customer_message", ""))
        st.success(advice)
        st.markdown(f"**Next step:** {action.get('Action', 'No further action needed')}")
else:
    st.info("Click 'Test my connection' to start.")
