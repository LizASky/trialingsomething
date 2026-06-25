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
# DEMO SCENARIOS
# ============================================================

SCENARIOS = {  # (Same as before; omitted here for brevity in snippet)
    "Healthy connection": {
        "product": "Streaming TV",
        "device_type": "Streaming device",
        "connection_method": "5GHz WiFi",
        "rssi": -55,
        "packet_loss": 0.3,
        "retransmission_rate": 3,
        "rapid_reconnects": 0,
        "telemetry_age_minutes": 12,
        # ... rest unchanged ...
    },
    # (other scenarios omitted for brevity, please copy from your original)
}

# ============================================================
# HELPER FUNCTIONS (same logic as before...)
# ============================================================

# [Include all your safe_value, rag_badge, calculate_rssi_rag, etc., 
#  functions exactly as before; no changes except the added functions below]

# === New functions for detailed diagnostic trace ===

def build_telemetry_rule_evaluations(t, marker_results):
    """Create a detailed table of telemetry values, thresholds applied, flag levels, and explanations for each marker."""
    evaluations = []
    for m in marker_results:
        # Map marker to threshold logic summary (customize as needed)
        if m["Marker"] == "WiFi signal strength":
            threshold_desc = "Green >= -67 dBm, Amber -75 to -67 dBm, Red < -75 dBm"
        elif m["Marker"] == "Packet loss":
            threshold_desc = "Green <=1%, Amber <=3%, Red >3%"
        elif m["Marker"] == "Retransmission rate":
            threshold_desc = "Green <=5%, Amber <=15%, Red >15%"
        elif m["Marker"] == "Rapid reconnects":
            threshold_desc = "Green <=1, Amber 2-4, Red>=5"
        elif m["Marker"] == "Line health":
            threshold_desc = "Green=OK, Amber=Unstable, Red=Fail"
        elif m["Marker"] == "Telemetry freshness":
            threshold_desc = "Green <=30 min, Amber <=120 min, Grey >120 min"
        elif m["Marker"] == "Equipment health":
            threshold_desc = "Green=OK, Red=Suspected fault, Grey=Unknown"
        else:
            threshold_desc = "No threshold defined"

        evaluations.append({
            "Telemetry Field": m["Marker"],
            "Value": m["Value"],
            "Thresholds/Rules": threshold_desc,
            "Flag": m["RAG"],
            "Explanation": m["Reason"]
        })
    return pd.DataFrame(evaluations)


def build_diagnostic_reasoning_text(t, marker_results, hypotheses, chosen, action):
    """Generates a detailed diagnostic reasoning narrative describing step-by-step how the outcome was reached."""

    text_lines = []

    # Observation and Validation
    text_lines.append(f"Telemetry collected includes signal strength, packet loss, retransmissions, reconnects, line health, equipment health, and telemetry freshness.")
    text_lines.append(f"Telemetry freshness: {t['telemetry_age_minutes']} minutes old.")
    if t["known_outage"]:
        text_lines.append("Known outage flag is active — normal troubleshooting suspended.")
    else:
        text_lines.append("No known outage reported — proceeding with diagnostics.")

    # Sensor & Marker Analysis
    text_lines.append("\nMarker evaluations:")
    for m in marker_results:
        value_str = m["Value"]
        flag_str = m["RAG"]
        reason_str = m["Reason"]
        text_lines.append(f"- {m['Marker']}: {value_str} → flagged as {flag_str} ({reason_str})")

    # Hypotheses Generation & Evidence
    text_lines.append("\nHypotheses generated:")
    for h in hypotheses:
        confidence = h.get("Confidence", "Unknown")
        hypothesis = h.get("Hypothesis", "Unknown Hypothesis")
        evidence_items = h.get("Evidence", [])
        text_lines.append(f"- {hypothesis} (Confidence: {confidence})")
        for e in evidence_items:
            text_lines.append(f"  • {e}")

    # Choosing the Best Hypothesis
    text_lines.append("\nChosen hypothesis:")
    text_lines.append(f"- {chosen.get('Hypothesis')}")
    text_lines.append(f"Recommended action:")
    text_lines.append(f"- {action.get('Action')}")
    text_lines.append(f"Risk level: {action.get('Risk')}\n")

    # Additional context for repeated issues etc.
    if t.get("repeat_issue_7_days"):
        text_lines.append("Note: Issue has repeated within 7 days — escalation or replacement may be more urgent.")

    text_lines.append("This detailed reasoning helps advisors and customers understand how the decision was made and supports learning.")

    return "\n".join(text_lines)

# === Reuse your existing detailed_customer/advisor functions (or enhance if you want)

# ============================================================
# The remainder of your base logic (run_agentic_test, randomise_scenario, etc.)
# Integrate the above functions within run_agentic_test to return detailed diagnostics
# ============================================================

def run_agentic_test(t):
    marker_results = build_marker_results(t)
    overall_rag = rollup_rag(marker_results)
    hypotheses = build_hypotheses(t, marker_results)
    chosen = choose_best_hypothesis(hypotheses)
    action = decide_action(t, chosen, overall_rag)

    detailed_customer_message = build_detailed_customer_message(t, marker_results, action)
    detailed_advisor_message = build_detailed_advisor_message(t, marker_results, action, hypotheses)
    diagnostic_trace_text = build_diagnostic_reasoning_text(t, marker_results, hypotheses, chosen, action)
    telemetry_rules_df = build_telemetry_rule_evaluations(t, marker_results)

    return {
        "marker_results": marker_results,
        "overall_rag": overall_rag,
        "hypotheses": hypotheses,
        "chosen": chosen,
        "action": action,
        "detailed_customer_message": detailed_customer_message,
        "detailed_advisor_message": detailed_advisor_message,
        "diagnostic_trace_text": diagnostic_trace_text,
        "telemetry_rules_df": telemetry_rules_df
    }

# ============================================================
# SESSION STATE and UI code remain mostly unchanged, except
# add a new tab called "Diagnostic details" to show this info
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

st.title("🛰️ Test SC")
st.subheader("Test my connection")

st.warning(
    "Demo only: this uses synthetic telemetry and made-up thresholds. It does not use real customer data, real production logic, or internal system data."
)

with st.sidebar:
    st.header("Demo mode")
    random_mode = st.toggle(
        "Pick a different synthetic scenario every time I test",
        value=True
    )
    selected_scenario = st.selectbox(
        "Or choose a specific scenario",
        list(SCENARIOS.keys())
    )
    st.caption(
        "If random mode is on, Test SC chooses a different synthetic scenario every time the button is clicked."
    )

st.markdown("## Check your connection")
st.write(
    "Click the button below to simulate a customer-style connection test. "
    "Test SC will collect synthetic telemetry, run an agentic diagnostic flow, and return a clear next step."
)
left, centre, right = st.columns([1, 2, 1])
with centre:
    run_button = st.button("🚀 Test my connection", use_container_width=True)

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
        "Checking data freshness...",
        "Checking WiFi signal and packet loss...",
        "Checking line health and known outage status...",
        "Checking whether equipment replacement may be needed...",
        "Generating possible outcomes...",
        "Selecting the clearest next step..."
    ]

    for index, step in enumerate(steps):
        status.info(step)
        progress.progress((index + 1) / len(steps))
        time.sleep(0.45)

    st.session_state.result = run_agentic_test(telemetry)
    st.session_state.run_complete = True
    status.success("Connection test complete.")

if not st.session_state.run_complete:
    st.info("No connection test has been run yet. Click **Test my connection** to start.")
    st.stop()

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
    st.metric("Next step type", action["Agentic_level"])

if action["Outcome"] in ["No issue found"]:
    st.success(result["detailed_customer_message"])
elif action["Outcome"] in ["Weak WiFi signal", "WiFi interference detected", "Unstable connection detected"]:
    st.warning(result["detailed_customer_message"])
elif action["Outcome"] in ["Engineer visit required", "Replacement recommended", "Known outage detected"]:
    st.error(result["detailed_customer_message"])
else:
    st.info(result["detailed_customer_message"])

st.subheader("Recommended next step")
st.write(action["Action"])

# === Updated tabs including new Diagnostic details tab ===

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Customer outcome",
    "Agentic AI reasoning",
    "Telemetry used",
    "Marker results",
    "Advisor view",
    "Audit log",
    "Diagnostic details"  # New tab for detailed diagnostic trace + telemetry rules
])

with tab1:
    st.header("Customer outcome")
    st.subheader(action["Outcome"])
    st.write(result["detailed_customer_message"])
    st.subheader("Next step")
    st.write(action["Action"])
    st.subheader("Plain English summary")
    st.write(
        f"Test SC looked at the synthetic connection data and selected **{action['Outcome']}** as the outcome."
    )

with tab2:
    st.header("Agentic AI reasoning")
    st.subheader("Step-by-step diagnostic reasoning")
    st.text_area(
        "Diagnostic reasoning narrative",
        result["diagnostic_trace_text"],
        height=350,
        disabled=True
    )

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
        {"Field": "Equipment health", "Value": telemetry["equipment_health"], "Meaning": "Synthetic equipment condition"},
        {"Field": "Customer symptom", "Value": telemetry["customer_symptom"], "Meaning": "What the customer reports"},
        {"Field": "Customer impact score", "Value": f"{telemetry['customer_impact_score']}/10", "Meaning": "Synthetic severity score"}
    ])
    st.dataframe(telemetry_df, use_container_width=True, hide_index=True)

with tab4:
    st.header("Marker results")
    marker_df = pd.DataFrame(result["marker_results"])
    marker_df["RAG"] = marker_df["RAG"].apply(rag_badge)
    st.dataframe(marker_df, use_container_width=True, hide_index=True)

with tab5:
    st.header("Advisor view")
    advisor_df = pd.DataFrame([
        {"Field": "Outcome", "Value": action["Outcome"]},
        {"Field": "Recommended action", "Value": action["Action"]},
        {"Field": "Advisor message", "Value": action["Advisor_message"]},
        {"Field": "Chosen hypothesis", "Value": result["chosen"]["Hypothesis"]},
        {"Field": "Confidence", "Value": result["chosen"]["Confidence"]},
        {"Field": "Overall status", "Value": result["overall_rag"]},
        {"Field": "Next step type", "Value": action["Agentic_level"]},
        {"Field": "Risk", "Value": action["Risk"]},
        {"Field": "Previous outcome", "Value": telemetry["previous_outcome"]},
        {"Field": "Repeat issue", "Value": "Yes" if telemetry["repeat_issue_7_days"] else "No"}
    ])
    st.dataframe(advisor_df, use_container_width=True, hide_index=True)
    st.subheader("Detailed diagnostic summary")
    st.text_area(
        "Advisor Explanation",
        result["detailed_advisor_message"],
        height=300,
        disabled=True
    )

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

with tab7:
    st.header("Diagnostic details")
    st.subheader("Telemetry Rule Evaluations")
    st.dataframe(result["telemetry_rules_df"], use_container_width=True)

    st.subheader("Step-by-Step Diagnostic Reasoning Narrative")
    st.text_area(
        "Diagnostic Narrative",
        result["diagnostic_trace_text"],
        height=350,
        disabled=True
    )

st.caption(
    "Prototype only. Uses synthetic telemetry and demo thresholds. "
    "Do not use real customer data, internal documents, sensitive information, or production telemetry in this demo."
)
