import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# --- Synthetic telemetry generator ---
def generate_fake_telemetry():
    products = ["Streaming TV", "Broadband", "Phone"]
    devices = ["Streaming device", "Laptop", "Mobile", "Hub"]
    connection_methods = ["5GHz WiFi", "2.4GHz WiFi", "Ethernet"]

    product = random.choice(products)
    device = random.choice(devices)
    connection = random.choice(connection_methods)

    telemetry = {
        "product": product,
        "device_type": device,
        "connection_method": connection,
        "rssi": random.randint(-90, -40) if connection != "Ethernet" else None,
        "packet_loss": round(random.uniform(0, 15), 1),
        "retransmission_rate": round(random.uniform(0, 30), 1),
        "rapid_reconnects": random.randint(0, 10),
        "telemetry_age_minutes": random.randint(1, 180),
        "line_health": random.choices(["OK", "Unstable", "Fail"], weights=[0.7, 0.2, 0.1])[0],
        "known_outage": random.choice([False, False, False, True]),  # rare outages
        "repeat_issue_7_days": random.choice([False, True]),
        "previous_outcome": random.choice(["No previous journey", "Self-serve guidance shown", "Issue repeated"]),
        "hub_model": random.choice(["Hub 4", "Hub 5", "Hub 6"]),
        "pod_present": random.choice([False, True]),
        "customer_symptom": random.choice(["No issue reported", "Buffering or poor picture quality", "Slow broadband speed", "Connection drops"]),
        "customer_impact_score": random.randint(1, 10),
        "equipment_health": random.choices(["OK", "Suspected fault"], weights=[0.85, 0.15])[0]
    }
    return telemetry

# --- All your previously defined helper functions (safe_value, rag_badge, calculate_rssi_rag, etc.) ---
# Please add all these functions here, exactly as you have them,
# including build_marker_results, rollup_rag, build_hypotheses, choose_best_hypothesis, decide_action,
# build_detailed_customer_message, build_detailed_advisor_message, generate_synthetic_history, summarize_trends, etc.

# For example:
def safe_value(value, suffix=""):
    return "Not available" if value is None else f"{value}{suffix}"

def rag_badge(rag):
    return {"Green":"🟢 Green","Amber":"🟠 Amber","Red":"🔴 Red","Grey":"⚪ Grey"}.get(rag, rag)

# ... (include all other helpers exactly)

# --- Your full diagnostic logic functions ---

# --- Main agentic test logic ---
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

# --- Streamlit Session State Initialization ---
for key in ['result', 'telemetry', 'scenario_used']:
    if key not in st.session_state:
        st.session_state[key] = None

# --- Streamlit UI ---
st.title("🛰️ Agentic AI Synthetic Connection Test")

random_mode = st.sidebar.checkbox("Random synthetic scenario", True)
selected_scenario = st.sidebar.selectbox("Or choose a specific synthetic scenario", list(SCENARIOS.keys()))

if st.button("🚀 Test my connection"):
    telemetry = generate_fake_telemetry()
    st.session_state.telemetry = telemetry
    st.session_state.scenario_used = "Synthetic scenario"
    st.session_state.result = run_agentic_test(telemetry, "Synthetic scenario")

if st.session_state.result:
    result = st.session_state.result
    action = result["action"]
    telemetry = st.session_state.telemetry

    cols = st.columns(5)
    cols[0].metric("Overall Status", rag_badge(result["overall_rag"]))
    cols[1].metric("Outcome", action.get("Outcome", "N/A"))
    cols[2].metric("Confidence", result["chosen"].get("Confidence", "N/A"))
    cols[3].metric("Risk Level", action.get("Risk", "N/A"))
    cols[4].metric("Next Step Type", action.get("Agentic_level", "N/A"))

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Telemetry", "Agentic Reasoning", "Marker Results", "Advisor View", "Customer View"])

    with tab1:
        st.header("Synthetic Telemetry Details")
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
            {"Field": "Equipment Health", "Value": telemetry["equipment_health"], "Meaning": "Device condition"},
            {"Field": "Customer Symptom", "Value": telemetry["customer_symptom"], "Meaning": "Customer reported symptoms"},
            {"Field": "Customer Impact Score", "Value": f"{telemetry['customer_impact_score']}/10", "Meaning": "Severity rating for impact"},
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
        marker_df = pd.DataFrame(result["marker_results"])
        marker_df["RAG Status"] = marker_df["RAG"].apply(rag_badge)
        st.table(marker_df[["Marker", "Value", "RAG Status", "Reason"]])

    with tab4:
        st.header("Advisor View")
        advisor_summary = {
            "Field": ["Outcome", "Recommended Action", "Chosen Hypothesis", "Confidence Level", "Risk Level"],
            "Value": [
                action.get("Outcome", "N/A"),
                action.get("Action", "N/A"),
                result["chosen"].get("Hypothesis", "N/A"),
                result["chosen"].get("Confidence", "N/A"),
                action.get("Risk", "N/A"),
            ]
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


