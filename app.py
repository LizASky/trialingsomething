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

# --- RAG Calculation Functions ---
def safe_value(value, suffix=""):
    return "Not available" if value is None else f"{value}{suffix}"

def rag_badge(rag):
    return {"Green": "🟢 Green", "Amber": "🟠 Amber", "Red": "🔴 Red", "Grey": "⚪ Grey"}.get(rag, rag)

def calculate_rssi_rag(rssi):
    if rssi is None:
        return "Grey", "RSSI telemetry unavailable"
    if rssi >= -67:
        return "Green", "RSSI is healthy"
    elif rssi >= -75:
        return "Amber", "RSSI is degraded"
    else:
        return "Red", "RSSI is poor"

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
        return "Green", "Reconnect behavior stable"
    elif rapid_reconnects <= 4:
        return "Amber", "Some reconnect instability"
    else:
        return "Red", "Frequent reconnect instability"

def calculate_line_health_rag(line_health):
    if line_health == "OK":
        return "Green", "Line is healthy"
    if line_health == "Unstable":
        return "Amber", "Line is unstable"
    if line_health == "Fail":
        return "Red", "Line has failed"
    return "Grey", "Line health unknown"

def calculate_telemetry_age_rag(age):
    if age is None:
        return "Grey", "Telemetry age unavailable"
    if age <= 30:
        return "Green", "Telemetry is fresh"
    elif age <=120:
        return "Amber", "Telemetry is slightly old"
    else:
        return "Grey", "Telemetry too old for diagnosis"

def calculate_equipment_health_rag(health):
    if health == "OK":
        return "Green", "Equipment is OK"
    if health == "Suspected fault":
        return "Red", "Suspected equipment fault"
    return "Grey", "Equipment health unknown"

# --- Build markers with explanations ---
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

# --- Hypotheses, decision logic ---
def build_hypotheses(t, marker_results):
    lookup = {m["Marker"]: m for m in marker_results}
    hypotheses = []
    if t["known_outage"]:
        hypotheses.append({"Hypothesis": "Known service outage", "Evidence": ["Outage flag is true"], "Confidence": "High"})
        return hypotheses
    if lookup["Telemetry freshness"]["RAG"] == "Grey":
        hypotheses.append({"Hypothesis": "Telemetry stale or missing", "Evidence": ["Telemetry data is too old or absent"], "Confidence": "High"})
    if lookup["Equipment health"]["RAG"] == "Red":
        hypotheses.append({"Hypothesis": "Equipment fault suspected", "Evidence": ["Equipment flagged as faulty"], "Confidence": "High"})
    if lookup["Line health"]["RAG"] == "Red":
        hypotheses.append({"Hypothesis": "Line failure", "Evidence": ["Line health is red"], "Confidence": "High"})
    if lookup["WiFi signal strength"]["RAG"] in ["Amber", "Red"]:
        hypotheses.append({"Hypothesis": "Poor WiFi quality", "Evidence": [f"Signal strength is {lookup['WiFi signal strength']['RAG']}"], "Confidence": "Medium"})
    if lookup["Packet loss"]["RAG"] == "Red" and lookup["Retransmission rate"]["RAG"] in ["Amber", "Red"]:
        hypotheses.append({"Hypothesis": "WiFi interference", "Evidence": ["Packet loss is high", "Retransmissions elevated"], "Confidence": "Medium"})
    if lookup["Rapid reconnects"]["RAG"] in ["Amber", "Red"]:
        hypotheses.append({"Hypothesis": "Connection instability", "Evidence": ["Rapid reconnects detected"], "Confidence": "Medium"})
    if not hypotheses:
        hypotheses.append({"Hypothesis": "Connection healthy", "Evidence": ["No high severity markers"], "Confidence": "High"})
    return hypotheses

def choose_best_hypothesis(hypotheses):
    rank = {"High": 3, "Medium": 2, "Low": 1}
    return sorted(hypotheses, key=lambda x: rank.get(x["Confidence"], 0), reverse=True)[0]

def decide_action(t, chosen, overall_rag):
    h = chosen["Hypothesis"]
    if t["known_outage"]:
        return {
            "Outcome": "Known outage detected",
            "Action": "No action needed; issue is being resolved.",
            "Customer_message": "There is a known outage affecting your service.",
            "Advisor_message": "Service outage ongoing; no further action from this test needed.",
            "Agentic_level": "Suspend troubleshooting",
            "Risk": "Low"
        }
    if "Telemetry stale" in h or "missing" in h:
        return {
            "Outcome": "Test incomplete",
            "Action": "Ask customer to retry test or escalate if issue persists.",
            "Customer_message": "The test could not complete because of missing or stale data.",
            "Advisor_message": "Insufficient telemetry; consider retest or manual review.",
            "Agentic_level": "Retry",
            "Risk": "Low"
        }
    if "Equipment fault" in h:
        return {
            "Outcome": "Equipment replacement recommended",
            "Action": "Recommend equipment replacement.",
            "Customer_message": "Faulty equipment detected; replacement advised.",
            "Advisor_message": "Equipment likely faulty; replace if eligible.",
            "Agentic_level": "Recommend replacement",
            "Risk": "Medium"
        }
    if "Line failure" in h:
        return {
            "Outcome": "Engineer visit needed",
            "Action": "Schedule engineer visit.",
            "Customer_message": "Line issue requires engineer intervention.",
            "Advisor_message": "Line health critical; escalate to engineering.",
            "Agentic_level": "Escalate",
            "Risk": "High"
        }
    if "Poor WiFi" in h:
        return {
            "Outcome": "Weak WiFi signal",
            "Action": "Advise customer to improve WiFi placement or add boosters.",
            "Customer_message": "Weak WiFi signal detected; try moving closer to hub.",
            "Advisor_message": "WiFi issues; advise in-home fixes before escalation.",
            "Agentic_level": "Recommend fix",
            "Risk": "Low"
        }
    if "WiFi interference" in h:
        return {
            "Outcome": "WiFi interference detected",
            "Action": "Advise optimizing WiFi channel or setup.",
            "Customer_message": "WiFi interference likely; optimize your setup.",
            "Advisor_message": "Elevated packet loss and retransmissions; interference suspected.",
            "Agentic_level": "Recommend optimization",
            "Risk": "Low"
        }
    if "Connection instability" in h:
        return {
            "Outcome": "Unstable connection detected",
            "Action": "Monitor issue; escalate if persistent.",
            "Customer_message": "Your connection is unstable; please monitor.",
            "Advisor_message": "Instability seen; follow up with repeat testing.",
            "Agentic_level": "Monitor",
            "Risk": "Medium"
        }
    return {
        "Outcome": "No issue found",
        "Action": "No immediate action needed.",
        "Customer_message": "Your connection looks healthy.",
        "Advisor_message": "No fault detected.",
        "Agentic_level": "Explain",
        "Risk": "Low"
    }

# --- Randomize telemetry data ---
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

# --- Generate synthetic history for trend charts ---
def generate_synthetic_history(scenario_key):
    base = SCENARIOS[scenario_key]
    history = []
    now = datetime.now()
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
            "rapid_reconnects": max(0, int(base["rapid_reconnects"] + random.randint(-1, 1)))
        })
    return history

# --- Summarize trends for user-friendly explanation ---
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

# --- Build detailed messages ---
def build_detailed_customer_message(t, markers, action):
    lines = []
    for m in markers:
        lines.append(f"{m['Marker']}: {m['Value']} — {m['Reason']}")
    lines.append(f"\nOutcome: {action['Outcome']}")
    lines.append(f"Recommended action: {action['Action']}")
    lines.append(f"Advice: {action['Customer_message']}")
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

# --- Run the main agentic AI diagnostic test ---
def run_agentic_test(t, scenario_key):
    markers = build_marker_results(t)
    overall_rag = rollup_rag(markers)
    hypotheses = build_hypotheses(t, markers)
    chosen = choose_best_hypothesis(hypotheses)
    action = decide_action(t, chosen, overall_rag)
    cust_msg = build_detailed_customer_message(t, markers, action)
    adv_msg = build_detailed_advisor_message(t, markers, action, hypotheses)
    diag_trace = f"Chosen hypothesis: {chosen['Hypothesis']} (Confidence: {chosen['Confidence']})\nAction: {action['Action']}"
    history = generate_synthetic_history(scenario_key)
    return {
        "marker_results": markers,
        "overall_rag": overall_rag,
        "hypotheses": hypotheses,
        "chosen": chosen,
        "action": action,
        "detailed_customer_message": cust_msg,
        "detailed_advisor_message": adv_msg,
        "diagnostic_trace_text": diag_trace,
        "history": history
    }

# --- Initialize session state ---
if "result" not in st.session_state:
    st.session_state.result = None
if "telemetry" not in st.session_state:
    st.session_state.telemetry = None
if "scenario_used" not in st.session_state:
    st.session_state.scenario_used = None

# --- Main UI ---
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
        st.header("Synthetic telemetry")
        telemetry_data = [
            {"Field": k, "Value": v} for k,v in telemetry.items() if k != "repeat_issue_7_days"
        ]
        st.dataframe(pd.DataFrame(telemetry_data).set_index("Field"))

    with tab2:
        st.header("Agentic AI reasoning")
        st.text_area("Diagnostic narrative", result["diagnostic_trace_text"], height=250, disabled=True)
        st.subheader("Telemetry metrics trends")
        df_hist = pd.DataFrame(result["history"]).set_index("timestamp")
        st.line_chart(df_hist[["rssi", "packet_loss", "retransmission_rate", "rapid_reconnects"]])
        st.info(summarize_trends(df_hist))

    with tab3:
        st.header("Marker results")
        df_markers = pd.DataFrame(result["marker_results"])
        df_markers["RAG Status"] = df_markers["RAG"].apply(rag_badge)
        st.dataframe(df_markers[["Marker", "Value", "RAG Status", "Reason"]])

    with tab4:
        st.header("Advisor view")
        summary_data = {
            "Field": [
                "Outcome",
                "Recommended Action",
                "Chosen Hypothesis",
                "Confidence",
                "Risk"
            ],
            "Value": [
                action.get("Outcome", "N/A"),
                action.get("Action", "N/A"),
                result["chosen"].get("Hypothesis", "N/A"),
                result["chosen"].get("Confidence", "N/A"),
                action.get("Risk", "N/A"),
            ]
        }
        st.table(pd.DataFrame(summary_data))
        st.subheader("Hypotheses and evidence")
        for h in result["hypotheses"]:
            st.markdown(f"**{h['Hypothesis']}** (Confidence: {h['Confidence']})")
            st.write(", ".join(h["Evidence"]))
            st.markdown("---")

    with tab5:
        st.header("Customer view")
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
        st.markdown(f"**Next step:** {action.get('Action', '')}")

else:
    st.info("Click 'Test my connection' to begin testing.")


