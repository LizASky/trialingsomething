import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime

# ============================================================
# TEST SC - AGENTIC CONNECTION TEST DEMO
# Synthetic telemetry only
# Demo thresholds only
# No real customer data
# No real production logic
# ============================================================

st.set_page_config(
    page_title="Test SC",
    page_icon="🛰️",
    layout="wide"
)

# ============================================================
# DEMO DATA
# ============================================================

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
        "customer_impact_score": 1
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
        "customer_impact_score": 7
    },
    "Slow WiFi / congestion": {
        "product": "Broadband / WiFi",
        "device_type": "Laptop or mobile",
        "connection_method": "5GHz WiFi",
        "rssi": -64,
        "packet_loss": 6.4,
        "retransmission_rate": 31,
        "rapid_reconnects": 2,
        "telemetry_age_minutes": 18,
        "line_health": "OK",
        "known_outage": False,
        "repeat_issue_7_days": True,
        "previous_outcome": "Customer abandoned journey",
        "hub_model": "Hub 6",
        "pod_present": False,
        "customer_symptom": "Slow broadband speed",
        "customer_impact_score": 8
    },
    "Connection dropping": {
        "product": "Broadband",
        "device_type": "Hub",
        "connection_method": "Ethernet",
        "rssi": None,
        "packet_loss": 8.7,
        "retransmission_rate": 5,
        "rapid_reconnects": 0,
        "telemetry_age_minutes": 10,
        "line_health": "Fail",
        "known_outage": False,
        "repeat_issue_7_days": True,
        "previous_outcome": "Advisor reviewed",
        "hub_model": "Hub 6",
        "pod_present": False,
        "customer_symptom": "Connection drops",
        "customer_impact_score": 9
    },
    "Known outage": {
        "product": "Broadband",
        "device_type": "Hub",
        "connection_method": "Ethernet",
        "rssi": None,
        "packet_loss": 12.2,
        "retransmission_rate": 8,
        "rapid_reconnects": 2,
        "telemetry_age_minutes": 9,
        "line_health": "Fail",
        "known_outage": True,
        "repeat_issue_7_days": False,
        "previous_outcome": "Known outage message shown",
        "hub_model": "Hub 6",
        "pod_present": False,
        "customer_symptom": "No broadband connection",
        "customer_impact_score": 10
    },
    "Telemetry unavailable": {
        "product": "Streaming TV",
        "device_type": "Unknown",
        "connection_method": "Unknown",
        "rssi": None,
        "packet_loss": None,
        "retransmission_rate": None,
        "rapid_reconnects": None,
        "telemetry_age_minutes": 430,
        "line_health": "Unknown",
        "known_outage": False,
        "repeat_issue_7_days": False,
        "previous_outcome": "Telemetry unavailable",
        "hub_model": "Unknown",
        "pod_present": False,
        "customer_symptom": "Service check failed",
        "customer_impact_score": 5
    }
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

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
        return "Grey", "RSSI telemetry unavailable"

    if rssi >= -67:
        return "Green", "Signal strength looks healthy"
    elif -75 <= rssi < -67:
        return "Amber", "Signal strength is degraded"
    else:
        return "Red", "Signal strength is poor"


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
        return "Green", "Line health check is OK"
    if line_health == "Unstable":
        return "Amber", "Line health appears unstable"
    if line_health == "Fail":
        return "Red", "Line health check failed"
    return "Grey", "Line health is unknown"


def calculate_telemetry_age_rag(age):
    if age is None:
        return "Grey", "Telemetry timestamp unavailable"

    if age <= 30:
        return "Green", "Telemetry is fresh"
    elif age <= 120:
        return "Amber", "Telemetry is slightly old"
    else:
        return "Grey", "Telemetry is too old to support confident diagnosis"


def build_marker_results(t):
    results = []

    rssi_rag, rssi_reason = calculate_rssi_rag(t["rssi"])
    results.append({
        "Marker": "WiFi signal strength",
        "Value": safe_value(t["rssi"], " dBm"),
        "RAG": rssi_rag,
        "Reason": rssi_reason
    })

    packet_rag, packet_reason = calculate_packet_loss_rag(t["packet_loss"])
    results.append({
        "Marker": "Packet loss",
        "Value": safe_value(t["packet_loss"], "%"),
        "RAG": packet_rag,
        "Reason": packet_reason
    })

    retrans_rag, retrans_reason = calculate_retransmission_rag(t["retransmission_rate"])
    results.append({
        "Marker": "Retransmission rate",
        "Value": safe_value(t["retransmission_rate"], "%"),
        "RAG": retrans_rag,
        "Reason": retrans_reason
    })

    reconnect_rag, reconnect_reason = calculate_reconnect_rag(t["rapid_reconnects"])
    results.append({
        "Marker": "Rapid reconnects",
        "Value": safe_value(t["rapid_reconnects"]),
        "RAG": reconnect_rag,
        "Reason": reconnect_reason
    })

    line_rag, line_reason = calculate_line_health_rag(t["line_health"])
    results.append({
        "Marker": "Line health",
        "Value": t["line_health"],
        "RAG": line_rag,
        "Reason": line_reason
    })

    age_rag, age_reason = calculate_telemetry_age_rag(t["telemetry_age_minutes"])
    results.append({
        "Marker": "Telemetry freshness",
        "Value": f"{t['telemetry_age_minutes']} minutes old",
        "RAG": age_rag,
        "Reason": age_reason
    })

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
            "Evidence": [
                "Known outage flag is active",
                "Normal troubleshooting should be suppressed"
            ],
            "Confidence": "High"
        })
        return hypotheses

    if lookup["Telemetry freshness"]["RAG"] == "Grey":
        hypotheses.append({
            "Hypothesis": "Insufficient evidence to diagnose confidently",
            "Evidence": [
                "Telemetry is stale or unavailable",
                "One or more markers are Grey"
            ],
            "Confidence": "High"
        })

    if lookup["Line health"]["RAG"] == "Red":
        hypotheses.append({
            "Hypothesis": "Potential line or network-side issue",
            "Evidence": [
                "Line health is Red",
                "Customer symptom indicates possible loss or instability"
            ],
            "Confidence": "High"
        })

    if lookup["WiFi signal strength"]["RAG"] in ["Amber", "Red"]:
        hypotheses.append({
            "Hypothesis": "Poor WiFi signal or poor device placement",
            "Evidence": [
                f"WiFi signal strength is {lookup['WiFi signal strength']['RAG']}",
                f"Connection method is {t['connection_method']}"
            ],
            "Confidence": "Medium"
        })

    if lookup["Packet loss"]["RAG"] == "Red" and lookup["Retransmission rate"]["RAG"] in ["Amber", "Red"]:
        hypotheses.append({
            "Hypothesis": "WiFi interference or congestion",
            "Evidence": [
                "Packet loss is Red",
                f"Retransmission rate is {lookup['Retransmission rate']['RAG']}"
            ],
            "Confidence": "Medium"
        })

    if lookup["Rapid reconnects"]["RAG"] in ["Amber", "Red"]:
        hypotheses.append({
            "Hypothesis": "Intermittent connectivity instability",
            "Evidence": [
                f"Rapid reconnects is {lookup['Rapid reconnects']['RAG']}"
            ],
            "Confidence": "Medium"
        })

    if not hypotheses:
        hypotheses.append({
            "Hypothesis": "Connection appears healthy based on synthetic telemetry",
            "Evidence": [
                "No Red markers detected",
                "Telemetry is fresh",
                "Line health is OK"
            ],
            "Confidence": "High"
        })

    return hypotheses


def choose_best_hypothesis(hypotheses):
    ranking = {
        "High": 3,
        "Medium": 2,
        "Low": 1
    }

    return sorted(
        hypotheses,
        key=lambda x: ranking.get(x["Confidence"], 0),
        reverse=True
    )[0]


def decide_action(t, chosen, overall_rag):
    h = chosen["Hypothesis"]

    if t["known_outage"]:
        return {
            "Outcome": "Known issue detected",
            "Action": "Show outage-aware messaging and stop normal troubleshooting.",
            "Customer_message": "We have detected a wider service issue. There is no need to continue standard troubleshooting at this stage.",
            "Advisor_message": "Normal journey suppressed because outage flag is active.",
            "Agentic_level": "Route / suppress",
            "Risk": "Low"
        }

    if "Insufficient evidence" in h:
        return {
            "Outcome": "Unable to complete a confident check",
            "Action": "Refresh telemetry or route to advisor review if the issue continues.",
            "Customer_message": "Some information needed for the check is missing or out of date. Please try the test again or continue with support.",
            "Advisor_message": "Telemetry is stale or incomplete. Avoid making a firm diagnosis from this run.",
            "Agentic_level": "Explain / gather evidence",
            "Risk": "Low"
        }

    if "line or network-side" in h:
        return {
            "Outcome": "Potential line issue",
            "Action": "Route to line-health investigation before suggesting in-home fixes.",
            "Customer_message": "The test found signs that the issue may not be limited to the home connection. The next step is to run a deeper line check.",
            "Advisor_message": "Line health is Red. Prioritise network or line path before WiFi optimisation.",
            "Agentic_level": "Escalate / route",
            "Risk": "Medium"
        }

    if "Poor WiFi signal" in h:
        return {
            "Outcome": "Poor WiFi signal detected",
            "Action": "Guide customer to improve device placement, check pod or hub distance, and re-test.",
            "Customer_message": "The test found signs of weak WiFi signal. Try moving the device closer to the hub or pod, then run the test again.",
            "Advisor_message": "WiFi signal is degraded. Recommend in-home placement optimisation before any engineer route.",
            "Agentic_level": "Recommend next best action",
            "Risk": "Low"
        }

    if "interference or congestion" in h:
        return {
            "Outcome": "Possible WiFi interference or congestion",
            "Action": "Recommend WiFi optimisation and re-test after change.",
            "Customer_message": "The test found signs of interference or congestion. The next step is to optimise the WiFi environment and re-test.",
            "Advisor_message": "Packet loss and retransmissions indicate likely congestion or interference.",
            "Agentic_level": "Recommend next best action",
            "Risk": "Low"
        }

    if "Intermittent connectivity" in h:
        return {
            "Outcome": "Intermittent connection detected",
            "Action": "Check recent reconnect pattern and re-test after a controlled interval.",
            "Customer_message": "The test found signs of the connection dropping and reconnecting. We recommend checking stability before choosing the next route.",
            "Advisor_message": "Reconnect pattern suggests instability. Review repeat history before closing journey.",
            "Agentic_level": "Recommend / monitor",
            "Risk": "Low"
        }

    return {
        "Outcome": "Connection looks healthy",
        "Action": "Reassure customer and monitor if symptoms continue.",
        "Customer_message": "The connection test did not find a major issue from the available synthetic telemetry.",
        "Advisor_message": "No major issue detected in this synthetic run.",
        "Agentic_level": "Explain / reassure",
        "Risk": "Low"
    }


def run_agentic_test(t):
    marker_results = build_marker_results(t)
    overall_rag = rollup_rag(marker_results)
    hypotheses = build_hypotheses(t, marker_results)
    chosen = choose_best_hypothesis(hypotheses)
    action = decide_action(t, chosen, overall_rag)

    return {
        "marker_results": marker_results,
        "overall_rag": overall_rag,
        "hypotheses": hypotheses,
        "chosen": chosen,
        "action": action
    }


def randomise_scenario(base):
    t = base.copy()

    # Add small controlled random variation each time the button is clicked
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


# ============================================================
# SESSION STATE
# ============================================================

if "run_complete" not in st.session_state:
    st.session_state.run_complete = False

if "result" not in st.session_state:
    st.session_state.result = None

if "telemetry" not in st.session_state:
    st.session_state.telemetry = None

if "audit_log" not in st.session_state:
    st.session_state.audit_log = []

if "scenario_used" not in st.session_state:
    st.session_state.scenario_used = None


# ============================================================
# PAGE HEADER
# ============================================================

st.title("🛰️ Test SC")
st.subheader("Test my connection")

st.warning(
    "Demo only: this uses synthetic telemetry and made-up thresholds. It does not use real customer data, real production logic, or internal system data."
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("Demo mode")

    random_mode = st.toggle(
        "Pick a different random scenario every time I test",
        value=True
    )

    selected_scenario = st.selectbox(
        "Or choose a specific scenario",
        list(SCENARIOS.keys())
    )

    st.caption(
        "If random mode is on, the app chooses a different synthetic scenario each time the button is clicked."
    )


# ============================================================
# LANDING / CUSTOMER JOURNEY
# ============================================================

st.markdown("## Check your connection")

st.write(
    "Click the button below to simulate a customer-style connection test. "
    "Test SC will collect synthetic telemetry, run an agentic diagnostic flow, and return an outcome."
)

left, centre, right = st.columns([1, 2, 1])

with centre:
    run_button = st.button("🚀 Test my connection", use_container_width=True)


# ============================================================
# RUN TEST
# ============================================================

if run_button:
    st.session_state.run_complete = False

    if random_mode:
        scenario_name = random.choice(list(SCENARIOS.keys()))
    else:
        scenario_name = selected_scenario

    base = SCENARIOS[scenario_name]
    telemetry = randomise_scenario(base)

    st.session_state.telemetry = telemetry
    st.session_state.scenario_used = scenario_name

    progress = st.progress(0)
    status = st.empty()

    steps = [
        "Starting connection test...",
        "Collecting synthetic telemetry...",
        "Checking telemetry freshness...",
        "Reading WiFi signal and packet loss markers...",
        "Checking line health and known outage status...",
        "Generating diagnostic hypotheses...",
        "Selecting next best action...",
        "Preparing customer and advisor outcome..."
    ]

    for index, step in enumerate(steps):
        status.info(step)
        progress.progress((index + 1) / len(steps))
        time.sleep(0.45)

    st.session_state.result = run_agentic_test(telemetry)
    st.session_state.run_complete = True
    status.success("Agentic diagnostic flow complete.")


# ============================================================
# BEFORE RUN MESSAGE
# ============================================================

if not st.session_state.run_complete:
    st.info("No connection test has been run yet. Click **Test my connection** to start.")
    st.stop()


# ============================================================
# RESULTS
# ============================================================

result = st.session_state.result
telemetry = st.session_state.telemetry
action = result["action"]

st.divider()

st.markdown("## Connection test outcome")

st.caption(f"Synthetic scenario used: {st.session_state.scenario_used}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Overall status", rag_badge(result["overall_rag"]))

with col2:
    st.metric("Outcome", action["Outcome"])

with col3:
    st.metric("Confidence", result["chosen"]["Confidence"])

with col4:
    st.metric("Agentic level", action["Agentic_level"])

if result["overall_rag"] == "Green":
    st.success(action["Customer_message"])
elif result["overall_rag"] == "Amber":
    st.warning(action["Customer_message"])
elif result["overall_rag"] == "Red":
    st.error(action["Customer_message"])
else:
    st.info(action["Customer_message"])

st.subheader("Recommended next step")
st.write(action["Action"])


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Customer outcome",
    "Agentic AI reasoning",
    "Telemetry used",
    "Marker results",
    "Advisor view",
    "Audit log"
])


# ============================================================
# CUSTOMER OUTCOME
# ============================================================

with tab1:
    st.header("Customer outcome")

    st.write(action["Customer_message"])

    st.subheader("What happens next")
    st.write(action["Action"])

    st.subheader("Plain English summary")
    st.write(
        f"The test looked at the synthetic connection data and selected **{action['Outcome']}** as the outcome."
    )


# ============================================================
# AGENTIC AI REASONING
# ============================================================

with tab2:
    st.header("Agentic AI reasoning")

    st.subheader("1. Observe")
    st.write(
        "The demo collects synthetic telemetry including WiFi signal, packet loss, retransmissions, reconnects, telemetry age, line health and known outage state."
    )

    st.subheader("2. Validate")
    if telemetry["known_outage"]:
        st.write("- Known outage flag is active.")
    if telemetry["telemetry_age_minutes"] > 120:
        st.write("- Telemetry is stale.")
    if telemetry["telemetry_age_minutes"] <= 120 and not telemetry["known_outage"]:
        st.write("- Telemetry is fresh enough for the demo to reason over.")

    st.subheader("3. Interpret")
    st.write("The demo converts telemetry into marker-level RAG outcomes.")

    st.subheader("4. Hypothesise")
    for h in result["hypotheses"]:
        with st.expander(f"{h['Hypothesis']} — confidence: {h['Confidence']}"):
            for evidence in h["Evidence"]:
                st.write(f"- {evidence}")

    st.subheader("5. Decide")
    st.write(f"Chosen hypothesis: **{result['chosen']['Hypothesis']}**")
    st.write(f"Chosen action: **{action['Action']}**")
    st.write(f"Risk: **{action['Risk']}**")

    st.subheader("6. Act")
    st.write(action["Action"])

    st.subheader("7. Explain")
    st.write(action["Customer_message"])

    st.subheader("8. Learn")
    st.write(
        "In a real governed version, this would create a learning record for SME review rather than changing logic automatically."
    )


# ============================================================
# TELEMETRY USED
# ============================================================

with tab3:
    st.header("Synthetic telemetry used")

    telemetry_df = pd.DataFrame([
        {"Field": "Product", "Value": telemetry["product"], "Meaning": "Service area being tested"},
        {"Field": "Device type", "Value": telemetry["device_type"], "Meaning": "Device involved in the test"},
        {"Field": "Connection method", "Value": telemetry["connection_method"], "Meaning": "How the device is connected"},
        {"Field": "RSSI", "Value": safe_value(telemetry["rssi"], " dBm"), "Meaning": "WiFi signal strength"},
        {"Field": "Packet loss", "Value": safe_value(telemetry["packet_loss"], "%"), "Meaning": "Dropped packet percentage"},
        {"Field": "Retransmission rate", "Value": safe_value(telemetry["retransmission_rate"], "%"), "Meaning": "How often data has to be resent"},
        {"Field": "Rapid reconnects", "Value": safe_value(telemetry["rapid_reconnects"]), "Meaning": "Fast disconnect/reconnect events"},
        {"Field": "Telemetry age", "Value": f"{telemetry['telemetry_age_minutes']} minutes", "Meaning": "How old the latest data is"},
        {"Field": "Line health", "Value": telemetry["line_health"], "Meaning": "Simplified line status"},
        {"Field": "Known outage", "Value": "Yes" if telemetry["known_outage"] else "No", "Meaning": "Whether normal troubleshooting should be suppressed"},
        {"Field": "Repeat issue 7 days", "Value": "Yes" if telemetry["repeat_issue_7_days"] else "No", "Meaning": "Whether the issue appears repeated"},
        {"Field": "Previous outcome", "Value": telemetry["previous_outcome"], "Meaning": "What happened on the previous journey"},
        {"Field": "Hub model", "Value": telemetry["hub_model"], "Meaning": "Synthetic hardware context"},
        {"Field": "Pod present", "Value": "Yes" if telemetry["pod_present"] else "No", "Meaning": "Whether a pod/booster exists in the home"},
        {"Field": "Customer symptom", "Value": telemetry["customer_symptom"], "Meaning": "What the customer reports"},
        {"Field": "Customer impact score", "Value": f"{telemetry['customer_impact_score']}/10", "Meaning": "Synthetic severity score"}
    ])

    st.dataframe(telemetry_df, use_container_width=True, hide_index=True)


# ============================================================
# MARKER RESULTS
# ============================================================

with tab4:
    st.header("Marker results")

    marker_df = pd.DataFrame(result["marker_results"])
    marker_df["RAG"] = marker_df["RAG"].apply(rag_badge)

    st.dataframe(marker_df, use_container_width=True, hide_index=True)


# ============================================================
# ADVISOR VIEW
# ============================================================

with tab5:
    st.header("Advisor view")

    advisor_df = pd.DataFrame([
        {"Field": "Outcome", "Value": action["Outcome"]},
        {"Field": "Recommended action", "Value": action["Action"]},
        {"Field": "Advisor message", "Value": action["Advisor_message"]},
        {"Field": "Chosen hypothesis", "Value": result["chosen"]["Hypothesis"]},
        {"Field": "Confidence", "Value": result["chosen"]["Confidence"]},
        {"Field": "Overall status", "Value": result["overall_rag"]},
        {"Field": "Agentic level", "Value": action["Agentic_level"]},
        {"Field": "Risk", "Value": action["Risk"]},
        {"Field": "Previous outcome", "Value": telemetry["previous_outcome"]},
        {"Field": "Repeat issue", "Value": "Yes" if telemetry["repeat_issue_7_days"] else "No"}
    ])

    st.dataframe(advisor_df, use_container_width=True, hide_index=True)


# ============================================================
# AUDIT LOG
# ============================================================

with tab6:
    st.header("Audit log")

    if st.button("Log this connection test"):
        st.session_state.audit_log.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scenario": st.session_state.scenario_used,
            "product": telemetry["product"],
            "symptom": telemetry["customer_symptom"],
            "overall_status": result["overall_rag"],
            "outcome": action["Outcome"],
            "chosen_hypothesis": result["chosen"]["Hypothesis"],
            "confidence": result["chosen"]["Confidence"],
            "recommended_action": action["Action"],
            "risk": action["Risk"]
        })

    if st.session_state.audit_log:
        st.dataframe(
            pd.DataFrame(st.session_state.audit_log),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No connection tests logged yet.")


st.caption(
    "Prototype only. Uses synthetic telemetry and demo thresholds. "
    "Do not use real customer data, internal documents, sensitive information, or production telemetry in this demo."
)
