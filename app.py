import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# === Synthetic scenarios ===
SCENARIOS = {
    "Healthy connection": {
        "product": "Broadband",
        "device_type": "Laptop",
        "connection_method": "Ethernet",
        "rssi": None,
        "packet_loss": 0.1,
        "retransmission_rate": 2,
        "rapid_reconnects": 0,
        "telemetry_age_minutes": 10,
        "line_health": "OK",
        "known_outage": False,
        "repeat_issue_7_days": False,
        "previous_outcome": "No previous journey",
        "hub_model": "Hub 6",
        "pod_present": False,
        "customer_symptom": "No issue reported",
        "customer_impact_score": 1,
        "equipment_health": "OK",
    },
    "WiFi congestion": {
        "product": "Broadband",
        "device_type": "Mobile",
        "connection_method": "2.4GHz WiFi",
        "rssi": -75,
        "packet_loss": 4,
        "retransmission_rate": 15,
        "rapid_reconnects": 3,
        "telemetry_age_minutes": 12,
        "line_health": "OK",
        "known_outage": False,
        "repeat_issue_7_days": True,
        "previous_outcome": "Self-serve guidance shown",
        "hub_model": "Hub 5",
        "pod_present": True,
        "customer_symptom": "Buffering or poor picture quality",
        "customer_impact_score": 7,
        "equipment_health": "OK",
    },
    "Weak WiFi": {
        "product": "Broadband",
        "device_type": "Laptop",
        "connection_method": "5GHz WiFi",
        "rssi": -85,
        "packet_loss": 1.5,
        "retransmission_rate": 5,
        "rapid_reconnects": 2,
        "telemetry_age_minutes": 15,
        "line_health": "OK",
        "known_outage": False,
        "repeat_issue_7_days": False,
        "previous_outcome": "No previous journey",
        "hub_model": "Hub 6",
        "pod_present": False,
        "customer_symptom": "Slow web browsing",
        "customer_impact_score": 5,
        "equipment_health": "OK",
    },
    "Suspected equipment fault": {
        "product": "Broadband",
        "device_type": "Hub",
        "connection_method": "Ethernet",
        "rssi": None,
        "packet_loss": 7,
        "retransmission_rate": 25,
        "rapid_reconnects": 5,
        "telemetry_age_minutes": 10,
        "line_health": "OK",
        "known_outage": False,
        "repeat_issue_7_days": True,
        "previous_outcome": "Issue repeated after self-serve steps",
        "hub_model": "Hub 4",
        "pod_present": False,
        "customer_symptom": "Frequent drops",
        "customer_impact_score": 8,
        "equipment_health": "Suspected fault",
    },
}

# === Helper functions ===
def safe_value(value, suffix=""):
    return f"{value}{suffix}" if value is not None else "Not available"

def rag_badge(rag):
    return {
        "Green": "🟢 Green", "Amber": "🟠 Amber", "Red": "🔴 Red", "Grey": "⚪ Grey"
    }.get(rag, rag)

def calculate_rssi_rag(rssi):
    if rssi is None:
        return "Grey", "Signal strength unavailable"
    if rssi >= -67:
        return "Green", "Good WiFi signal strength"
    elif -75 <= rssi < -67:
        return "Amber", "Moderate WiFi signal strength"
    else:
        return "Red", "Poor WiFi signal strength"

def calculate_packet_loss_rag(packet_loss):
    if packet_loss is None:
        return "Grey", "Packet loss data unavailable"
    if packet_loss <= 1:
        return "Green", "Low packet loss"
    elif packet_loss <= 3:
        return "Amber", "Elevated packet loss"
    else:
        return "Red", "High packet loss"

def calculate_retransmission_rag(retransmission_rate):
    if retransmission_rate is None:
        return "Grey", "Retransmission data unavailable"
    if retransmission_rate <= 5:
        return "Green", "Low retransmission rate"
    elif retransmission_rate <= 15:
        return "Amber", "Elevated retransmission rate"
    else:
        return "Red", "High retransmission rate"

def calculate_reconnect_rag(rapid_reconnects):
    if rapid_reconnects is None:
        return "Grey", "Reconnect data unavailable"
    if rapid_reconnects <= 1:
        return "Green", "Stable connection"
    elif rapid_reconnects <= 4:
        return "Amber", "Moderate instability"
    else:
        return "Red", "High instability"

def calculate_line_health_rag(line_health):
    return {
        "OK": ("Green", "Line is healthy"),
        "Unstable": ("Amber", "Line is unstable"),
        "Fail": ("Red", "Line has failed")
    }.get(line_health, ("Grey", "Line health unknown"))

def calculate_telemetry_age_rag(age):
    if age is None:
        return "Grey", "Telemetry age unavailable"
    if age <= 30:
        return "Green", "Telemetry is fresh"
    elif age <= 120:
        return "Amber", "Telemetry is aging"
    else:
        return "Grey", "Telemetry stale"

def calculate_equipment_health_rag(equipment_health):
    return {
        "OK": ("Green", "Equipment is OK"),
        "Suspected fault": ("Red", "Potential equipment fault")
    }.get(equipment_health, ("Grey", "Equipment health unknown"))

def build_marker_results(t):
    results = []
    metrics = [
        ("rssi", "WiFi signal strength", calculate_rssi_rag, " dBm"),
        ("packet_loss", "Packet loss", calculate_packet_loss_rag, "%"),
        ("retransmission_rate", "Retransmission rate", calculate_retransmission_rag, "%"),
        ("rapid_reconnects", "Rapid reconnects", calculate_reconnect_rag, ""),
        ("line_health", "Line health", calculate_line_health_rag, ""),
        ("telemetry_age_minutes", "Telemetry freshness", calculate_telemetry_age_rag, " minutes old"),
        ("equipment_health", "Equipment health", calculate_equipment_health_rag, ""),
    ]
    for key, name, calc_func, suffix in metrics:
        value = t.get(key)
        rag, reason = calc_func(value)
        val_str = safe_value(value, suffix)
        results.append({"Marker": name, "Value": val_str, "RAG": rag, "Reason": reason})
    return results

def rollup_rag(marker_results):
    priority = {"Red": 3, "Amber": 2, "Green": 1, "Grey": 0}
    max_priority = max(priority[m["RAG"]] for m in marker_results)
    return next(key for key, val in priority.items() if val == max_priority)

def build_hypotheses(t, marker_results):
    lookup = {m["Marker"]: m for m in marker_results}
    hypotheses = []

    if t.get("known_outage"):
        hypotheses.append({"Hypothesis": "Known service outage", "Evidence": ["Known outage active"], "Confidence": "High"})
        return hypotheses

    if lookup["Telemetry freshness"]["RAG"] == "Grey":
        hypotheses.append({"Hypothesis": "Telemetry missing or stale", "Evidence": ["Stale or missing telemetry"], "Confidence": "High"})

    if lookup["Equipment health"]["RAG"] == "Red":
        hypotheses.append({"Hypothesis": "Equipment fault suspected", "Evidence": ["Equipment fault flag"], "Confidence": "High"})

    if lookup["Line health"]["RAG"] == "Red":
        hypotheses.append({"Hypothesis": "Line failure", "Evidence": ["Line health failure"], "Confidence": "High"})

    if lookup["WiFi signal strength"]["RAG"] in ("Amber", "Red"):
        hypotheses.append({"Hypothesis": "Poor WiFi signal", "Evidence": ["Weak WiFi signal"], "Confidence": "Medium"})

    if (lookup["Packet loss"]["RAG"] == "Red" and lookup["Retransmission rate"]["RAG"] in ("Amber", "Red")):
        hypotheses.append({"Hypothesis": "WiFi interference or congestion", "Evidence": ["High packet loss and retransmissions"], "Confidence": "Medium"})

    if lookup["Rapid reconnects"]["RAG"] in ("Amber", "Red"):
        hypotheses.append({"Hypothesis": "Connection instability", "Evidence": ["Frequent rapid reconnects"], "Confidence": "Medium"})

    if not hypotheses:
        hypotheses.append({"Hypothesis": "Healthy connection", "Evidence": ["No red flags"], "Confidence": "High"})

    return hypotheses

def choose_best_hypothesis(hypotheses):
    ranking = {"High": 3, "Medium": 2, "Low": 1}
    return max(hypotheses, key=lambda h: ranking.get(h["Confidence"], 0))

def decide_action(t, chosen, overall_rag):
    h = chosen["Hypothesis"].lower()
    if t.get("known_outage"):
        return {
            "Outcome": "Known outage detected",
            "Action": "No action needed; service issue being resolved.",
            "Customer_message": "Known outage affecting your service.",
            "Advisor_message": "Known outage; no escalation.",
            "Agentic_level": "Suppress troubleshooting",
            "Risk": "Low",
        }
    if "telemetry missing" in h or "stale" in h:
        return {
            "Outcome": "Test incomplete",
            "Action": "Retry diagnostic test or escalate if persists.",
            "Customer_message": "Diagnostic incomplete due to telemetry issues.",
            "Advisor_message": "Telemetry stale or missing.",
            "Agentic_level": "Retry",
            "Risk": "Low",
        }
    if "equipment fault" in h:
        return {
            "Outcome": "Equipment replacement recommended",
            "Action": "Recommend equipment replacement.",
            "Customer_message": "Equipment fault suspected; replacement advised.",
            "Advisor_message": "Suspected equipment fault.",
            "Agentic_level": "Recommend replacement",
            "Risk": "Medium",
        }
    if "line failure" in h:
        return {
            "Outcome": "Engineer visit required",
            "Action": "Schedule an engineer visit.",
            "Customer_message": "Service issue requires engineer",
            "Advisor_message": "Suspected line failure.",
            "Agentic_level": "Escalate",
            "Risk": "Medium",
        }
    if "poor wifi" in h:
        return {
            "Outcome": "Weak WiFi signal",
            "Action": "Advise improving WiFi placement or boosters.",
            "Customer_message": "Weak WiFi signal detected; move closer to router.",
            "Advisor_message": "WiFi signal weak; recommend fixes.",
            "Agentic_level": "Recommend fix",
            "Risk": "Low",
        }
    if "interference" in h:
        return {
            "Outcome": "WiFi interference detected",
            "Action": "Optimize WiFi setup and retest.",
            "Customer_message": "WiFi interference likely; optimize setup.",
            "Advisor_message": "High packet loss and retransmissions.",
            "Agentic_level": "Recommend optimization",
            "Risk": "Low",
        }
    if "instability" in h:
        return {
            "Outcome": "Connection instability detected",
            "Action": "Monitor connection and retest.",
            "Customer_message": "Connection unstable; please monitor.",
            "Advisor_message": "Intermittent connection issues.",
            "Agentic_level": "Monitor",
            "Risk": "Medium",
        }
    return {
        "Outcome": "No issue found",
        "Action": "No action needed.",
        "Customer_message": "Your connection looks healthy.",
        "Advisor_message": "No faults detected.",
        "Agentic_level": "Explain",
        "Risk": "Low",
    }

def generate_synthetic_history(scenario_key):
    base = SCENARIOS[scenario_key]
    now = datetime.now()
    hist = []
    for i in range(10):
        ts = now - timedelta(hours=10 - i)
        noise = lambda v, l, h: max(l, min(h, v + random.uniform(-3, 3))) if v is not None else None
        hist.append({
            "timestamp": ts,
            "rssi": noise(base.get("rssi"), -95, -30),
            "packet_loss": noise(base.get("packet_loss"), 0, 20),
            "retransmission_rate": noise(base.get("retransmission_rate"), 0, 50),
            "rapid_reconnects": max(0, int(base.get("rapid_reconnects", 0) + random.randint(-1, 1))),
        })
    return hist

def summarize_trends(df):
    if df.empty or len(df) < 2:
        return "Insufficient data for trend analysis."
    summaries = []
    if df["rssi"].iloc[-1] < df["rssi"].iloc[0]:
        summaries.append("WiFi signal strength decreased over time.")
    else:
        summaries.append("WiFi signal strength stable or improved.")
    if df["packet_loss"].iloc[-1] > df["packet_loss"].iloc[0]:
        summaries.append("Packet loss increased; may affect quality.")
    else:
        summaries.append("Packet loss stable or improved.")
    if df["retransmission_rate"].iloc[-1] > df["retransmission_rate"].iloc[0]:
        summaries.append("Retransmission rate increased; indicates errors.")
    else:
        summaries.append("Retransmission rate stable or improved.")
    if df["rapid_reconnects"].iloc[-1] > df["rapid_reconnects"].iloc[0]:
        summaries.append("Rapid reconnects more frequent; showing instability.")
    else:
        summaries.append("Rapid reconnects stable or decreased.")
    return " ".join(summaries)

def build_detailed_customer_message(t, markers, action):
    lines = [f"{m['Marker']}: {m['Value']} — {m['Reason']}" for m in markers]
    lines.append('')
    lines.append(f"Diagnosis outcome: {action['Outcome']}")
    lines.append(f"Recommended action: {action['Action']}")
    lines.append(f"Customer advice: {action['Customer_message']}")
    return "\n".join(lines)

def build_detailed_advisor_message(t, markers, action, hypotheses):
    lines = ["Markers and telemetry:"]
    for m in markers:
        lines.append(f"- {m['Marker']}: {m['Value']} (RAG {m['RAG']}) — {m['Reason']}")
    lines.append("\nHypotheses:")
    for h in hypotheses:
        lines.append(f"- {h['Hypothesis']} (Confidence: {h['Confidence']})")
        for ev in h["Evidence"]:
            lines.append(f"  • {ev}")
    lines.append("\nFinal recommendation:")
    lines.append(f"Outcome: {action['Outcome']}")
    lines.append(f"Action: {action['Action']}")
    lines.append(f"Advisor notes: {action['Advisor_message']}")
    return "\n".join(lines)

def run_agentic_test(telemetry, scenario):
    markers = build_marker_results(telemetry)
    overall_rag = rollup_rag(markers)
    hypotheses = build_hypotheses(telemetry, markers)
    chosen = choose_best_hypothesis(hypotheses)
    action = decide_action(telemetry, chosen, overall_rag)
    detailed_customer_message = build_detailed_customer_message(telemetry, markers, action)
    detailed_advisor_message = build_detailed_advisor_message(telemetry, markers, action, hypotheses)
    diagnostic_trace_text = f"Chosen hypothesis: {chosen['Hypothesis']} (Confidence: {chosen['Confidence']})\nAction: {action['Action']}"
    history = generate_synthetic_history(scenario)
    return {
        "marker_results": markers,
        "overall_rag": overall_rag,
        "hypotheses": hypotheses,
        "chosen": chosen,
        "action": action,
        "detailed_customer_message": detailed_customer_message,
        "detailed_advisor_message": detailed_advisor_message,
        "diagnostic_trace_text": diagnostic_trace_text,
        "history": history
    }

# --- Streamlit app UI ---

if "result" not in st.session_state:
    st.session_state.result = None
if "telemetry" not in st.session_state:
    st.session_state.telemetry = None
if "scenario_used" not in st.session_state:
    st.session_state.scenario_used = None

st.title("🛰️ Synthetic Agentic AI Connection Test Demo")

random_mode = st.sidebar.checkbox("Random scenario every test", True)
selected_scenario = st.sidebar.selectbox("Or pick synthetic scenario", list(SCENARIOS.keys()))

if st.button("🚀 Test my connection"):
    # Using synthetic random telemetry per your request
    telemetry = generate_synthetic_telemetry()
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
    cols[3].metric("Risk", action.get("Risk", "N/A"))
    cols[4].metric("Next Step", action.get("Agentic_level", "N/A"))

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Telemetry", "Agentic Reasoning", "Marker Results", "Advisor View", "Customer View"
    ])

    with tab1:
        st.header("Synthetic Telemetry")
        telemetry_info = [
            {"Field": "Product", "Value": telemetry["product"], "Meaning": "Type of service being tested"},
            {"Field": "Device Type", "Value": telemetry["device_type"], "Meaning": "Device you are using"},
            {"Field": "Connection Method", "Value": telemetry["connection_method"], "Meaning": "How your device connects"},
            {"Field": "RSSI", "Value": safe_value(telemetry["rssi"], " dBm"), "Meaning": "WiFi signal strength"},
            {"Field": "Packet Loss", "Value": safe_value(telemetry["packet_loss"], "%"), "Meaning": "Packet loss percentage"},
            {"Field": "Retransmission Rate", "Value": safe_value(telemetry["retransmission_rate"], "%"), "Meaning": "Packet retransmission rate"},
            {"Field": "Rapid Reconnects", "Value": safe_value(telemetry["rapid_reconnects"]), "Meaning": "Number of rapid reconnect events"},
            {"Field": "Telemetry Age", "Value": f"{telemetry['telemetry_age_minutes']} minutes", "Meaning": "Recency of telemetry data"},
            {"Field": "Line Health", "Value": telemetry["line_health"], "Meaning": "Broadband line health"},
            {"Field": "Known Outage", "Value": "Yes" if telemetry["known_outage"] else "No", "Meaning": "Known service outages"},
            {"Field": "Equipment Health", "Value": telemetry["equipment_health"], "Meaning": "Equipment condition"},
            {"Field": "Customer Symptom", "Value": telemetry["customer_symptom"], "Meaning": "Reported symptom"},
            {"Field": "Customer Impact Score", "Value": f"{telemetry['customer_impact_score']}/10", "Meaning": "Severity score"},
        ]
        st.table(pd.DataFrame(telemetry_info).set_index("Field"))

    with tab2:
        st.header("Agentic AI Reasoning")
        st.text_area("Diagnostic narrative", result["diagnostic_trace_text"], height=250, disabled=True)
        history_df = pd.DataFrame(result["history"]).set_index("timestamp")
        st.line_chart(history_df[["rssi", "packet_loss", "retransmission_rate", "rapid_reconnects"]])
        st.info(summarize_trends(history_df))

    with tab3:
        st.header("Marker Results")
        markers_df = pd.DataFrame(result["marker_results"])
        markers_df["RAG Status"] = markers_df["RAG"].apply(rag_badge)
        st.table(markers_df[["Marker", "Value", "RAG Status", "Reason"]])

    with tab4:
        st.header("Advisor View")
        advisor_summary = {
            "Field": ["Outcome", "Recommended Action", "Chosen Hypothesis", "Confidence Level", "Risk Level"],
            "Value": [
                action.get("Outcome"),
                action.get("Action"),
                result["chosen"].get("Hypothesis"),
                result["chosen"].get("Confidence"),
                action.get("Risk")
            ]
        }
        st.table(pd.DataFrame(advisor_summary))
        st.subheader("Hypotheses & Evidence")
        for h in result["hypotheses"]:
            st.markdown(f"**{h['Hypothesis']}** — Confidence: {h['Confidence']}")
            st.write(", ".join(h["Evidence"]))
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
        customer_advice = advice_map.get(action.get("Outcome", ""), action.get("Customer_message", ""))
        st.success(customer_advice)
        st.markdown(f"**Next step:** {action.get('Action', 'No further action needed')}")
else:
    st.info("Click 'Test my connection' to start.")


