import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# ----- Synthetic telemetry generator -----
def generate_synthetic_telemetry():
    products = ["Streaming TV", "Broadband", "Phone"]
    devices = ["Streaming device", "Laptop", "Mobile", "Hub"]
    connection_types = ["5GHz WiFi", "2.4GHz WiFi", "Ethernet"]

    product = random.choice(products)
    device = random.choice(devices)
    connection = random.choice(connection_types)

    telemetry = {
        "product": product,
        "device_type": device,
        "connection_method": connection,
        "rssi": random.randint(-90, -40) if connection != "Ethernet" else None,
        "packet_loss": round(random.uniform(0, 20), 1),
        "retransmission_rate": round(random.uniform(0, 40), 1),
        "rapid_reconnects": random.randint(0, 10),
        "telemetry_age_minutes": random.randint(1, 180),
        "line_health": random.choices(["OK", "Unstable", "Fail"], [0.7, 0.2, 0.1])[0],
        "known_outage": random.choice([False]*8 + [True]*2),
        "repeat_issue_7_days": random.choice([False]*7 + [True]*3),
        "previous_outcome": random.choice(["No previous journey", "Self-serve guidance", "Issue repeated"]),
        "hub_model": random.choice(["Hub 4", "Hub 5", "Hub 6"]),
        "pod_present": random.choice([False, True]),
        "customer_symptom": random.choice(["No issues", "Buffering or lag", "Slow speeds", "Connection drops"]),
        "customer_impact_score": random.randint(1, 10),
        "equipment_health": random.choices(["OK", "Suspected fault"], [0.85, 0.15])[0],
    }
    return telemetry

# ----- RAG Thresholds -----
def compute_rag(value, thresholds):
    if value is None:
        return "Grey"
    for color, (min_val, max_val) in thresholds.items():
        if min_val <= value <= max_val:
            return color
    return "Grey"

def calculate_rssi_rag(rssi):
    thresholds = {
        "Green": (-67, 100),
        "Amber": (-74, -68),
        "Red": (-100, -75)
    }
    rag = compute_rag(rssi, thresholds)
    reasons = {
        "Green": "WiFi signal strength looks healthy.",
        "Amber": "WiFi signal strength is fair but could be improved.",
        "Red": "WiFi signal strength is poor."
    }
    return rag, reasons.get(rag, "No data.")

def calculate_packet_loss_rag(pl):
    thresholds = {
        "Green": (0, 1),
        "Amber": (1.01, 3),
        "Red": (3.01, 100)
    }
    rag = compute_rag(pl, thresholds)
    reasons = {
        "Green": "Packet loss rate is low.",
        "Amber": "Packet loss rate is moderate.",
        "Red": "Packet loss rate is high."
    }
    return rag, reasons.get(rag, "No data.")

def calculate_retransmission_rag(rate):
    thresholds = {
        "Green": (0, 5),
        "Amber": (5.01, 15),
        "Red": (15.01, 100)
    }
    rag = compute_rag(rate, thresholds)
    reasons = {
        "Green": "Retransmission rate is low.",
        "Amber": "Retransmission rate is moderate.",
        "Red": "Retransmission rate is high."
    }
    return rag, reasons.get(rag, "No data.")

def calculate_reconnect_rag(reconnects):
    thresholds = {
        "Green": (0, 1),
        "Amber": (2, 4),
        "Red": (5, 100)
    }
    if reconnects is None:
        return "Grey", "Reconnect data unavailable."
    if reconnects <= 1:
        rag = "Green"
    elif reconnects <= 4:
        rag = "Amber"
    else:
        rag = "Red"
    reasons = {
        "Green": "Reconnect behavior is stable.",
        "Amber": "Some instability detected from reconnects.",
        "Red": "Frequent reconnect instability detected."
    }
    return rag, reasons.get(rag, "No data.")

def calculate_line_health_rag(status):
    stained_map = {"OK": ("Green", "Line health looks OK"),
                   "Unstable": ("Amber", "Line health appears unstable"),
                   "Fail": ("Red", "Line health has failed")}
    return stained_map.get(status, ("Grey", "Unknown line health status"))

def calculate_telemetry_age_rag(age):
    if age is None:
        return "Grey", "Telemetry age unknown."
    if age <= 30:
        return "Green", "Telemetry is fresh."
    elif age <= 120:
        return "Amber", "Telemetry is slightly old."
    else:
        return "Grey", "Telemetry too old for confident diagnosis."

def calculate_equipment_health_rag(health):
    stained_map = {"OK": ("Green", "Equipment is healthy"),
                   "Suspected fault": ("Red", "Equipment fault suspected")}
    return stained_map.get(health, ("Grey", "Unknown equipment health"))

def build_marker_results(t):
    results = []
    r, rr = calculate_rssi_rag(t["rssi"])
    results.append({"Marker":"WiFi signal strength","Value":safe_value(t["rssi"]," dBm"),"RAG":r,"Reason":rr})

    r, rr = calculate_packet_loss_rag(t["packet_loss"])
    results.append({"Marker":"Packet loss","Value":safe_value(t["packet_loss"],"%"),"RAG":r,"Reason":rr})

    r, rr = calculate_retransmission_rag(t["retransmission_rate"])
    results.append({"Marker":"Retransmission rate","Value":safe_value(t["retransmission_rate"],"%"),"RAG":r,"Reason":rr})

    r, rr = calculate_reconnect_rag(t["rapid_reconnects"])
    results.append({"Marker":"Rapid reconnects","Value":safe_value(t["rapid_reconnects"]),"RAG":r,"Reason":rr})

    r, rr = calculate_line_health_rag(t["line_health"])
    results.append({"Marker":"Line health","Value":t["line_health"],"RAG":r,"Reason":rr})

    r, rr = calculate_telemetry_age_rag(t["telemetry_age_minutes"])
    results.append({"Marker":"Telemetry freshness","Value":f"{t['telemetry_age_minutes']} minutes old","RAG":r,"Reason":rr})

    r, rr = calculate_equipment_health_rag(t["equipment_health"])
    results.append({"Marker":"Equipment health","Value":t["equipment_health"],"RAG":r,"Reason":rr})

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
    hypotheses = []
    if t["known_outage"]:
        hypotheses.append({"Hypothesis": "Known Service Outage", "Evidence": ["Known outage active"], "Confidence": "High"})
        return hypotheses
    if lookup["Telemetry freshness"]["RAG"] == "Grey":
        hypotheses.append({"Hypothesis": "Telemetry Missing or Stale", "Evidence": ["Telemetry too old or missing"], "Confidence": "High"})
    if lookup["Equipment health"]["RAG"] == "Red":
        hypotheses.append({"Hypothesis": "Equipment Fault Suspected", "Evidence": ["Equipment health flagged red"], "Confidence": "High"})
    if lookup["Line health"]["RAG"] == "Red":
        hypotheses.append({"Hypothesis": "Line Failure Detected", "Evidence": ["Line health failed"], "Confidence": "High"})
    if lookup["WiFi signal strength"]["RAG"] in ["Amber", "Red"]:
        hypotheses.append({"Hypothesis": "Poor WiFi Signal", "Evidence": [f"WiFi signal strength {lookup['WiFi signal strength']['RAG']}"], "Confidence": "Medium"})
    if (lookup["Packet loss"]["RAG"] == "Red" and
        lookup["Retransmission rate"]["RAG"] in ["Amber", "Red"]):
        hypotheses.append({"Hypothesis": "WiFi Interference or Congestion", "Evidence": ["High packet loss", "High retransmissions"], "Confidence": "Medium"})
    if lookup["Rapid reconnects"]["RAG"] in ["Amber", "Red"]:
        hypotheses.append({"Hypothesis": "Intermittent Connection Instability", "Evidence": ["Rapid reconnects elevated"], "Confidence": "Medium"})
    if not hypotheses:
        hypotheses.append({"Hypothesis": "Connection Healthy", "Evidence": ["No high severity markers detected"], "Confidence": "High"})
    return hypotheses

def choose_best_hypothesis(hypotheses):
    rank = {"High":3, "Medium":2, "Low":1}
    return sorted(hypotheses, key=lambda x: rank.get(x["Confidence"], 0), reverse=True)[0]

def decide_action(t, chosen, overall_rag):
    h = chosen["Hypothesis"]
    if t["known_outage"]:
        return {
            "Outcome": "Known outage detected",
            "Action": "No action needed; issue being resolved.",
            "Customer_message": "Known service outage affecting you.",
            "Advisor_message": "Known outage, no escalation needed.",
            "Agentic_level": "Suppress troubleshooting",
            "Risk": "Low"
        }
    if "Telemetry Missing or Stale" in h:
        return {
            "Outcome": "Test incomplete",
            "Action": "Retry test; escalate if persists.",
            "Customer_message": "Test incomplete due to telemetry issues.",
            "Advisor_message": "Telemetry stale or missing.",
            "Agentic_level": "Retry",
            "Risk": "Low"
        }
    if "Equipment Fault Suspected" in h:
        return {
            "Outcome": "Replacement recommended",
            "Action": "Offer replacement equipment.",
            "Customer_message": "Equipment fault suspected; replacement advised.",
            "Advisor_message": "Recommend replacement route.",
            "Agentic_level": "Recommend replacement",
            "Risk": "Medium"
        }
    if "Line Failure Detected" in h:
        return {
            "Outcome": "Engineer visit required",
            "Action": "Schedule engineer visit.",
            "Customer_message": "Issue requires engineer intervention.",
            "Advisor_message": "Escalate to engineering.",
            "Agentic_level": "Escalate",
            "Risk": "Medium"
        }
    if "Poor WiFi Signal" in h:
        return {
            "Outcome": "Weak WiFi signal",
            "Action": "Advise device placement or boosters.",
            "Customer_message": "Weak WiFi signal; move closer to router.",
            "Advisor_message": "Recommend WiFi fixes.",
            "Agentic_level": "Recommend fix",
            "Risk": "Low"
        }
    if "WiFi Interference or Congestion" in h:
        return {
            "Outcome": "WiFi interference detected",
            "Action": "Optimize WiFi and retest.",
            "Customer_message": "WiFi interference likely; optimize setup.",
            "Advisor_message": "Interference/congestion suspected.",
            "Agentic_level": "Recommend optimization",
            "Risk": "Low"
        }
    if "Intermittent Connection Instability" in h:
        return {
            "Outcome": "Unstable connection detected",
            "Action": "Monitor and retest; escalate if persists.",
            "Customer_message": "Connection unstable; retest and monitor.",
            "Advisor_message": "Instability requires follow-up.",
            "Agentic_level": "Monitor",
            "Risk": "Medium"
        }
    return {
        "Outcome": "No issue found",
        "Action": "No action needed now.",
        "Customer_message": "Connection appears healthy.",
        "Advisor_message": "No fault found.",
        "Agentic_level": "Explain",
        "Risk": "Low"
    }

# Streamlit app UI
if "result" not in st.session_state:
    st.session_state.result = None
if "telemetry" not in st.session_state:
    st.session_state.telemetry = None
if "scenario_used" not in st.session_state:
    st.session_state.scenario_used = None

st.title("🛰️ Synthetic Agentic AI Connection Test Demo")

random_mode = st.sidebar.checkbox("Random synthetic telemetry every test", True)
selected_scenario = st.sidebar.selectbox("Or select synthetic scenario", list(SCENARIOS.keys()))

if st.button("🚀 Test my connection"):
    telemetry = generate_synthetic_telemetry()
    st.session_state.telemetry = telemetry
    st.session_state.scenario_used = "Synthetic scenario"
    st.session_state.result = run_agentic_test(telemetry, st.session_state.scenario_used)

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

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Telemetry","Agentic Reasoning","Marker Results","Advisor View","Customer View"])

    with tab1:
        st.header("Synthetic Telemetry")
        telemetry_info = [
            {"Field": "Product", "Value": telemetry["product"], "Meaning": "Type of service being tested"},
            {"Field": "Device Type", "Value": telemetry["device_type"], "Meaning": "Device used"},
            {"Field": "Connection Method", "Value": telemetry["connection_method"], "Meaning": "How your device connects"},
            {"Field": "RSSI", "Value": safe_value(telemetry["rssi"], " dBm"), "Meaning": "WiFi signal strength"},
            {"Field": "Packet Loss", "Value": safe_value(telemetry["packet_loss"], "%"), "Meaning": "Lost packets %"},
            {"Field": "Retransmission Rate", "Value": safe_value(telemetry["retransmission_rate"], "%"), "Meaning": "Packet retransmissions %"},
            {"Field": "Rapid Reconnects", "Value": safe_value(telemetry["rapid_reconnects"]), "Meaning": "Fast reconnect events"},
            {"Field": "Telemetry Age", "Value": f"{telemetry['telemetry_age_minutes']} minutes", "Meaning": "Data freshness"},
            {"Field": "Line Health", "Value": telemetry["line_health"], "Meaning": "Broadband line status"},
            {"Field": "Known Outage", "Value": "Yes" if telemetry["known_outage"] else "No", "Meaning": "Active known outage"},
            {"Field": "Equipment Health", "Value": telemetry["equipment_health"], "Meaning": "Equipment condition"},
            {"Field": "Customer Symptom", "Value": telemetry["customer_symptom"], "Meaning": "Customer complaint"},
            {"Field": "Customer Impact Score", "Value": f"{telemetry['customer_impact_score']}/10", "Meaning": "Severity score"},
        ]
        st.table(pd.DataFrame(telemetry_info).set_index("Field"))

    with tab2:
        st.header("Agentic AI Reasoning")
        st.text_area("Diagnostic Narrative", result["diagnostic_trace_text"], height=250, disabled=True)
        hist_df = pd.DataFrame(result["history"]).set_index("timestamp")
        st.line_chart(hist_df[["rssi", "packet_loss", "retransmission_rate", "rapid_reconnects"]])
        st.info(summarize_trends(hist_df))

    with tab3:
        st.header("Marker Results")
        markers_df = pd.DataFrame(result["marker_results"])
        markers_df["RAG Status"] = markers_df["RAG"].apply(rag_badge)
        st.table(markers_df[["Marker", "Value", "RAG Status", "Reason"]])

    with tab4:
        st.header("Advisor View")
        summary = {
            "Field": ["Outcome", "Recommended Action", "Chosen Hypothesis", "Confidence", "Risk"],
            "Value": [action.get("Outcome"), action.get("Action"), result["chosen"].get("Hypothesis"), result["chosen"].get("Confidence"), action.get("Risk")]
        }
        st.table(pd.DataFrame(summary))
        st.subheader("Hypotheses & Evidence")
        for hyp in result["hypotheses"]:
            st.markdown(f"**{hyp['Hypothesis']}** (Confidence: {hyp['Confidence']})")
            st.write(", ".join(hyp["Evidence"]))
            st.markdown("---")

    with tab5:
        st.header("Customer View")
        customer_advice_map = {
            "Weak WiFi signal": "Try moving closer to your router or WiFi booster.",
            "WiFi interference detected": "Optimize your WiFi setup by reducing interference or changing channels.",
            "Unstable connection detected": "Monitor connection and rerun tests. Contact support if needed.",
            "Engineer visit required": "An engineer will visit to resolve your issue.",
            "Replacement recommended": "Replacement equipment is advised.",
            "Known outage detected": "There is a known outage; please wait for resolution.",
            "Test incomplete": "Test incomplete; please try again or contact support.",
            "No issue found": "Your connection looks healthy."
        }
        advice = customer_advice_map.get(action.get("Outcome"), action.get("Customer_message", ""))
        st.success(advice)
        st.markdown(f"**Next step:** {action.get('Action', 'No further action needed')}")
else:
    st.info("Click 'Test my connection' to start.")

