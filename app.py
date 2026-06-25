import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# --- Helper functions and diagnostics logic ---

def safe_value(value, suffix=""):
    return "Not available" if value is None else f"{value}{suffix}"

def rag_badge(rag):
    return {
        "Green": "🟢 Green",
        "Amber": "🟠 Amber",
        "Red": "🔴 Red",
        "Grey": "⚪ Grey"
    }.get(rag, rag)

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

def calculate_equipment_health_rag(health):
    if health == "OK":
        return "Green", "No suspected equipment fault"
    if health == "Suspected fault":
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

def build_hypotheses(t, markers):
    lookup = {m["Marker"]: m for m in markers}
    hyps = []
    if t["known_outage"]:
        hyps.append({"Hypothesis": "Known wider service issue", "Evidence": ["Known outage active", "Stop troubleshooting", "No engineer/replacement needed"], "Confidence": "High"})
        return hyps
    if lookup["Telemetry freshness"]["RAG"] == "Grey":
        hyps.append({"Hypothesis": "Telemetry missing or stale", "Evidence": ["Telemetry too old/unavailable", "Markers Grey"], "Confidence": "High"})
    if lookup["Equipment health"]["RAG"] == "Red":
        hyps.append({"Hypothesis": "Equipment replacement needed", "Evidence": ["Suspected equipment fault", "Issue repeated"], "Confidence": "High"})
    if lookup["Line health"]["RAG"] == "Red":
        hyps.append({"Hypothesis": "Engineer visit needed", "Evidence": ["Line health failed", "Symptoms severe"], "Confidence": "High"})
    if lookup["WiFi signal strength"]["RAG"] in ["Amber", "Red"]:
        hyps.append({"Hypothesis": "Poor WiFi signal or placement", "Evidence": [f"WiFi signal flagged {lookup['WiFi signal strength']['RAG']}", f"Connection method {t['connection_method']}"], "Confidence": "Medium"})
    if lookup["Packet loss"]["RAG"] == "Red" and lookup["Retransmission rate"]["RAG"] in ["Amber", "Red"]:
        hyps.append({"Hypothesis": "WiFi interference or congestion", "Evidence": ["Packet loss Red", f"Retransmission rate {lookup['Retransmission rate']['RAG']}"], "Confidence": "Medium"})
    if lookup["Rapid reconnects"]["RAG"] in ["Amber", "Red"]:
        hyps.append({"Hypothesis": "Intermittent connectivity instability", "Evidence": [f"Rapid reconnects {lookup['Rapid reconnects']['RAG']}"], "Confidence": "Medium"})
    if not hyps:
        hyps.append({"Hypothesis": "Connection healthy", "Evidence": ["No Red markers", "Telemetry fresh", "Line health OK"], "Confidence": "High"})
    return hyps

def choose_best_hypothesis(hyps):
    rank = {"High": 3, "Medium": 2, "Low": 1}
    return sorted(hyps, key=lambda x: rank.get(x["Confidence"], 0), reverse=True)[0]

def decide_action(t, chosen, overall_rag):
    h = chosen["Hypothesis"]
    if t["known_outage"]:
        return {"Outcome": "Known outage detected", "Action": "No action needed.", "Customer_message": "Known service issue; no action required.", "Advisor_message": "Known outage; no escalation.", "Agentic_level": "Suppress troubleshooting", "Risk": "Low"}
    if "Telemetry missing or stale" in h:
        return {"Outcome": "Test incomplete", "Action": "Retry test; escalate if persists.", "Customer_message": "Telemetry missing or outdated.", "Advisor_message": "Telemetry stale; no firm diagnosis.", "Agentic_level": "Retry", "Risk": "Low"}
    if "Equipment replacement needed" in h:
        return {"Outcome": "Replacement recommended", "Action": "Offer replacement equipment.", "Customer_message": "Suspected faulty equipment; replacement advised.", "Advisor_message": "Equipment fault suspected.", "Agentic_level": "Recommend replacement", "Risk": "Medium"}
    if "Engineer visit needed" in h:
        return {"Outcome": "Engineer visit required", "Action": "Schedule engineer visit.", "Customer_message": "Issue requires engineer support.", "Advisor_message": "Escalate to engineer.", "Agentic_level": "Escalate", "Risk": "Medium"}
    if "Poor WiFi signal" in h:
        step = "Move closer to the hub or WiFi booster, then retest."
        adv_note = "Recommend device relocation or WiFi improvements."
        return {"Outcome": "Weak WiFi signal", "Action": step, "Customer_message": f"Weak WiFi detected. {step}", "Advisor_message": adv_note, "Agentic_level": "Recommend fix", "Risk": "Low"}
    if "WiFi interference or congestion" in h:
        return {"Outcome": "WiFi interference detected", "Action": "Optimize WiFi and retest.", "Customer_message": "WiFi interference detected; optimize setup.", "Advisor_message": "Suggest WiFi optimization.", "Agentic_level": "Recommend optimization", "Risk": "Low"}
    if "Intermittent connectivity instability" in h:
        return {"Outcome": "Unstable connection detected", "Action": "Monitor and retest; escalate if persists.", "Customer_message": "Connection unstable; please retest.", "Advisor_message": "Advise monitoring repeat issues.", "Agentic_level": "Monitor", "Risk": "Medium"}
    return {"Outcome": "No issue found","Action": "No action needed.","Customer_message": "Connection is healthy.","Advisor_message": "No fault detected.","Agentic_level": "Explain","Risk": "Low"}

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

# --- Session initialization ---
if "result" not in st.session_state:
    st.session_state.result = None
if "telemetry" not in st.session_state:
    st.session_state.telemetry = None
if "scenario_used" not in st.session_state:
    st.session_state.scenario_used = None

# --- App UI ---
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
    cols[1].metric("Outcome", action["Outcome"])
    cols[2].metric("Confidence", result["chosen"]["Confidence"])
    cols[3].metric("Risk", action["Risk"])
    cols[4].metric("Next Step Type", action["Agentic_level"])

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
            {"Field": "Retransmission Rate", "Value": safe_value(telemetry["retransmission_rate"], "%"), "Description": "Retransmissions"},
            {"Field": "Rapid Reconnects", "Value": safe_value(telemetry["rapid_reconnects"]), "Description": "Fast reconnect events"},
            {"Field": "Telemetry Age", "Value": f"{telemetry['telemetry_age_minutes']} minutes", "Description": "Telemetry age"},
            {"Field": "Line Health", "Value": telemetry["line_health"], "Description": "Line status"},
            {"Field": "Known Outage", "Value": "Yes" if telemetry["known_outage"] else "No", "Description": "Known outages"},
            {"Field": "Equipment Health", "Value": telemetry["equipment_health"], "Description": "Equipment condition"},
            {"Field": "Customer Symptom", "Value": telemetry["customer_symptom"], "Description": "Customer reported symptom"},
            {"Field": "Customer Impact Score", "Value": f"{telemetry['customer_impact_score']}/10", "Description": "Severity rating"},
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
        st.header("Advisor View — Summary")
        advisor_summary = {
            "Field": ["Outcome", "Recommended Action", "Chosen Hypothesis", "Confidence Level", "Risk Level"],
            "Value": [
                action["Outcome"],
                action["Action"],
                result["chosen"]["Hypothesis"],
                result["chosen"]["Confidence"],
                action["Risk"]
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
            "Weak WiFi signal": "Try moving your device closer to your router or WiFi booster.",
            "WiFi interference detected": "Optimize your WiFi setup by reducing interference or changing channels.",
            "Unstable connection detected": "Monitor your connection and retest. Contact support if problems persist.",
            "Engineer visit required": "An engineer visit is recommended to resolve your issue.",
            "Replacement recommended": "We recommend you arrange a replacement for faulty equipment.",
            "Known outage detected": "There is a known service outage. Please wait for resolution updates.",
            "Test incomplete": "The test could not complete. Please try again or contact support.",
            "No issue found": "Your connection is healthy. No further action needed."
        }
        advice = advice_map.get(action["Outcome"], action["Customer_message"])
        st.success(advice)
        st.markdown(f"**Next step:** {action['Action']}")

else:
    st.info("Click 'Test my connection' to start.")


