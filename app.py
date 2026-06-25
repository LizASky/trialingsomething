import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime, timedelta
import plotly.graph_objs as go

# ===============================
# Synthetic Scenarios (same as before)
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
    # Add more scenarios as needed...
}

# ===============================
# Helper Functions (keep your functions here -- I have kept the core ones for brevity)
# ===============================

def safe_value(value, suffix=""):
    if value is None:
        return "Not available"
    return f"{value}{suffix}"

def rag_badge(rag):
    if rag == "Green":
        return "🟢 Green"
    if rag == "Amber":
        return "🟠 Amber"
    if rag == "Red":
        return "🔴 Red"
    if rag == "Grey":
        return "⚪ Grey"
    return rag

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

def calculate_retransmission_rag(retransmission_rate):
    if retransmission_rate is None:
        return "Grey", "Retransmission telemetry unavailable"
    if retransmission_rate <= 5:
        return "Green", "Retransmissions are low"
    elif retransmission_rate <= 15:
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
    return "Grey", "Equipment health is unknown"

def build_marker_results(t):
    results = []

    rssi_rag, rssi_reason = calculate_rssi_rag(t["rssi"])
    results.append({"Marker": "WiFi signal strength","Value": safe_value(t["rssi"], " dBm"),"RAG": rssi_rag,"Reason": rssi_reason})

    packet_rag, packet_reason = calculate_packet_loss_rag(t["packet_loss"])
    results.append({"Marker": "Packet loss","Value": safe_value(t["packet_loss"], "%"),"RAG": packet_rag,"Reason": packet_reason})

    retrans_rag, retrans_reason = calculate_retransmission_rag(t["retransmission_rate"])
    results.append({"Marker": "Retransmission rate","Value": safe_value(t["retransmission_rate"], "%"),"RAG": retrans_rag,"Reason": retrans_reason})

    reconnect_rag, reconnect_reason = calculate_reconnect_rag(t["rapid_reconnects"])
    results.append({"Marker": "Rapid reconnects","Value": safe_value(t["rapid_reconnects"]),"RAG": reconnect_rag,"Reason": reconnect_reason})

    line_rag, line_reason = calculate_line_health_rag(t["line_health"])
    results.append({"Marker": "Line health","Value": t["line_health"],"RAG": line_rag,"Reason": line_reason})

    age_rag, age_reason = calculate_telemetry_age_rag(t["telemetry_age_minutes"])
    results.append({"Marker": "Telemetry freshness","Value": f"{t['telemetry_age_minutes']} minutes old","RAG": age_rag,"Reason": age_reason})

    equipment_rag, equipment_reason = calculate_equipment_health_rag(t["equipment_health"])
    results.append({"Marker": "Equipment health","Value": t["equipment_health"],"RAG": equipment_rag,"Reason": equipment_reason})

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

# Continue with building hypotheses, choosing best hypothesis, deciding action (same logic as your original code)...

def build_hypotheses(t, marker_results):
    lookup = {m["Marker"]: m for m in marker_results}
    hypotheses = []

    if t["known_outage"]:
        hypotheses.append({"Hypothesis": "Known wider service issue","Evidence": ["Known outage flag is active","Normal troubleshooting should be stopped","Customer does not need engineer or replacement action from this journey"],"Confidence": "High"})
        return hypotheses

    if lookup["Telemetry freshness"]["RAG"] == "Grey":
        hypotheses.append({"Hypothesis": "Test cannot complete because telemetry is missing or stale","Evidence": ["Telemetry is too old or unavailable","One or more markers are Grey"],"Confidence": "High"})

    if lookup["Equipment health"]["RAG"] == "Red":
        hypotheses.append({"Hypothesis": "Equipment replacement may be required","Evidence": ["Equipment health is flagged as suspected fault","Issue has repeated after previous outcome","Connection instability is present"],"Confidence": "High"})

    if lookup["Line health"]["RAG"] == "Red":
        hypotheses.append({"Hypothesis": "Engineer visit may be required","Evidence": ["Line health is Red","Customer symptom indicates loss, drops or instability","Issue may not be fixable through self-serve steps"],"Confidence": "High"})

    if lookup["WiFi signal strength"]["RAG"] in ["Amber", "Red"]:
        hypotheses.append({"Hypothesis": "Poor WiFi signal or poor device placement","Evidence": [f"WiFi signal strength is {lookup['WiFi signal strength']['RAG']}","Connection method is {t['connection_method']}"],"Confidence": "Medium"})

    if lookup["Packet loss"]["RAG"] == "Red" and lookup["Retransmission rate"]["RAG"] in ["Amber", "Red"]:
        hypotheses.append({"Hypothesis": "WiFi interference or congestion","Evidence": ["Packet loss is Red",f"Retransmission rate is {lookup['Retransmission rate']['RAG']}"],"Confidence": "Medium"})

    if lookup["Rapid reconnects"]["RAG"] in ["Amber", "Red"]:
        hypotheses.append({"Hypothesis": "Intermittent connectivity instability","Evidence": [f"Rapid reconnects is {lookup['Rapid reconnects']['RAG']}"],"Confidence": "Medium"})

    if not hypotheses:
        hypotheses.append({"Hypothesis": "Connection appears healthy based on synthetic telemetry","Evidence": ["No Red markers detected","Telemetry is fresh","Line health is OK","No equipment fault suspected"],"Confidence": "High"})

    return hypotheses

def choose_best_hypothesis(hypotheses):
    ranking = {"High": 3,"Medium": 2,"Low": 1}
    return sorted(hypotheses,key=lambda x: ranking.get(x["Confidence"], 0),reverse=True)[0]

def decide_action(t, chosen, overall_rag):
    h = chosen["Hypothesis"]
    if t["known_outage"]:
        return {"Outcome": "Known outage detected","Action": "No action needed from the customer. We’ll keep the customer updated while the issue is fixed.","Customer_message": "There is a known issue affecting the service. The customer does not need to do anything right now — the issue is already being worked on.","Advisor_message": "Known outage path. Do not send engineer or offer replacement from this journey.","Agentic_level": "Suppress normal troubleshooting","Risk": "Low"}
    if "Test cannot complete" in h:
        return {"Outcome": "Test could not complete","Action": "Ask the customer to run the test again. If it fails again, route to advisor support.","Customer_message": "The test could not complete because some connection information was missing or out of date. Please try the test again.","Advisor_message": "Telemetry missing or stale. Do not make a firm diagnosis from this run.","Agentic_level": "Retry / gather evidence","Risk": "Low"}
    if "Equipment replacement" in h:
        return {"Outcome": "Replacement recommended","Action": "Offer replacement equipment.","Customer_message": "The test found signs that the equipment may be causing the issue. The next step is to arrange a replacement.","Advisor_message": "Equipment fault suspected. Replacement route recommended if eligibility checks pass.","Agentic_level": "Recommend replacement","Risk": "Medium"}
    if "Engineer visit" in h:
        return {"Outcome": "Engineer visit required","Action": "Book an engineer visit.","Customer_message": "The test found an issue that is unlikely to be fixed by simple self-serve steps. The next step is to book an engineer.","Advisor_message": "Line/network evidence indicates engineer route. Do not loop the customer through repeated WiFi self-serve steps.","Agentic_level": "Escalate to engineer","Risk": "Medium"}
    if "Poor WiFi signal" in h:
        if t["pod_present"]:
            next_step = "Move closer to the hub or pod, then test again."
            advisor_note = "Pod present. Recommend placement guidance and retest before replacement or engineer."
        else:
            next_step = "Move closer to the hub or consider adding a WiFi booster/pod, then test again."
            advisor_note = "No pod present. Recommend in-home WiFi improvement before escalation."
        return {"Outcome": "Weak WiFi signal","Action": next_step,"Customer_message": f"The test found weak WiFi signal where the device is being used. {next_step}","Advisor_message": advisor_note,"Agentic_level": "Recommend in-home fix","Risk": "Low"}
    if "interference or congestion" in h:
        return {"Outcome": "WiFi interference detected","Action": "Optimise the WiFi setup and test again.","Customer_message": "The test found signs of WiFi interference or congestion. The next step is to improve the WiFi setup and run the test again.","Advisor_message": "Packet loss and retransmissions indicate likely interference/congestion. Recommend WiFi optimisation before engineer route.","Agentic_level": "Recommend optimisation","Risk": "Low"}
    if "Intermittent connectivity" in h:
        return {"Outcome": "Unstable connection detected","Action": "Monitor and retest. If it keeps happening, route to replacement or engineer depending on repeat evidence.","Customer_message": "The test found signs that the connection is unstable. Please test again if it continues. If it keeps happening, the next step may be replacement equipment or an engineer.","Advisor_message": "Instability detected. Use repeat history to decide whether replacement or engineer route is more suitable.","Agentic_level": "Monitor / recommend next route","Risk": "Medium"}
    return {"Outcome": "No issue found","Action": "No action needed. Monitor and test again if the issue continues.","Customer_message": "The connection test did not find a problem from the available synthetic data. No action is needed right now.","Advisor_message": "No fault detected from this run. Reassure customer and avoid unnecessary intervention.","Agentic_level": "Explain / reassure","Risk": "Low"}

# ===============================
# Enriched explanation functions (same as before)
# ===============================

def build_detailed_customer_message(t, marker_results, action):
    lookup = {m["Marker"]: m for m in marker_results}
    lines = []
    rssi_rag = lookup["WiFi signal strength"]["RAG"]
    rssi_val = safe_value(t["rssi"], " dBm")
    if rssi_rag in ["Amber", "Red"]:
        lines.append(
            f"Your device's WiFi signal strength is {rssi_val}, which is "
            f"{'below ideal levels, which can cause buffering or disconnections.' if rssi_rag == 'Red' else 'weaker than optimal and may affect performance.'}"
        )
    packet_rag = lookup["Packet loss"]["RAG"]
    packet_val = safe_value(t["packet_loss"], "%")
    if packet_rag in ["Amber", "Red"]:
        lines.append(
            f"Packet loss is at {packet_val}, indicating { 'significant data loss impacting quality' if packet_rag == 'Red' else 'some data loss affecting connection stability.'}"
        )
    retrans_rag = lookup["Retransmission rate"]["RAG"]
    retrans_val = safe_value(t["retransmission_rate"], "%")
    if retrans_rag in ["Amber", "Red"]:
        lines.append(
            f"Data retransmissions are {retrans_val}, meaning data packets are being resent frequently due to errors, which can degrade your experience."
        )
    reconnect_rag = lookup["Rapid reconnects"]["RAG"]
    reconnect_val = safe_value(t["rapid_reconnects"])
    if reconnect_rag in ["Amber", "Red"]:
        lines.append(
            f"There were {reconnect_val} rapid reconnect events recently, indicating your connection sometimes drops and quickly reconnects — causing instability."
        )
    line_rag = lookup["Line health"]["RAG"]
    if line_rag == "Red":
        lines.append(
            "The line health is failing, which usually means a serious issue with your broadband line requiring technician intervention."
        )
    elif line_rag == "Amber":
        lines.append(
            "The line health is unstable, which might result in intermittent connection issues."
        )
    equipment_rag = lookup["Equipment health"]["RAG"]
    if equipment_rag == "Red":
        lines.append(
            "There are signs your equipment may be faulty and could need replacement."
        )
    if action.get("Customer_message"):
        lines.append(action["Customer_message"])
    return " ".join(lines)

def build_detailed_advisor_message(t, marker_results, action, hypotheses):
    lookup = {m["Marker"]: m for m in marker_results}
    lines = []
    if t["known_outage"]:
        lines.append("Known outage detected: normal troubleshooting suspended.")
    elif t["telemetry_age_minutes"] > 120:
        lines.append(f"Telemetry data is stale: {t['telemetry_age_minutes']} minutes old.")
    for marker in marker_results:
        lines.append(f"{marker['Marker']}: {marker['Value']} — {marker['Reason']}")
    lines.append("Hypotheses evaluated:")
    for h in hypotheses:
        evidence_str = "; ".join(h["Evidence"])
        lines.append(f"- {h['Hypothesis']} (Confidence: {h['Confidence']})\n  Evidence: {evidence_str}")
    lines.append(f"Chosen hypothesis: {action['Outcome']}")
    lines.append(f"Recommended action: {action['Action']}")
    lines.append(f"Risk level: {action['Risk']}")
    return "\n".join(lines)

# ===============================
# Feedback Handling
# ===============================

def add_feedback():
    st.subheader("Feedback - Help us improve!")
    feedback = st.radio("How useful was this diagnostic?", options=["Select", "Very useful", "Somewhat useful", "Not useful"], horizontal=True)
    comments = st.text_area("Additional comments or suggestions:")
    submitted = st.button("Submit Feedback")

    if submitted:
        if feedback == "Select":
            st.warning("Please select a feedback rating before submitting.")
            return
        feedback_record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scenario": st.session_state.get("scenario_used", "Unknown"),
            "feedback": feedback,
            "comments": comments,
            "chosen_outcome": st.session_state.result["action"]["Outcome"] if st.session_state.result else "Unknown"
        }
        st.session_state.feedback_log.append(feedback_record)
        st.success("Thank you for your feedback!")

# ===============================
# Synthetic Trend Data
# ===============================

def generate_synthetic_history(scenario_key, points=10):
    base = SCENARIOS[scenario_key]
    history = []
    now = datetime.now()
    for i in range(points):
        timestamp = now - timedelta(hours=points - i)
        def jitter(val, low, high, scale=3):
            if val is None:
                return None
            v = val + random.uniform(-scale, scale)
            return max(low, min(high, v))
        record = {
            "timestamp": timestamp,
            "rssi": jitter(base["rssi"], -95, -30),
            "packet_loss": jitter(base["packet_loss"], 0, 20),
            "retransmission_rate": jitter(base["retransmission_rate"], 0, 50),
            "rapid_reconnects": max(0, int(base["rapid_reconnects"] + random.randint(-1, 1))),
            "telemetry_age_minutes": max(1, base["telemetry_age_minutes"] + random.randint(-5, 5)),
            "line_health": base["line_health"],
            "equipment_health": base["equipment_health"]
        }
        history.append(record)
    return history

def plot_trends(history):
    df = pd.DataFrame(history)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["rssi"], mode='lines+markers', name="RSSI (dBm)", line=dict(color='royalblue')))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["packet_loss"], mode='lines+markers', name="Packet Loss (%)", line=dict(color='firebrick')))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["retransmission_rate"], mode='lines+markers', name="Retransmission Rate (%)", line=dict(color='green')))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["rapid_reconnects"], mode='lines+markers', name="Rapid Reconnects", line=dict(color='orange')))
    fig.update_layout(title="Connection Metrics Over Time (Simulated History)", xaxis_title="Timestamp", yaxis_title="Value", legend_title="Metrics", hovermode="x unified", height=400, margin=dict(t=50, b=40))
    st.plotly_chart(fig, use_container_width=True)
    return df

def summarize_trends(df):
    summaries = []
    if df["rssi"].iloc[-1] < df["rssi"].iloc[0]:
        summaries.append("WiFi signal strength (RSSI) decreased over time, indicating possible worsening coverage.")
    else:
        summaries.append("WiFi signal strength (RSSI) is stable or improved.")
    if df["packet_loss"].iloc[-1] > df["packet_loss"].iloc[0]:
        summaries.append("Packet loss increased, which may affect streaming quality.")
    else:
        summaries.append("Packet loss is stable or improved.")
    if df["retransmission_rate"].iloc[-1] > df["retransmission_rate"].iloc[0]:
        summaries.append("Retransmission rate increased, suggesting more errors in data transmission.")
    else:
        summaries.append("Retransmission rate is stable or improved.")
    if df["rapid_reconnects"].iloc[-1] > df["rapid_reconnects"].iloc[0]:
        summaries.append("Rapid reconnect events have become more frequent, indicating unstable connection.")
    else:
        summaries.append("Rapid reconnects are stable or reduced.")
    return " ".join(summaries)

# ===============================
# Personalization
# ===============================
def personalization_select():
    st.sidebar.header("User Profile (Demo)")
    user_type = st.sidebar.selectbox("Select user type:", ["General Customer", "Tech-Savvy Customer", "Advisor"])
    st.session_state["user_type"] = user_type

# ===============================
# Telemetry Randomizer
# ===============================
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

# ===============================
# Agentic test execution
# ===============================
def run_agentic_test(t):
    marker_results = build_marker_results(t)
    overall_rag = rollup_rag(marker_results)
    hypotheses = build_hypotheses(t, marker_results)
    chosen = choose_best_hypothesis(hypotheses)
    action = decide_action(t, chosen, overall_rag)
    detailed_customer_message = build_detailed_customer_message(t, marker_results, action)
    detailed_advisor_message = build_detailed_advisor_message(t, marker_results, action, hypotheses)
    diagnostic_trace_text = (
        f"Telemetry age: {t['telemetry_age_minutes']} mins\n" +
        f"Known outage: {'Yes' if t['known_outage'] else 'No'}\n" +
        f"Hypotheses: {', '.join([h['Hypothesis'] + f'({h['Confidence']})' for h in hypotheses])}\n" +
        f"Chosen hypothesis: {chosen['Hypothesis']}\nAction: {action['Action']}\nConfidence: {chosen['Confidence']}"
    )
    history = generate_synthetic_history(st.session_state.scenario_used if "scenario_used" in st.session_state else list(SCENARIOS.keys())[0])
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

# ===============================
# Streamlit App UI
# ===============================

# Initialize session state for feedback and logs
if "feedback_log" not in st.session_state:
    st.session_state.feedback_log = []

if "logs" not in st.session_state:
    st.session_state.logs = []

personalization_select()

st.title("🛰️ Test SC Enhanced Agentic AI Connection Diagnosis")

with st.sidebar:
    st.header("Demo mode options")
    random_mode = st.checkbox("Random scenario on each test", True)
    selected_scenario = st.selectbox("Or select a specific scenario", list(SCENARIOS.keys()))
    st.markdown("---")
    st.subheader("Submit Device Logs / Errors")
    log_input = st.text_area("Paste device or error logs here:")
    if st.button("Submit Logs"):
        if log_input.strip():
            st.session_state.logs.append({"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "log": log_input})
            st.success("Log submitted.")
            st.experimental_rerun()
    st.markdown("---")
    st.subheader("Feedback")
    add_feedback()

run_test = st.button("🚀 Test my connection")

if run_test or "result" in st.session_state:
    if run_test:
        if random_mode:
            scenario = random.choice(list(SCENARIOS.keys()))
        else:
            scenario = selected_scenario
        telemetry = randomise_scenario(SCENARIOS[scenario])
        st.session_state.telemetry = telemetry
        st.session_state.scenario_used = scenario
        st.session_state.result = run_agentic_test(telemetry)

    result = st.session_state.result
    telemetry = st.session_state.telemetry
    action = result["action"]

    st.markdown(f"### Synthetic scenario used: **{st.session_state.scenario_used}**")

    cols = st.columns(4)
    cols[0].metric("Overall status", rag_badge(result["overall_rag"]))
    cols[1].metric("Outcome", action["Outcome"])
    cols[2].metric("Confidence", result["chosen"]["Confidence"])
    cols[3].metric("Next step type", action["Agentic_level"])

    user_type = st.session_state.get("user_type", "General Customer")
    if user_type in ["Tech-Savvy Customer", "Advisor"]:
        st.info(result["detailed_advisor_message"])
    else:
        st.success(result["detailed_customer_message"])

    st.subheader("Recommended next step")
    st.write(action["Action"])
    st.info(f"Confidence info: {result['chosen']['Confidence']} - {action.get('Risk')} risk")

    st.markdown("---")
    st.subheader("Connection Metrics Trend (Simulated History)")
    df_hist = plot_trends(result["history"])
    summary = summarize_trends(df_hist)
    st.info(summary)

    st.markdown("---")
    st.subheader("Synthetic telemetry details")
    telemetry_rows = [
        {"Field": "Product", "Value": telemetry["product"]},
        {"Field": "Device type", "Value": telemetry["device_type"]},
        {"Field": "Connection method", "Value": telemetry["connection_method"]},
        {"Field": "RSSI", "Value": safe_value(telemetry["rssi"], " dBm")},
        {"Field": "Packet loss", "Value": safe_value(telemetry["packet_loss"], "%")},
        {"Field": "Retransmission rate", "Value": safe_value(telemetry["retransmission_rate"], "%")},
        {"Field": "Rapid reconnects", "Value": safe_value(telemetry["rapid_reconnects"])},
        {"Field": "Telemetry age", "Value": f"{telemetry['telemetry_age_minutes']} minutes"},
        {"Field": "Line health", "Value": telemetry["line_health"]},
        {"Field": "Known outage", "Value": "Yes" if telemetry["known_outage"] else "No"},
        {"Field": "Equipment health", "Value": telemetry["equipment_health"]},
        {"Field": "Customer symptom", "Value": telemetry["customer_symptom"]},
        {"Field": "Customer impact score", "Value": f"{telemetry['customer_impact_score']}/10"},
    ]
    st.dataframe(pd.DataFrame(telemetry_rows), use_container_width=True)

    st.markdown("---")
    st.subheader("Marker evaluations")
    marker_df = pd.DataFrame(result["marker_results"])
    marker_df["RAG"] = marker_df["RAG"].apply(rag_badge)
    st.dataframe(marker_df, use_container_width=True)

    st.markdown("---")
    st.subheader("Diagnostic reasoning narrative")
    st.text_area("Details behind the diagnosis", result["diagnostic_trace_text"], height=250, disabled=True)

    st.markdown("---")
    st.subheader("Device Logs")
    if st.session_state.logs:
        df_logs = pd.DataFrame(st.session_state.logs)
        st.dataframe(df_logs, use_container_width=True)
    else:
        st.info("No device logs submitted yet.")

    st.markdown("---")
    st.subheader("Feedback summary")
    if st.session_state.feedback_log:
        st.dataframe(pd.DataFrame(st.session_state.feedback_log), use_container_width=True)
    else:
        st.info("No feedback submitted yet.")

else:
    st.info("Click 'Test my connection' to begin the diagnosis.")



