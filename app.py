import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# --- Generate synthetic telemetry randomly ---

def generate_synthetic_telemetry():
    """Produce fully synthetic telemetry for demo purposes."""
    products = ["Streaming TV", "Broadband", "Phone"]
    devices = ["Streaming device", "Laptop", "Smartphone", "Hub"]
    connection_types = ["5GHz WiFi", "2.4GHz WiFi", "Ethernet"]

    product = random.choice(products)
    device = random.choice(devices)
    connection = random.choice(connection_types)

    telemetry = {
        "product": product,
        "device_type": device,
        "connection_method": connection,
        "rssi": random.randint(-90, -40) if connection != "Ethernet" else None,
        "packet_loss": round(random.uniform(0, 15), 1),
        "retransmission_rate": round(random.uniform(0, 30),1),
        "rapid_reconnects": random.randint(0, 10),
        "telemetry_age_minutes": random.randint(1, 180),
        "line_health": random.choices(["OK", "Unstable", "Fail"], [0.7, 0.2, 0.1])[0],
        "known_outage": random.choices([False, True], [0.9, 0.1])[0],
        "repeat_issue_7_days": random.choice([False, True]),
        "previous_outcome": random.choice(["No previous journey", "Self-serve guidance shown", "Issue repeated"]),
        "hub_model": random.choice(["Hub 4", "Hub 5", "Hub 6"]),
        "pod_present": random.choice([True, False]),
        "customer_symptom": random.choice(["No issue reported", "Buffering", "Slow speed", "Connection drops"]),
        "customer_impact_score": random.randint(1, 10),
        "equipment_health": random.choices(["OK", "Suspected fault"], [0.85, 0.15])[0]
    }
    return telemetry

# --- Diagnostic helper functions (RAG calcs, marker building, hypotheses, etc.) ---

# (Include your existing helper functions here, adjusted if needed for synthetic)
# For brevity, you can reuse previously provided functions such as:
# safe_value(), rag_badge(), calculate_rssi_rag(), build_marker_results(),
# build_hypotheses(), choose_best_hypothesis(), decide_action(), run_agentic_test(), etc.

# --- Streamlit UI ---

if "result" not in st.session_state:
    st.session_state.result = None
if "telemetry" not in st.session_state:
    st.session_state.telemetry = None

st.title("🛰️ Synthetic Agentic AI Connection Test Demo")

if st.button("🚀 Test my connection"):
    telemetry = generate_synthetic_telemetry()
    st.session_state.telemetry = telemetry
    st.session_state.result = run_agentic_test(telemetry, "Synthetic Scenario")

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

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Telemetry", "Agentic Reasoning", "Marker Results", "Advisor View", "Customer View"
    ])

    with tab1:
        st.header("Synthetic Telemetry")
        telemetry_info = [
            {"Field": "Product", "Value": telemetry["product"], "Meaning": "Type of service being tested"},
            {"Field": "Device Type", "Value": telemetry["device_type"], "Meaning": "Device type used"},
            {"Field": "Connection Method", "Value": telemetry["connection_method"], "Meaning": "Connection type"},
            {"Field": "RSSI", "Value": safe_value(telemetry["rssi"], " dBm"), "Meaning": "WiFi signal strength"},
            {"Field": "Packet Loss", "Value": safe_value(telemetry["packet_loss"], "%"), "Meaning": "Loss of packets in transmission"},
            {"Field": "Retransmission Rate", "Value": safe_value(telemetry["retransmission_rate"], "%"), "Meaning": "Frequency of re-sent packets"},
            {"Field": "Rapid Reconnects", "Value": safe_value(telemetry["rapid_reconnects"]), "Meaning": "Fast reconnect instances"},
            {"Field": "Telemetry Age", "Value": f"{telemetry['telemetry_age_minutes']} minutes", "Meaning": "Age of the telemetry data"},
            {"Field": "Line Health", "Value": telemetry["line_health"], "Meaning": "Broadband line status"},
            {"Field": "Known Outage", "Value": "Yes" if telemetry["known_outage"] else "No", "Meaning": "Known widespread outages"},
            {"Field": "Equipment Health", "Value": telemetry["equipment_health"], "Meaning": "Status of equipment"},
            {"Field": "Customer Symptom", "Value": telemetry["customer_symptom"], "Meaning": "Reported issue"},
            {"Field": "Customer Impact Score", "Value": f"{telemetry['customer_impact_score']}/10", "Meaning": "Severity score"}
        ]
        st.table(pd.DataFrame(telemetry_info).set_index("Field"))

    with tab2:
        st.header("Agentic AI Reasoning")
        st.text_area("Diagnostic Narrative", result["diagnostic_trace_text"], height=250, disabled=True)
        df_hist = pd.DataFrame(result.get("history", [])).set_index("timestamp")
        if not df_hist.empty:
            st.line_chart(df_hist[["rssi", "packet_loss", "retransmission_rate", "rapid_reconnects"]])
            st.info(summarize_trends(df_hist))
        else:
            st.info("No telemetry history available yet.")

    with tab3:
        st.header("Marker Results")
        marker_df = pd.DataFrame(result["marker_results"])
        marker_df["RAG Status"] = marker_df["RAG"].apply(rag_badge)
        st.table(marker_df[["Marker", "Value", "RAG Status", "Reason"]])

    with tab4:
        st.header("Advisor View")
        advisor_summary = {
            "Field": ["Outcome", "Recommended Action", "Chosen Hypothesis", "Confidence", "Risk Level"],
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
            st.markdown(f"**{hyp['Hypothesis']}** (Confidence: {hyp['Confidence']})")
            st.write(", ".join(hyp["Evidence"]))
            st.markdown("---")

    with tab5:
        st.header("Customer View")
        advice_map = {
            "Weak WiFi signal": "Try moving closer to your router or WiFi booster.",
            "WiFi interference detected": "Optimize your WiFi setup to reduce interference.",
            "Unstable connection detected": "Monitor your connection and retest. Contact support if needed.",
            "Engineer visit required": "An engineer visit is recommended.",
            "Replacement recommended": "Please arrange equipment replacement.",
            "Known outage detected": "Known outage; please wait for fix.",
            "Test incomplete": "Test incomplete, please retry or contact support.",
            "No issue found": "Connection appears healthy; no action needed."
        }
        st.success(advice_map.get(action.get("Outcome",""), action.get("Customer_message","")))
        st.markdown(f"**Next step:** {action.get('Action', 'No further action needed')}")

else:
    st.info("Press **Test my connection** to begin synthetic diagnostics.")
