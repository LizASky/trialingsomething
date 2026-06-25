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

# --- Helper functions ---

def safe_value(value, suffix=""):
    return "Not available" if value is None else f"{value}{suffix}"

def rag_badge(rag):
    return {
        "Green": "🟢 Green",
        "Amber": "🟠 Amber",
        "Red": "🔴 Red",
        "Grey": "⚪ Grey"
    }.get(rag, rag)

def randomise_scenario(base):
    t = base.copy()
    if t["rssi"] is not None:
        t["rssi"] = max(-95, min(-30, t["rssi"] + random.randint(-6,6)))
    if t["packet_loss"] is not None:
        t["packet_loss"] = round(max(0, min(20, t["packet_loss"] + random.uniform(-1.8,1.8))), 1)
    if t["retransmission_rate"] is not None:
        t["retransmission_rate"] = max(0, min(50, t["retransmission_rate"] + random.randint(-5,5)))
    if t["rapid_reconnects"] is not None:
        t["rapid_reconnects"] = max(0, min(20, t["rapid_reconnects"] + random.randint(-2,2)))
    t["telemetry_age_minutes"] = max(1, min(600, t["telemetry_age_minutes"] + random.randint(-8,8)))
    return t

def calculate_rssi_rag(rssi):
    if rssi is None:
        return "Grey", "WiFi signal telemetry unavailable"
    if rssi >= -67:
        return "Green", "WiFi signal is healthy"
    elif rssi >= -75:
        return "Amber", "WiFi signal is degraded"
    else:
        return "Red", "WiFi signal is poor"

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
        return "Green", "Reconnect behaviour is stable"
    elif rapid_reconnects <= 4:
        return "Amber", "Some reconnect instability"
    else:
        return "Red", "Frequent reconnect instability"

def calculate_line_health_rag(line_health):
    if line_health == "OK":
        return "Green", "Line health looks OK"
    if line_health == "Unstable":
        return "Amber", "Line health unstable"
    if line_health == "Fail":
        return "Red", "Line health failed"
    return "Grey", "Line health unknown"

def calculate_telemetry_age_rag(age):
    if age is None:
        return "Grey", "Telemetry age unknown"
    if age <= 30:
        return "Green", "Telemetry is fresh"
    elif age <=120:
        return "Amber", "Telemetry is slightly old"
    else:
        return "Grey", "Telemetry too old"

def calculate_equipment_health_rag(health):
    if health == "OK":
        return "Green", "No equipment faults suspected"
    if health == "Suspected fault":
        return "Red", "Suspected equipment fault"
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
    equip_rag, equip_reason = calculate_equipment_health_rag(t["equipment_health"])
    results.append({"Marker": "Equipment health", "Value": t["equipment_health"], "RAG": equip_rag, "Reason": equip_reason})
    return results

def rollup_rag(marker_results):
    rags = [m["RAG"] for m in marker_results]
    if "Red" in rags:
        return "Red"
    if "Amber" in rags:
        return "Amber"
    if "Grey" in rags:
        return "Grey"
    return "Green"

def build_hypotheses(t, markers):
    lookup = {m["Marker"]: m for m in markers}
    hyps = []
    if t["known_outage"]:
        hyps.append({"Hypothesis": "Known service outage", "Evidence": ["Known outage active"], "Confidence": "High"})
        return hyps
    if lookup["Telemetry freshness"]["RAG"] == "Grey":
        hyps.append({"Hypothesis": "Telemetry missing or stale", "Evidence": ["Telemetry too old/unavailable"], "Confidence": "High"})
    if lookup["Equipment health"]["RAG"] == "Red":
        hyps.append({"Hypothesis": "Equipment replacement needed", "Evidence": ["Suspected equipment fault", "Issue repeated"], "Confidence": "High"})
    if lookup["Line health"]["RAG"] == "Red":
        hyps.append({"Hypothesis": "Engineer visit needed", "Evidence": ["Line health failed", "Symptoms severe"], "Confidence": "High"})
    if lookup["WiFi signal strength"]["RAG"] in ["Amber", "Red"]:
        hyps.append({"Hypothesis": "Poor WiFi signal or placement", "Evidence": ["WiFi signal degraded"], "Confidence": "Medium"})
    if lookup["Packet loss"]["RAG"] == "Red" and lookup["Retransmission rate"]["RAG"] in ["Amber", "Red"]:
        hyps.append({"Hypothesis": "WiFi interference or congestion", "Evidence": ["Elevated packet loss and retransmissions"], "Confidence": "Medium"})
    if lookup["Rapid reconnects"]["RAG"] in ["Amber", "Red"]:
        hyps.append({"Hypothesis": "Intermittent connectivity instability", "Evidence": ["Frequent rapid reconnects"], "Confidence": "Medium"})
    if not hyps:
        hyps.append({"Hypothesis": "Connection healthy", "Evidence": ["No red flags detected"], "Confidence": "High"})
    return hyps

def choose_best_hypothesis(hypotheses):
    ranking = {"High": 3, "Medium": 2, "Low": 1}
    return sorted(hypotheses, key=lambda h: ranking.get(h["Confidence"], 0), reverse=True)[0]

def decide_action(t, chosen, overall_rag):
    h = chosen["Hypothesis"]
    if t["known_outage"]:
        return {
            "Outcome": "Known outage detected",
            "Action": "No action needed; issue is being resolved.",
            "Customer_message": "Service outage ongoing; please wait.",
            "Advisor_message": "Known outage active.",
            "Agentic_level": "Suppress troubleshooting",
            "Risk": "Low"
        }
    if "Telemetry missing or stale" in h:
        return {
            "Outcome": "Test incomplete",
            "Action": "Retry the test; escalate if persists.",
            "Customer_message": "Test incomplete due to missing telemetry.",
            "Advisor_message": "Telemetry stale or missing.",
            "Agentic_level": "Retry",
            "Risk": "Low"
        }
    if "Equipment replacement needed" in h:
        return {
            "Outcome": "Replacement recommended",
            "Action": "Offer equipment replacement.",
            "Customer_message": "Equipment likely faulty; replacement recommended.",
            "Advisor_message": "Suspected equipment fault.",
            "Agentic_level": "Recommend replacement",
            "Risk": "Medium"
        }
    if "Engineer visit needed" in h:
        return {
            "Outcome": "Engineer visit required",
            "Action": "Schedule engineer visit.",
            "Customer_message": "Issue requires engineer intervention.",
            "Advisor_message": "Line failure detected.",
            "Agentic_level": "Escalate",
            "Risk": "Medium"
        }
    if "Poor WiFi signal or placement" in h:
        return {
            "Outcome": "Weak WiFi signal",
            "Action": "Move device closer to router or add boosters.",
            "Customer_message": "Weak WiFi signal detected; improve placement.",
            "Advisor_message": "Weak WiFi detected, recommend in-home fixes.",
            "Agentic_level": "Recommend fix",
            "Risk": "Low"
        }
    if "WiFi interference or congestion" in h:
        return {
            "Outcome": "WiFi interference detected",
            "Action": "Optimize WiFi setup and retest.",
            "Customer_message": "WiFi interference or congestion detected.",
            "Advisor_message": "High packet loss and retransmission rate.",
            "Agentic_level": "Recommend optimization",
            "Risk": "Low"
        }
    if "Intermittent connectivity instability" in h:
        return {
            "Outcome": "Unstable connection detected",
            "Action": "Monitor and retest; escalate if persists.",
            "Customer_message": "Connection unstable; monitor and retest.",
            "Advisor_message": "Instability detected.",
            "Agentic_level": "Monitor",
            "Risk": "Medium"
        }
    return {
        "Outcome": "No issue found",
        "Action": "No action needed at this time.",
        "Customer_message": "Connection appears healthy.",
        "Advisor_message": "No fault detected.",
        "Agentic_level": "Explain",
        "Risk": "Low"
    }

def generate_synthetic_history(scenario_key):
    base = SCENARIOS[scenario_key]
    now = datetime.now()
    history = []
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
            "rapid_reconnects": max(0,int(base["rapid_reconnects"] + random.randint(-1,1)))
        })
    return history

def plot_trends(history):
    df = pd.DataFrame(history).set_index("timestamp")
    st.line_chart(df[["rssi", "packet_loss", "retransmission_rate", "rapid_reconnects"]])
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
    cols[1].metric("Outcome", action.get("Outcome", "N/A"))
    cols[2].metric("Confidence", result["chosen"].get("Confidence", "N/A"))
    cols[3].metric("Risk", action.get("Risk", "N/A"))
    cols[4].metric("Next Step Type", action.get("Agentic_level", "N/A"))

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
            {"Field": "Product", "Value": telemetry["product"], "Meaning": "Type of service being tested"},
            {"Field": "Device Type", "Value": telemetry["device_type"], "Meaning": "Device you are using"},
            {"Field": "Connection Method", "Value": telemetry["connection_method"], "Meaning": "How your device connects"},
            {"Field": "RSSI", "Value": safe_value(telemetry["rssi"], " dBm"), "Meaning": "WiFi signal strength (connection quality)"},
            {"Field": "Packet Loss", "Value": safe_value(telemetry["packet_loss"], "%"), "Meaning": "Percentage of data packets lost"},
            {"Field": "Retransmission Rate", "Value": safe_value(telemetry["retransmission_rate"], "%"), "Meaning": "How often data is resent due to errors"},
            {"Field": "Rapid Reconnects", "Value": safe_value(telemetry["rapid_reconnects"]), "Meaning": "Number of quick disconnects and reconnects"},
            {"Field": "Telemetry Age", "Value": f"{telemetry['telemetry_age_minutes']} minutes", "Meaning": "Recency of data"},
            {"Field": "Line Health", "Value": telemetry["line_health"], "Meaning": "Overall quality of your broadband line"},
            {"Field": "Known Outage", "Value": "Yes" if telemetry["known_outage"] else "No", "Meaning": "Known service issue affecting your connection"},
            {"Field": "Equipment Health", "Value": telemetry["equipment_health"], "Meaning": "Device hardware condition"},
            {"Field": "Customer Symptom", "Value": telemetry["customer_symptom"], "Meaning": "Issue you reported"},
            {"Field": "Customer Impact Score", "Value": f"{telemetry['customer_impact_score']}/10", "Meaning": "Severity of your connection problem"},
        ]
        st.table(pd.DataFrame(telemetry_info).set_index("Field"))

    with tab2:
        st.header("Agentic AI Reasoning")
        st.text_area("Diagnostic Narrative", result["diagnostic_trace_text"], height=250, disabled=True)
        df_hist = pd.DataFrame(result["history"]).set_index("timestamp")
        st.line_chart(df_hist[["rssi","packet_loss","retransmission_rate","rapid_reconnects"]])
        st.info(summarize_trends(df_hist))

    with tab3:
        st.header("Marker Results")
        marker_df = pd.DataFrame(result["marker_results"])
        marker_df["RAG Status"] = marker_df["RAG"].apply(rag_badge)
        st.table(marker_df[["Marker", "Value", "RAG Status", "Reason"]])

    with tab4:
        st.header("Advisor View — Summary")
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
        st.header("Customer View — Recommendations")
        advice_map = {
            "Weak WiFi signal": "Move your device closer to your router or WiFi booster to improve signal strength.",
            "WiFi interference detected": "Try optimizing your WiFi setup by changing channels or reducing interference.",
            "Unstable connection detected": "Monitor your connection and rerun the test. Contact support if persists.",
            "Engineer visit required": "An engineer visit is recommended to resolve your issue.",
            "Replacement recommended": "We suggest arranging equipment replacement.",
            "Known outage detected": "A known service outage is affecting your connection; please wait for resolution.",
            "Test incomplete": "The test didn’t complete successfully; please retry or contact support.",
            "No issue found": "Your connection looks healthy. No further action is needed."
        }
        advice = advice_map.get(action["Outcome"], action.get("Customer_message", ""))
        st.success(advice)
        st.markdown(f"**Next step:** {action.get('Action', 'No further action needed')}")

else:
    st.info("Click 'Test my connection' to start the diagnostic.")


