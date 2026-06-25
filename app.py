import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# --- Synthetic telemetry generator ---
def generate_random_telemetry():
    products = ["Streaming TV", "Broadband", "Phone"]
    devices = ["Streaming device", "Laptop", "Mobile", "Hub"]
    connections = ["5GHz WiFi", "2.4GHz WiFi", "Ethernet"]

    conn = random.choice(connections)
    telemetry = {
        "product": random.choice(products),
        "device_type": random.choice(devices),
        "connection_method": conn,
        "rssi": random.randint(-95, -40) if conn != "Ethernet" else None,
        "packet_loss": round(random.uniform(0, 15), 1),
        "retransmission_rate": round(random.uniform(0, 30), 1),
        "rapid_reconnects": random.randint(0, 10),
        "telemetry_age_minutes": random.randint(1, 180),
        "line_health": random.choices(["OK", "Unstable", "Fail"], [0.7, 0.2, 0.1])[0],
        "known_outage": random.choices([False, True], [0.9, 0.1])[0],
        "repeat_issue_7_days": random.choice([False, True]),
        "previous_outcome": random.choice(["No previous journey", "Self-serve guidance shown", "Issue repeated"]),
        "hub_model": random.choice(["Hub 4", "Hub 5", "Hub 6"]),
        "pod_present": random.choice([False, True]),
        "customer_symptom": random.choice(["No issue reported", "Buffering or poor picture quality", "Slow broadband speed", "Connection drops"]),
        "customer_impact_score": random.randint(1, 10),
        "equipment_health": random.choices(["OK", "Suspected fault"], [0.85, 0.15])[0]
    }
    return telemetry

def safe_value(value, suffix=""):
    return "Not available" if value is None else f"{value}{suffix}"

def rag_badge(rag):
    return {"Green":"🟢 Green","Amber":"🟠 Amber","Red":"🔴 Red","Grey":"⚪ Grey"}.get(rag, rag)

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

def calculate_reconnect_rag(reconnects):
    if reconnects is None:
        return "Grey", "Reconnect telemetry unavailable"
    if reconnects <= 1:
        return "Green", "Reconnect behaviour stable"
    elif reconnects <= 4:
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
    elif age <= 120:
        return "Amber", "Telemetry is slightly old"
    else:
        return "Grey", "Telemetry too old for confident diagnosis"

def calculate_equipment_health_rag(health):
    if health == "OK":
        return "Green", "No equipment faults suspected"
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

def build_hypotheses(t, marker_results):
    lookup = {m["Marker"]: m for m in marker_results}
    hyps = []
    if t["known_outage"]:
        hyps.append({"Hypothesis": "Known service outage", "Evidence": ["Service outage active"], "Confidence": "High"})
        return hyps
    if lookup["Telemetry freshness"]["RAG"] == "Grey":
        hyps.append({"Hypothesis": "Telemetry missing or stale", "Evidence": ["Telemetry too old or missing"], "Confidence": "High"})
    if lookup["Equipment health"]["RAG"] == "Red":
        hyps.append({"Hypothesis": "Equipment fault suspected", "Evidence": ["Equipment flagged faulty"], "Confidence": "High"})
    if lookup["Line health"]["RAG"] == "Red":
        hyps.append({"Hypothesis": "Line failure", "Evidence": ["Line health failed"], "Confidence": "High"})
    if lookup["WiFi signal strength"]["RAG"] in ["Amber", "Red"]:
        hyps.append({"Hypothesis": "Poor WiFi signal or placement", "Evidence": ["WiFi signal degraded"], "Confidence": "Medium"})
    if lookup["Packet loss"]["RAG"] == "Red" and lookup["Retransmission rate"]["RAG"] in ["Amber", "Red"]:
        hyps.append({"Hypothesis": "WiFi interference or congestion", "Evidence": ["Elevated packet loss and retransmission"], "Confidence": "Medium"})
    if lookup["Rapid reconnects"]["RAG"] in ["Amber", "Red"]:
        hyps.append({"Hypothesis": "Connection instability", "Evidence": ["Frequent rapid reconnects"], "Confidence": "Medium"})
    if not hyps:
        hyps.append({"Hypothesis": "Connection healthy", "Evidence": ["No red markers detected"], "Confidence": "High"})
    return hyps

def choose_best_hypothesis(hypotheses):
    ranking = {"High": 3, "Medium": 2, "Low": 1}
    return sorted(hypotheses, key=lambda h: ranking.get(h["Confidence"], 0), reverse=True)[0]

def decide_action(t, chosen, overall_rag):
    h = chosen["Hypothesis"]
    if t["known_outage"]:
        return {"Outcome": "Known outage detected", "Action": "No action needed; issue being resolved.", "Customer_message": "Service outage ongoing.", "Advisor_message": "Known outage; no escalation.", "Agentic_level": "Suppress troubleshooting", "Risk": "Low"}
    if "Telemetry missing or stale" in h:
        return {"Outcome": "Test incomplete", "Action": "Retry test or escalate if persists.", "Customer_message": "Test incomplete due to missing telemetry.", "Advisor_message": "Telemetry stale or missing.", "Agentic_level": "Retry", "Risk": "Low"}
    if "Equipment fault suspected" in h:
        return {"Outcome": "Replacement recommended", "Action": "Equipment replacement advised.", "Customer_message": "Possible equipment fault detected.", "Advisor_message": "Device suspected faulty.", "Agentic_level": "Recommend replacement", "Risk": "Medium"}
    if "Line failure" in h:
        return {"Outcome": "Engineer visit required", "Action": "Schedule engineer visit.", "Customer_message": "Issue requires engineer.", "Advisor_message": "Line failed; escalate.", "Agentic_level": "Escalate", "Risk": "Medium"}
    if "Poor WiFi signal or placement" in h:
        return {"Outcome": "Weak WiFi signal", "Action": "Improve WiFi placement.", "Customer_message": "Weak WiFi signal detected; move closer to hub.", "Advisor_message": "Advise router proximity improvements.", "Agentic_level": "Recommend fix", "Risk": "Low"}
    if "WiFi interference or congestion" in h:
        return {"Outcome": "WiFi interference detected", "Action": "Optimize WiFi setup.", "Customer_message": "Possible WiFi interference.", "Advisor_message": "Packet loss and retransmission high.", "Agentic_level": "Recommend optimization", "Risk": "Low"}
    if "Connection instability" in h:
        return {"Outcome": "Unstable connection detected", "Action": "Monitor connection and retest.", "Customer_message": "Intermittent connection instability noticed.", "Advisor_message": "Escalate if persistent.", "Agentic_level": "Monitor", "Risk": "Medium"}
    return {"Outcome": "No issue found", "Action": "No action needed.", "Customer_message": "Connection appears healthy.", "Advisor_message": "No fault found.", "Agentic_level": "Explain", "Risk": "Low"}

def generate_synthetic_history(scenario_key):
    base = SCENARIOS[scenario_key]
    now = datetime.now()
    history = []
    for i in range(10):
        timestamp = now - timedelta(hours=10 - i)
        jitter = lambda v, low, high, scale=3: max(low, min(high, v + random.uniform(-scale, scale))) if v is not None else None
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
        summaries.append("Packet loss has increased.")
    else:
        summaries.append("Packet loss is stable or improved.")
    if df["retransmission_rate"].iloc[-1] > df["retransmission_rate"].iloc[0]:
        summaries.append("Retransmission rate has increased.")
    else:
        summaries.append("Retransmission rate is stable or improved.")
    if df["rapid_reconnects"].iloc[-1] > df["rapid_reconnects"].iloc[0]:
        summaries.append("Rapid reconnects have increased.")
    else:
        summaries.append("Rapid reconnects are stable or decreased.")
    return " ".join(summaries)

def build_detailed_customer_message(t, markers, action):
    lines = [f"{m['Marker']}: {m['Value']} — {m['Reason']}" for m in markers]
    lines.extend([
        "",
        f"Outcome: {action['Outcome']}",
        f"Recommended action: {action['Action']}",
        f"Advice: {action['Customer_message']}"
    ])
    return "\n".join(lines)

def build_detailed_advisor_message(t, markers, action, hypotheses):
    lines = ["Markers and telemetry details:"]
    for m in markers:
        lines.append(f"- {m['Marker']}: {m['Value']} (RAG: {m['RAG']})")
        lines.append(f"  Reason: {m['Reason']}")
    lines.append("\nHypotheses considered:")
    for h in hypotheses:
        lines.append(f"- {h['Hypothesis']} (Confidence: {h['Confidence']})")
        lines.extend([f"  • {e}" for e in h["Evidence"]])
    lines.extend([
        "",
        f"Final Outcome: {action['Outcome']}",
        f"Recommended Action: {action['Action']}",
        f"Advisor Notes: {action['Advisor_message']}",
        f"Risk Level: {action['Risk']}"
    ])
    return "\n".join(lines)

def run_agentic_test(t, scenario_key):
    markers = build_marker_results(t)
    overall_rag = rollup_rag(markers)
    hypotheses = build_hypotheses(t, markers)
    chosen = choose_best_hypothesis(hypotheses)
    action = decide_action(t, chosen, overall_rag)
    cust_msg = build_detailed_customer_message(t, markers, action)
    adv_msg = build_detailed_advisor_message(t, markers, action, hypotheses)
    diag_text = f"Chosen hypothesis: {chosen['Hypothesis']} (Confidence {chosen['Confidence']})\nAction taken: {action['Action']}"
    history = generate_synthetic_history(scenario_key)
    return {
        "marker_results": markers,
        "overall_rag": overall_rag,
        "hypotheses": hypotheses,
        "chosen": chosen,
        "action": action,
        "detailed_customer_message": cust_msg,
        "detailed_advisor_message": adv_msg,
        "diagnostic_trace_text": diag_text,
        "history": history
    }

# Streamlit app UI

if "result" not in st.session_state:
    st.session_state.result = None
if "telemetry" not in st.session_state:
    st.session_state.telemetry = None
if "scenario_used" not in st.session_state:
    st.session_state.scenario_used = None

st.title("🛰️ Test SC Agentic AI Demo")

random_mode = st.sidebar.checkbox("Random scenario every test",True)
selected_scenario = st.sidebar.selectbox("Or pick specific scenario", list(SCENARIOS.keys()))

if st.button("🚀 Test my connection"):
    if random_mode:
        scenario = random.choice(list(SCENARIOS.keys()))
    else:
        scenario = selected_scenario
    telemetry = generate_random_telemetry()
    st.session_state.telemetry = telemetry
    st.session_state.scenario_used = scenario
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
            {"Field": "Packet Loss", "Value": safe_value(telemetry["packet_loss"], "%"), "Meaning": "Percentage of lost data packets"},
            {"Field": "Retransmission Rate", "Value": safe_value(telemetry["retransmission_rate"], "%"), "Meaning": "Frequency of retransmissions"},
            {"Field": "Rapid Reconnects", "Value": safe_value(telemetry["rapid_reconnects"]), "Meaning": "Number of rapid reconnect events"},
            {"Field": "Telemetry Age", "Value": f"{telemetry['telemetry_age_minutes']} minutes", "Meaning": "Recency of telemetry data"},
            {"Field": "Line Health", "Value": telemetry["line_health"], "Meaning": "Broadband line health"},
            {"Field": "Known Outage", "Value": "Yes" if telemetry["known_outage"] else "No", "Meaning": "Known service outages"},
            {"Field": "Equipment Health", "Value": telemetry["equipment_health"], "Meaning": "Equipment condition"},
            {"Field": "Customer Symptom", "Value": telemetry["customer_symptom"], "Meaning": "Customer reported symptoms"},
            {"Field": "Customer Impact Score", "Value": f"{telemetry['customer_impact_score']}/10", "Meaning": "Severity of your connection problem"},
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
                action.get("Outcome"),
                action.get("Action"),
                result["chosen"].get("Hypothesis"),
                result["chosen"].get("Confidence"),
                action.get("Risk")
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


