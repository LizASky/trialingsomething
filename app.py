import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# ==== Synthetic Scenarios ====

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

# ==== Helpers: RAG Calculations ====

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

# ==== Build marker results and overall RAG

def build_marker_results(t):
    res = []
    rssi_rag, rssi_reason = calculate_rssi_rag(t["rssi"])
    res.append({"Marker":"WiFi signal strength","Value":safe_value(t["rssi"]," dBm"),"RAG":rssi_rag,"Reason":rssi_reason})
    packet_rag, packet_reason = calculate_packet_loss_rag(t["packet_loss"])
    res.append({"Marker":"Packet loss","Value":safe_value(t["packet_loss"],"%"),"RAG":packet_rag,"Reason":packet_reason})
    retrans_rag, retrans_reason = calculate_retransmission_rag(t["retransmission_rate"])
    res.append({"Marker":"Retransmission rate","Value":safe_value(t["retransmission_rate"],"%"),"RAG":retrans_rag,"Reason":retrans_reason})
    reconnect_rag, reconnect_reason = calculate_reconnect_rag(t["rapid_reconnects"])
    res.append({"Marker":"Rapid reconnects","Value":safe_value(t["rapid_reconnects"]),"RAG":reconnect_rag,"Reason":reconnect_reason})
    line_rag, line_reason = calculate_line_health_rag(t["line_health"])
    res.append({"Marker":"Line health","Value":t["line_health"],"RAG":line_rag,"Reason":line_reason})
    age_rag, age_reason = calculate_telemetry_age_rag(t["telemetry_age_minutes"])
    res.append({"Marker":"Telemetry freshness","Value":f"{t['telemetry_age_minutes']} minutes old","RAG":age_rag,"Reason":age_reason})
    equipment_rag, equipment_reason = calculate_equipment_health_rag(t["equipment_health"])
    res.append({"Marker":"Equipment health","Value":t["equipment_health"],"RAG":equipment_rag,"Reason":equipment_reason})
    return res

def rollup_rag(marker_results):
    rags = [m["RAG"] for m in marker_results]
    if "Grey" in rags:
        return "Grey"
    if "Red" in rags:
        return "Red"
    if "Amber" in rags:
        return "Amber"
    return "Green"

# ==== Hypotheses generation, choosing, action decision ====

def build_hypotheses(t, markers):
    lookup = {m["Marker"]:m for m in markers}
    hyps = []
    if t["known_outage"]:
        hyps.append({"Hypothesis":"Known wider service issue","Evidence":["Known outage active","Stop normal troubleshooting","No engineer/replacement"],"Confidence":"High"})
        return hyps
    if lookup["Telemetry freshness"]["RAG"]=="Grey":
        hyps.append({"Hypothesis":"Telemetry missing or stale","Evidence":["Telemetry too old or unavailable","Markers contain Grey"],"Confidence":"High"})
    if lookup["Equipment health"]["RAG"]=="Red":
        hyps.append({"Hypothesis":"Equipment replacement needed","Evidence":["Suspected equipment fault","Issue repeated"],"Confidence":"High"})
    if lookup["Line health"]["RAG"]=="Red":
        hyps.append({"Hypothesis":"Engineer visit needed","Evidence":["Line health failed","Symptoms severe"],"Confidence":"High"})
    if lookup["WiFi signal strength"]["RAG"] in ["Amber","Red"]:
        hyps.append({"Hypothesis":"Poor WiFi signal or placement","Evidence":[f"WiFi signal is {lookup['WiFi signal strength']['RAG']}","Connection method "+t["connection_method"]],"Confidence":"Medium"})
    if lookup["Packet loss"]["RAG"]=="Red" and lookup["Retransmission rate"]["RAG"] in ["Amber","Red"]:
        hyps.append({"Hypothesis":"WiFi interference or congestion","Evidence":["Packet loss Red","Retransmission rate Amber/Red"],"Confidence":"Medium"})
    if lookup["Rapid reconnects"]["RAG"] in ["Amber","Red"]:
        hyps.append({"Hypothesis":"Intermittent connectivity","Evidence":[f"Rapid reconnects {lookup['Rapid reconnects']['RAG']}"],"Confidence":"Medium"})
    if not hyps:
        hyps.append({"Hypothesis":"Connection appears healthy","Evidence":["No Red markers","Telemetry fresh","Line health OK"],"Confidence":"High"})
    return hyps

def choose_best_hypothesis(hypotheses):
    ranking = {"High":3,"Medium":2,"Low":1}
    return sorted(hypotheses,key=lambda x:ranking.get(x["Confidence"],0),reverse=True)[0]

def decide_action(t, chosen, overall_rag):
    h = chosen["Hypothesis"]
    if t["known_outage"]:
        return {"Outcome":"Known outage detected","Action":"No action needed; issue being fixed.","Customer_message":"Known service issue; please wait.","Advisor_message":"Known outage suppress troubleshooting.","Agentic_level":"Suppress troubleshooting","Risk":"Low"}
    if "Telemetry missing or stale" in h:
        return {"Outcome":"Test incomplete","Action":"Retry test; escalate if repeated.","Customer_message":"Telemetry missing or outdated.","Advisor_message":"No firm diagnosis; telemetry stale.","Agentic_level":"Retry","Risk":"Low"}
    if "Equipment replacement needed" in h:
        return {"Outcome":"Replacement recommended","Action":"Offer replacement equipment.","Customer_message":"Equipment fault suspected; replacement advised.","Advisor_message":"Suspected equipment fault.","Agentic_level":"Recommend replacement","Risk":"Medium"}
    if "Engineer visit needed" in h:
        return {"Outcome":"Engineer visit required","Action":"Schedule engineer visit.","Customer_message":"Issue needs engineer attention.","Advisor_message":"Escalate to engineer.","Agentic_level":"Escalate","Risk":"Medium"}
    if "Poor WiFi signal" in h:
        if t["pod_present"]:
            step="Move closer to hub/pod then retest."
            note="Pod present; recommend placement adjustment."
        else:
            step="Move closer to hub or add booster, then retest."
            note="No pod; recommend in-home WiFi improvements."
        return {"Outcome":"Weak WiFi signal","Action":step,"Customer_message":f"Weak WiFi signal detected. {step}","Advisor_message":note,"Agentic_level":"Recommend fix","Risk":"Low"}
    if "WiFi interference or congestion" in h:
        return {"Outcome":"WiFi interference detected","Action":"Optimize WiFi and retest.","Customer_message":"Interference detected; optimize WiFi.","Advisor_message":"Warn about congestion/interference.","Agentic_level":"Recommend optimization","Risk":"Low"}
    if "Intermittent connectivity" in h:
        return {"Outcome":"Unstable connection detected","Action":"Monitor and retest; escalate if persists.","Customer_message":"Connection unstable; please retest.","Advisor_message":"Monitor repeat history for route.","Agentic_level":"Monitor","Risk":"Medium"}
    return {"Outcome":"No issue found","Action":"No action needed now.","Customer_message":"Connection looks healthy.","Advisor_message":"No fault detected.","Agentic_level":"Explain","Risk":"Low"}

# ==== Randomise telemetry for demo ====

def randomise_scenario(base):
    t = base.copy()
    if t["rssi"] is not None:
        t["rssi"] = max(-95,min(-30,t["rssi"]+random.randint(-6,6)))
    if t["packet_loss"] is not None:
        t["packet_loss"] = round(max(0,min(20,t["packet_loss"]+random.uniform(-1.8,1.8))),1)
    if t["retransmission_rate"] is not None:
        t["retransmission_rate"] = max(0,min(50,t["retransmission_rate"]+random.randint(-5,5)))
    if t["rapid_reconnects"] is not None:
        t["rapid_reconnects"] = max(0,min(20,t["rapid_reconnects"]+random.randint(-2,2)))
    t["telemetry_age_minutes"] = max(1,min(600,t["telemetry_age_minutes"]+random.randint(-8,8)))
    return t

# ==== Synthetic history for trend chart ====

def generate_synthetic_history(scenario_key):
    base = SCENARIOS[scenario_key]
    history = []
    now = datetime.now()
    for i in range(10):
        timestamp = now - timedelta(hours=10-i)
        def jitter(val, low, high, scale=3):
            if val is None:
                return None
            v = val + random.uniform(-scale, scale)
            return max(low, min(high, v))
        history.append({
            "timestamp": timestamp,
            "rssi": jitter(base["rssi"],-95,-30),
            "packet_loss": jitter(base["packet_loss"],0,20),
            "retransmission_rate": jitter(base["retransmission_rate"],0,50),
            "rapid_reconnects": max(0,int(base["rapid_reconnects"]+random.randint(-1,1)))
        })
    return history

def plot_trends(history):
    df = pd.DataFrame(history).set_index("timestamp")[["rssi","packet_loss","retransmission_rate","rapid_reconnects"]]
    st.line_chart(df)
    return df

def summarize_trends(df):
    summaries = []
    if df["rssi"].iloc[-1]<df["rssi"].iloc[0]:
        summaries.append("WiFi signal strength has decreased over time.")
    else:
        summaries.append("WiFi signal strength is stable or improved.")
    if df["packet_loss"].iloc[-1]>df["packet_loss"].iloc[0]:
        summaries.append("Packet loss has increased, possibly impacting quality.")
    else:
        summaries.append("Packet loss is stable or improved.")
    if df["retransmission_rate"].iloc[-1]>df["retransmission_rate"].iloc[0]:
        summaries.append("Retransmission rate has increased, indicating rising errors.")
    else:
        summaries.append("Retransmission rate is stable or improved.")
    if df["rapid_reconnects"].iloc[-1]>df["rapid_reconnects"].iloc[0]:
        summaries.append("Rapid reconnects are more frequent, showing instability.")
    else:
        summaries.append("Rapid reconnects stable or decreased.")
    return " ".join(summaries)

# ==== Customer and advisor messages ====

def build_detailed_customer_message(t, marker_results, action):
    lookup = {m["Marker"]:m for m in marker_results}
    lines = []
    if lookup["WiFi signal strength"]["RAG"] in ["Amber","Red"]:
        lines.append(f"WiFi signal strength is {safe_value(t['rssi'],' dBm')} and may cause issues.")
    if lookup["Packet loss"]["RAG"] in ["Amber","Red"]:
        lines.append(f"Packet loss of {safe_value(t['packet_loss'],'%')} detected, may degrade performance.")
    lines.append(action["Customer_message"])
    return " ".join(lines)

def build_detailed_advisor_message(t, marker_results, action, hypotheses):
    lines = []
    for mr in marker_results:
        lines.append(f"{mr['Marker']} ({mr['Value']}): {mr['Reason']} - {mr['RAG']}")
    lines.append("Hypotheses:")
    for h in hypotheses:
        lines.append(f"- {h['Hypothesis']} (Confidence: {h['Confidence']})")
    lines.append(f"Recommended action: {action['Action']}")
    return "\n".join(lines)

# ==== Main test runner ====

def run_agentic_test(t, scenario_key):
    markers = build_marker_results(t)
    overall = rollup_rag(markers)
    hyps = build_hypotheses(t, markers)
    chosen = choose_best_hypothesis(hyps)
    action = decide_action(t, chosen, overall)
    cust_msg = build_detailed_customer_message(t, markers, action)
    adv_msg = build_detailed_advisor_message(t, markers, action, hyps)
    diag_text = f"Chosen hypothesis: {chosen['Hypothesis']} (Confidence: {chosen['Confidence']})\nAction: {action['Action']}"
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

# ==== Streamlit UI =====

if "result" not in st.session_state:
    st.session_state.result = None
if "telemetry" not in st.session_state:
    st.session_state.telemetry = None
if "scenario_used" not in st.session_state:
    st.session_state.scenario_used = None

st.title("🛰️ Test SC Enhanced Agentic AI Demo")

random_mode = st.sidebar.checkbox("Random scenario every run", True)
selected_scenario = st.sidebar.selectbox("Or choose specific scenario:", list(SCENARIOS.keys()))

st.markdown("## Check your connection")
if st.button("🚀 Test my connection"):
    scenario = random.choice(list(SCENARIOS.keys())) if random_mode else selected_scenario
    st.session_state.scenario_used = scenario
    telem = randomise_scenario(SCENARIOS[scenario])
    st.session_state.telemetry = telem
    st.session_state.result = run_agentic_test(telem, scenario)

if st.session_state.result:
    res = st.session_state.result
    action = res["action"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall status", rag_badge(res["overall_rag"]))
    col2.metric("Outcome", action["Outcome"])
    col3.metric("Confidence", res["chosen"]["Confidence"])
    col4.metric("Next step type", action["Agentic_level"])

    st.subheader("Customer message")
    st.success(res["detailed_customer_message"])

    st.subheader("Recommended next step")
    st.write(action["Action"])

    st.subheader("Connection metrics trend")
    df_hist = plot_trends(res["history"])
    st.info(summarize_trends(df_hist))

    st.subheader("Telemetry details")
    telem_df = pd.DataFrame([
        {"Field": "Product", "Value": st.session_state.telemetry["product"]},
        {"Field": "Device type", "Value": st.session_state.telemetry["device_type"]},
        {"Field": "Connection method", "Value": st.session_state.telemetry["connection_method"]},
        {"Field": "RSSI", "Value": safe_value(st.session_state.telemetry["rssi"], " dBm")},
        {"Field": "Packet loss", "Value": safe_value(st.session_state.telemetry["packet_loss"], "%")},
        {"Field": "Retransmission rate", "Value": safe_value(st.session_state.telemetry["retransmission_rate"], "%")},
        {"Field": "Rapid reconnects", "Value": safe_value(st.session_state.telemetry["rapid_reconnects"])},
        {"Field": "Telemetry age", "Value": f"{st.session_state.telemetry['telemetry_age_minutes']} minutes"},
        {"Field": "Line health", "Value": st.session_state.telemetry["line_health"]},
        {"Field": "Known outage", "Value": "Yes" if st.session_state.telemetry["known_outage"] else "No"},
        {"Field": "Equipment health", "Value": st.session_state.telemetry["equipment_health"]},
        {"Field": "Customer symptom", "Value": st.session_state.telemetry["customer_symptom"]},
        {"Field": "Customer impact score", "Value": f"{st.session_state.telemetry['customer_impact_score']}/10"},
    ])
    st.dataframe(telem_df, use_container_width=True)

    st.subheader("Marker results")
    marker_df = pd.DataFrame(res["marker_results"])
    marker_df["RAG"] = marker_df["RAG"].apply(rag_badge)
    st.dataframe(marker_df, use_container_width=True)

    st.subheader("Diagnostic reasoning narrative")
    st.text_area("Reasoning", res["diagnostic_trace_text"], height=240, disabled=True)

else:
    st.info("Click above to run a synthetic connection test.")

