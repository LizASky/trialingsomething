import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# ===============================
# Synthetic Scenarios (demo-only data)
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
    }
}

# ===============================
# Helper functions and RAG calculations
# ===============================
def safe_value(value, suffix=""):
    return "Not available" if value is None else f"{value}{suffix}"

def rag_badge(rag):
    return {"Green":"🟢 Green","Amber":"🟠 Amber","Red":"🔴 Red","Grey":"⚪ Grey"}.get(rag, rag)

def calculate_rssi_rag(rssi):
    if rssi is None:
        return "Grey", "WiFi signal telemetry unavailable"
    if rssi >= -67:
        return "Green", "WiFi signal strength looks healthy"
    elif rssi >= -75:
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

def build_hypotheses(t, marker_results):
    lookup = {m["Marker"]: m for m in marker_results}
    hypotheses = []
    if t["known_outage"]:
        hypotheses.append({
            "Hypothesis": "Known wider service issue",
            "Evidence": ["Known outage active", "Stop troubleshooting", "No engineer/replacement needed"],
            "Confidence": "High"
        })
        return hypotheses
    if lookup["Telemetry freshness"]["RAG"] == "Grey":
        hypotheses.append({
            "Hypothesis": "Telemetry missing or stale",
            "Evidence": ["Telemetry too old/unavailable", "Markers Grey"],
            "Confidence": "High"
        })
    if lookup["Equipment health"]["RAG"] == "Red":
        hypotheses.append({
            "Hypothesis": "Equipment replacement needed",
            "Evidence": ["Suspected equipment fault", "Issue repeated"],
            "Confidence": "High"
        })
    if lookup["Line health"]["RAG"] == "Red":
        hypotheses.append({
            "Hypothesis": "Engineer visit needed",
            "Evidence": ["Line health failed", "Symptoms severe"],
            "Confidence": "High"
        })
    if lookup["WiFi signal strength"]["RAG"] in ["Amber", "Red"]:
        hypotheses.append({
            "Hypothesis": "Poor WiFi signal or placement",
            "Evidence": [f"WiFi signal flagged {lookup['WiFi signal strength']['RAG']}", f"Connection method {t['connection_method']}"],
            "Confidence": "Medium"
        })
    if lookup["Packet loss"]["RAG"] == "Red" and lookup["Retransmission rate"]["RAG"] in ["Amber", "Red"]:
        hypotheses.append({
            "Hypothesis": "WiFi interference or congestion",
            "Evidence": ["Packet loss Red", f"Retransmission rate {lookup['Retransmission rate']['RAG']}"],
            "Confidence": "Medium"
        })
    if lookup["Rapid reconnects"]["RAG"] in ["Amber", "Red"]:
        hypotheses.append({
            "Hypothesis": "Intermittent connectivity instability",
            "Evidence": [f"Rapid reconnects {lookup['Rapid reconnects']['RAG']}"],
            "Confidence": "Medium"
        })
    if not hypotheses:
        hypotheses.append({
            "Hypothesis": "Connection healthy",
            "Evidence": ["No Red markers", "Telemetry fresh", "Line health OK"],
            "Confidence": "High"
        })
    return hypotheses

def choose_best_hypothesis(hypotheses):
    rank = {"High":3,"Medium":2,"Low":1}
    return sorted(hypotheses, key=lambda x: rank.get(x["Confidence"],0), reverse=True)[0]

def decide_action(t, chosen, overall_rag):
    h = chosen["Hypothesis"]
    if t["known_outage"]:
        return {"Outcome":"Known outage detected", "Action":"No action needed.", "Customer_message":"Known issue affecting service; no action required.", "Advisor_message":"Known outage path; do not escalate.", "Agentic_level":"Suppress troubleshooting", "Risk":"Low"}
    if "Telemetry missing or stale" in h:
        return {"Outcome":"Test incomplete", "Action":"Retry test; escalate if persists.", "Customer_message":"Missing or stale telemetry data.", "Advisor_message":"No firm diagnosis due to telemetry.", "Agentic_level":"Retry", "Risk":"Low"}
    if "Equipment replacement needed" in h:
        return {"Outcome":"Replacement recommended", "Action":"Offer replacement equipment.", "Customer_message":"Device suspected faulty; replacement advised.", "Advisor_message":"Equipment fault suspected.", "Agentic_level":"Recommend replacement", "Risk":"Medium"}
    if "Engineer visit needed" in h:
        return {"Outcome":"Engineer visit required", "Action":"Schedule engineer visit.", "Customer_message":"Issue requires engineer intervention.", "Advisor_message":"Escalate to engineer.", "Agentic_level":"Escalate", "Risk":"Medium"}
    if "Poor WiFi signal" in h:
        if t["pod_present"]:
            next_step = "Move closer to hub or pod, then retest."
            advisor_note = "Pod present; suggest placement adjustments."
        else:
            next_step = "Move closer to hub or add WiFi booster, then retest."
            advisor_note = "No pod; recommend improving WiFi coverage."
        return {"Outcome":"Weak WiFi signal", "Action":next_step, "Customer_message":f"Weak WiFi detected. {next_step}", "Advisor_message":advisor_note, "Agentic_level":"Recommend fix", "Risk":"Low"}
    if "WiFi interference or congestion" in h:
        return {"Outcome":"WiFi interference detected", "Action":"Optimize WiFi setup & retest.", "Customer_message":"WiFi interference or congestion detected.", "Advisor_message":"Recommend WiFi optimization.", "Agentic_level":"Recommend optimization", "Risk":"Low"}
    if "Intermittent connectivity instability" in h:
        return {"Outcome":"Unstable connection detected", "Action":"Monitor and retest; escalate if persists.", "Customer_message":"Connection unstable; monitor and retest.", "Advisor_message":"Escalate based on repeat issues.", "Agentic_level":"Monitor", "Risk":"Medium"}
    return {"Outcome":"No issue found", "Action":"No action needed. Monitor and test again if necessary.", "Customer_message":"Connection looks healthy.", "Advisor_message":"No fault detected.", "Agentic_level":"Explain", "Risk":"Low"}

# Telemetry randomizer for demo
def randomise_scenario(base):
    t = base.copy()
    if t["rssi"] is not None:
        t["rssi"] = max(-95, min(-30, t["rssi"] + random.randint(-6,6)))
    if t["packet_loss"] is not None:
        t["packet_loss"] = round(max(0,min(20,t["packet_loss"] + random.uniform(-1.8,1.8))),1)
    if t["retransmission_rate"] is not None:
        t["retransmission_rate"] = max(0,min(50,t["retransmission_rate"] + random.randint(-5,5)))
    if t["rapid_reconnects"] is not None:
        t["rapid_reconnects"] = max(0,min(20,t["rapid_reconnects"] + random.randint(-2,2)))
    t["telemetry_age_minutes"] = max(1,min(600,t["telemetry_age_minutes"] + random.randint(-8,8)))
    return t

# Generate synthetic trend history (timestamp + values)
def generate_synthetic_history(scenario_key):
    base = SCENARIOS[scenario_key]
    history = []
    now = datetime.now()
    for i in range(10):
        timestamp = now - timedelta(hours=10 - i)
        def jitter(v, low, high, scale=3):
            if v is None:
                return None
            val = v + random.uniform(-scale, scale)
            return max(low, min(high, val))
        history.append({
            "timestamp": timestamp,
            "rssi": jitter(base["rssi"], -95, -30),
            "packet_loss": jitter(base["packet_loss"], 0, 20),
            "retransmission_rate": jitter(base["retransmission_rate"], 0, 50),
            "rapid_reconnects": max(0,int(base["rapid_reconnects"] + random.randint(-1,1)))
        })
    return history

# Plot trends using native Streamlit line_chart
def plot_trends(history):
    df = pd.DataFrame(history).set_index("timestamp")
    df_plot = df[["rssi","packet_loss","retransmission_rate","rapid_reconnects"]]
    st.line_chart(df_plot)
    return df

# Summarize trends clearly
def summarize_trends(df):
    summaries = []
    if df["rssi"].iloc[-1] < df["rssi"].iloc[0]:
        summaries.append("WiFi signal strength decreased over time.")
    else:
        summaries.append("WiFi signal strength is stable or improved.")
    if df["packet_loss"].iloc[-1] > df["packet_loss"].iloc[0]:
        summaries.append("Packet loss increased, possibly impacting quality.")
    else:
        summaries.append("Packet loss is stable or improved.")
    if df["retransmission_rate"].iloc[-1] > df["retransmission_rate"].iloc[0]:
        summaries.append("Retransmission rate increased, indicating more errors.")
    else:
        summaries.append("Retransmission rate is stable or improved.")
    if df["rapid_reconnects"].iloc[-1] > df["rapid_reconnects"].iloc[0]:
        summaries.append("Rapid reconnects increased, showing instability.")
    else:
        summaries.append("Rapid reconnects are stable or decreased.")
    return " ".join(summaries)

# Build messages for customer and advisor
def build_detailed_customer_message(t, markers, action):
    lines = []
    for m in markers:
        lines.append(f"{m['Marker']}: {m['Value']} — {m['Reason']}")
    lines.append(f"\nOutcome: {action['Outcome']}\nRecommended action: {action['Action']}\nAdvice: {action['Customer_message']}")
    return "\n".join(lines)

def build_detailed_advisor_message(t, markers, action, hypotheses):
    lines = []
    lines.append("Markers and telemetry details:")
    for m in markers:
        lines.append(f"- {m['Marker']}: {m['Value']} (RAG: {m['RAG']})")
        lines.append(f"  Reason: {m['Reason']}")
    lines.append("\nHypotheses considered:")
    for h in hypotheses:
        lines.append(f"- {h['Hypothesis']} (Confidence: {h['Confidence']})")
        for ev in h["Evidence"]:
            lines.append(f"  • {ev}")
    lines.append(f"\nFinal Outcome: {action['Outcome']}")
    lines.append(f"Recommended Action: {action['Action']}")
    lines.append(f"Advisor Notes: {action['Advisor_message']}")
    lines.append(f"Risk Level: {action['Risk']}")
    return "\n".join(lines)

# Run full diagnostic flow
def run_agentic_test(t, scenario_key):
    markers = build_marker_results(t)
    overall = rollup_rag(markers)
    hyps = build_hypotheses(t, markers)
    chosen = choose_best_hypothesis(hyps)
    action = decide_action(t, chosen, overall)
    cust_msg = build_detailed_customer_message(t, markers, action)
    adv_msg = build_detailed_advisor_message(t, markers, action, hyps)
    diag_text = f"Chosen hypothesis: {chosen['Hypothesis']} (Confidence: {chosen['Confidence']})\nAction taken: {action['Action']}"
    history = generate_synthetic_history(scenario_key)
    return {
        "marker_results": markers,
        "overall_rag": overall,
        "hypotheses": hyps,
        "chosen": chosen,
        "action": action,
        "detailed_customer_message": cust_msg,
        "detailed_advisor_message": adv_msg,
        "diagnostic_trace_text": diag_text,
        "history": history
    }

# --- Initialize session state ---
if "result" not in st.session_state:
    st.session_state.result = None
if "telemetry" not in st.session_state:
    st.session_state.telemetry = None
if "scenario_used" not in st.session_state:
    st.session_state.scenario_used = None

# --- Streamlit UI ---
st.title("🛰️ Test SC Agentic AI Demo with Tabs")

random_mode = st.sidebar.checkbox("Random scenario each test", True)
selected_scenario = st.sidebar.selectbox("Or pick scenario", list(SCENARIOS.keys()))

if st.button("🚀 Test my connection"):
    scenario = random.choice(list(SCENARIOS.keys())) if random_mode else selected_scenario
    telem = randomise_scenario(SCENARIOS[scenario])
    st.session_state.telemetry = telem
    st.session_state.scenario_used = scenario
    st.session_state.result = run_agentic_test(telem, scenario)

if st.session_state.result:
    result = st.session_state.result
    telemetry = st.session_state.telemetry
    action = result["action"]

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Telemetry",
        "Agentic reasoning",
        "Marker results",
        "Advisor view",
        "Customer view"
    ])

    with tab1:
        st.header("Synthetic Telemetry")
        telemetry_info = [
            {"Field": "Product", "Value": telemetry["product"], "Description": "Service area"},
            {"Field": "Device Type", "Value": telemetry["device_type"], "Description": "Device involved"},
            {"Field": "Connection Method", "Value": telemetry["connection_method"], "Description": "Connection type"},
            {"Field": "RSSI", "Value": safe_value(telemetry["rssi"], " dBm"), "Description": "WiFi signal strength"},
            {"Field": "Packet Loss", "Value": safe_value(telemetry["packet_loss"], "%"), "Description": "Percentage packets dropped"},
            {"Field": "Retransmission Rate", "Value": safe_value(telemetry["retransmission_rate"], "%"), "Description": "Packet retransmissions"},
            {"Field": "Rapid Reconnects", "Value": safe_value(telemetry["rapid_reconnects"]), "Description": "Frequent reconnect events"},
            {"Field": "Telemetry Age", "Value": f"{telemetry['telemetry_age_minutes']} minutes", "Description": "Data recency"},
            {"Field": "Line Health", "Value": telemetry["line_health"], "Description": "Broadband line status"},
            {"Field": "Known Outage", "Value": "Yes" if telemetry["known_outage"] else "No", "Description": "Service outage status"},
            {"Field": "Equipment Health", "Value": telemetry["equipment_health"], "Description": "Device condition"},
            {"Field": "Customer Symptom", "Value": telemetry["customer_symptom"], "Description": "Reported issue"},
            {"Field": "Customer Impact Score", "Value": f"{telemetry['customer_impact_score']}/10", "Description": "Severity estimate"}
        ]
        st.dataframe(pd.DataFrame(telemetry_info).set_index("Field"))

    with tab2:
        st.header("Agentic AI Reasoning & Trends")
        st.subheader("Diagnostic reasoning narrative")
        st.text_area("Reasoning", result["diagnostic_trace_text"], height=250, disabled=True)

        st.subheader("Synthetic telemetry trends")
        df_hist = pd.DataFrame(result["history"]).set_index("timestamp")
        st.line_chart(df_hist[["rssi","packet_loss","retransmission_rate","rapid_reconnects"]])
        st.info(summarize_trends(df_hist))

    with tab3:
        st.header("Marker Results")
        marker_df = pd.DataFrame(result["marker_results"])
        marker_df["RAG Status"] = marker_df["RAG"].apply(rag_badge)
        st.dataframe(marker_df[["Marker", "Value", "RAG Status", "Reason"]])

    with tab4:
        st.header("Advisor View")
        st.markdown(result["detailed_advisor_message"].replace("\n", "  \n"))

    with tab5:
        st.header("Customer View")
        st.markdown(result["detailed_customer_message"].replace("\n", "  \n"))

else:
    st.info("Click 'Test my connection' to begin.")

