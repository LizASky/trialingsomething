import streamlit as st
import pandas as pd
import random
from datetime import datetime

# ============================================================
# TEST SC - AGENTIC REACTIVE JOURNEY DEMO
# Synthetic telemetry only
# Demo thresholds only
# No real customer data
# ============================================================

st.set_page_config(
    page_title="Test SC",
    page_icon="🛰️",
    layout="wide"
)

# ============================================================
# DEMO DATA
# ============================================================

PRODUCTS = [
    "Broadband",
    "Broadband / WiFi",
    "Streaming TV",
    "SOIP",
    "Sky Q",
    "IHH"
]

DEVICE_TYPES = [
    "Hub",
    "Streaming device",
    "Laptop or mobile",
    "Gaming device",
    "Tablet",
    "Smart TV",
    "Pod",
    "Unknown"
]

CONNECTION_METHODS = [
    "Ethernet",
    "5GHz WiFi",
    "2.4GHz WiFi",
    "Unknown"
]

LINE_HEALTH_OPTIONS = [
    "OK",
    "Unstable",
    "Fail",
    "Unknown"
]

HUB_MODELS = [
    "Hub 4",
    "Hub 6",
    "XER10",
    "Unknown"
]

CUSTOMER_SYMPTOMS = [
    "Buffering on streaming apps",
    "Slow broadband speed",
    "WiFi keeps dropping",
    "No broadband connection",
    "Poor picture quality",
    "Device keeps disconnecting",
    "Video calls freezing",
    "Gaming lag",
    "Service check failed",
    "No issue reported",
    "Intermittent connection",
    "Poor WiFi upstairs",
    "Unable to connect device"
]

PREVIOUS_OUTCOMES = [
    "No previous journey",
    "Self-serve guidance shown",
    "Advisor reviewed",
    "Engineer recommended",
    "Hardware replacement suggested",
    "No fault found",
    "Customer abandoned journey",
    "Telemetry unavailable",
    "Known outage message shown"
]

RISK_LEVELS = [
    "Low",
    "Medium",
    "High"
]


FIXED_SCENARIOS = {
    "Healthy service": {
        "product": "Streaming TV",
        "device_type": "Streaming device",
        "connection_method": "5GHz WiFi",
        "rssi": -55,
        "packet_loss": 0.3,
        "retransmission_rate": 3,
        "rapid_reconnects": 0,
        "telemetry_age_minutes": 15,
        "line_health": "OK",
        "known_outage": False,
        "repeat_issue_7_days": False,
        "advisor_override_history": False,
        "customer_symptom": "No issue reported",
        "test_sc_runs_24h": 1,
        "previous_outcome": "No previous journey",
        "hub_model": "Hub 6",
        "pod_present": False,
        "device_category_confidence": "High",
        "customer_impact_score": 1,
        "cost_to_assure_risk": "Low",
        "digital_containment_risk": "Low"
    },
    "Poor WiFi signal": {
        "product": "Streaming TV",
        "device_type": "Streaming device",
        "connection_method": "2.4GHz WiFi",
        "rssi": -82,
        "packet_loss": 2.5,
        "retransmission_rate": 12,
        "rapid_reconnects": 3,
        "telemetry_age_minutes": 15,
        "line_health": "OK",
        "known_outage": False,
        "repeat_issue_7_days": True,
        "advisor_override_history": False,
        "customer_symptom": "Buffering or poor picture quality",
        "test_sc_runs_24h": 3,
        "previous_outcome": "Self-serve guidance shown",
        "hub_model": "Hub 6",
        "pod_present": True,
        "device_category_confidence": "High",
        "customer_impact_score": 7,
        "cost_to_assure_risk": "Medium",
        "digital_containment_risk": "Medium"
    },
    "Interference or congestion": {
        "product": "Broadband / WiFi",
        "device_type": "Laptop or mobile",
        "connection_method": "5GHz WiFi",
        "rssi": -63,
        "packet_loss": 5.8,
        "retransmission_rate": 28,
        "rapid_reconnects": 2,
        "telemetry_age_minutes": 15,
        "line_health": "OK",
        "known_outage": False,
        "repeat_issue_7_days": True,
        "advisor_override_history": False,
        "customer_symptom": "Slow speeds",
        "test_sc_runs_24h": 4,
        "previous_outcome": "Customer abandoned journey",
        "hub_model": "Hub 6",
        "pod_present": False,
        "device_category_confidence": "Medium",
        "customer_impact_score": 8,
        "cost_to_assure_risk": "Medium",
        "digital_containment_risk": "High"
    },
    "Stale telemetry / cannot diagnose": {
        "product": "Streaming TV",
        "device_type": "Streaming device",
        "connection_method": "Unknown",
        "rssi": None,
        "packet_loss": None,
        "retransmission_rate": None,
        "rapid_reconnects": None,
        "telemetry_age_minutes": 420,
        "line_health": "Unknown",
        "known_outage": False,
        "repeat_issue_7_days": False,
        "advisor_override_history": False,
        "customer_symptom": "Service check failed",
        "test_sc_runs_24h": 2,
        "previous_outcome": "Telemetry unavailable",
        "hub_model": "Unknown",
        "pod_present": False,
        "device_category_confidence": "Unknown",
        "customer_impact_score": 5,
        "cost_to_assure_risk": "Low",
        "digital_containment_risk": "Medium"
    },
    "Potential line issue": {
        "product": "Broadband",
        "device_type": "Hub",
        "connection_method": "Ethernet",
        "rssi": None,
        "packet_loss": 9.5,
        "retransmission_rate": 4,
        "rapid_reconnects": 0,
        "telemetry_age_minutes": 15,
        "line_health": "Fail",
        "known_outage": False,
        "repeat_issue_7_days": True,
        "advisor_override_history": True,
        "customer_symptom": "Connection drops",
        "test_sc_runs_24h": 5,
        "previous_outcome": "Advisor reviewed",
        "hub_model": "Hub 6",
        "pod_present": False,
        "device_category_confidence": "High",
        "customer_impact_score": 9,
        "cost_to_assure_risk": "High",
        "digital_containment_risk": "High"
    },
    "Known outage suppression": {
        "product": "Broadband",
        "device_type": "Hub",
        "connection_method": "Ethernet",
        "rssi": None,
        "packet_loss": 12.0,
        "retransmission_rate": 8,
        "rapid_reconnects": 2,
        "telemetry_age_minutes": 15,
        "line_health": "Fail",
        "known_outage": True,
        "repeat_issue_7_days": False,
        "advisor_override_history": False,
        "customer_symptom": "No broadband connection",
        "test_sc_runs_24h": 1,
        "previous_outcome": "Known outage message shown",
        "hub_model": "Hub 6",
        "pod_present": False,
        "device_category_confidence": "High",
        "customer_impact_score": 10,
        "cost_to_assure_risk": "Low",
        "digital_containment_risk": "Low"
    }
}


def generate_random_case(case_number):
    product = random.choice(PRODUCTS)
    device_type = random.choice(DEVICE_TYPES)
    connection_method = random.choice(CONNECTION_METHODS)

    if connection_method in ["5GHz WiFi", "2.4GHz WiFi"]:
        rssi = random.randint(-92, -40)
        retransmission_rate = random.randint(0, 45)
    else:
        rssi = None
        retransmission_rate = random.choice([None, random.randint(0, 25)])

    if connection_method == "Unknown":
        rapid_reconnects = None
    else:
        rapid_reconnects = random.randint(0, 15)

    return {
        "product": product,
        "device_type": device_type,
        "connection_method": connection_method,
        "rssi": rssi,
        "packet_loss": round(random.uniform(0, 18), 1),
        "retransmission_rate": retransmission_rate,
        "rapid_reconnects": rapid_reconnects,
        "telemetry_age_minutes": random.choice([
            random.randint(5, 30),
            random.randint(31, 120),
            random.randint(121, 600)
        ]),
        "line_health": random.choice(LINE_HEALTH_OPTIONS),
        "known_outage": random.choices([False, True], weights=[85, 15], k=1)[0],
        "repeat_issue_7_days": random.choices([False, True], weights=[60, 40], k=1)[0],
        "advisor_override_history": random.choices([False, True], weights=[80, 20], k=1)[0],
        "customer_symptom": random.choice(CUSTOMER_SYMPTOMS),
        "test_sc_runs_24h": random.randint(0, 6),
        "previous_outcome": random.choice(PREVIOUS_OUTCOMES),
        "hub_model": random.choice(HUB_MODELS),
        "pod_present": random.choices([False, True], weights=[65, 35], k=1)[0],
        "device_category_confidence": random.choice(["High", "Medium", "Low", "Unknown"]),
        "customer_impact_score": random.randint(1, 10),
        "cost_to_assure_risk": random.choice(RISK_LEVELS),
        "digital_containment_risk": random.choice(RISK_LEVELS)
    }


RANDOM_SCENARIOS = {}

for i in range(1, 31):
    RANDOM_SCENARIOS[f"Synthetic case {i:02d}"] = generate_random_case(i)

SCENARIOS = {
    **FIXED_SCENARIOS,
    **RANDOM_SCENARIOS
}

# ============================================================
# RAG / MARKER LOGIC
# ============================================================

RAG_ORDER = {
    "Green": 1,
    "Amber": 2,
    "Red": 3,
    "Grey": 4
}


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


def safe_value(value, suffix=""):
    if value is None:
        return "Not available"
    return f"{value}{suffix}"


def calculate_rssi_rag(rssi):
    if rssi is None:
        return "Grey", "RSSI telemetry unavailable"
    if rssi >= -67:
        return "Green", "Signal strength looks healthy"
    if -75 <= rssi < -67:
        return "Amber", "Signal strength is degraded"
    return "Red", "Signal strength is poor"


def calculate_packet_loss_rag(packet_loss):
    if packet_loss is None:
        return "Grey", "Packet loss telemetry unavailable"
    if packet_loss <= 1:
        return "Green", "Packet loss is low"
    if 1 < packet_loss <= 3:
        return "Amber", "Packet loss is elevated"
    return "Red", "Packet loss is high"


def calculate_retransmission_rag(retransmission_rate):
    if retransmission_rate is None:
        return "Grey", "Retransmission telemetry unavailable"
    if retransmission_rate <= 5:
        return "Green", "Retransmissions are low"
    if 5 < retransmission_rate <= 15:
        return "Amber", "Retransmissions are elevated"
    return "Red", "Retransmissions are high"


def calculate_reconnect_rag(rapid_reconnects):
    if rapid_reconnects is None:
        return "Grey", "Reconnect telemetry unavailable"
    if rapid_reconnects <= 1:
        return "Green", "Reconnect behaviour looks stable"
    if 1 < rapid_reconnects <= 4:
        return "Amber", "Some reconnect instability detected"
    return "Red", "Frequent reconnect instability detected"


def calculate_connection_method_rag(connection_method, device_type):
    if connection_method == "Unknown":
        return "Grey", "Connection method unavailable"
    if connection_method == "Ethernet":
        return "Green", "Device is connected by Ethernet"
    if connection_method == "5GHz WiFi":
        return "Green", "Device is connected on 5GHz WiFi"
    if connection_method == "2.4GHz WiFi":
        if device_type in ["Streaming device", "Laptop or mobile", "Gaming device", "Smart TV"]:
            return "Amber", "Device is connected on 2.4GHz WiFi, which may limit performance"
        return "Green", "2.4GHz WiFi may be acceptable for this device type"
    return "Grey", "Connection method not recognised"


def calculate_telemetry_freshness_rag(age_minutes):
    if age_minutes is None:
        return "Grey", "Telemetry timestamp unavailable"
    if age_minutes <= 30:
        return "Green", "Telemetry is fresh"
    if 30 < age_minutes <= 120:
        return "Amber", "Telemetry is slightly old"
    return "Grey", "Telemetry is too old to support confident diagnosis"


def calculate_line_health_rag(line_health):
    if line_health == "OK":
        return "Green", "Line health check is OK"
    if line_health == "Unstable":
        return "Amber", "Line health appears unstable"
    if line_health == "Fail":
        return "Red", "Line health check has failed"
    return "Grey", "Line health is unknown"


def build_marker_results(telemetry):
    marker_results = []

    rssi_rag, rssi_reason = calculate_rssi_rag(telemetry["rssi"])
    marker_results.append({
        "marker": "RSSI",
        "value": safe_value(telemetry["rssi"], " dBm"),
        "rag": rssi_rag,
        "reason": rssi_reason
    })

    packet_rag, packet_reason = calculate_packet_loss_rag(telemetry["packet_loss"])
    marker_results.append({
        "marker": "Packet Loss",
        "value": safe_value(telemetry["packet_loss"], "%"),
        "rag": packet_rag,
        "reason": packet_reason
    })

    retrans_rag, retrans_reason = calculate_retransmission_rag(telemetry["retransmission_rate"])
    marker_results.append({
        "marker": "Retransmission Rate",
        "value": safe_value(telemetry["retransmission_rate"], "%"),
        "rag": retrans_rag,
        "reason": retrans_reason
    })

    reconnect_rag, reconnect_reason = calculate_reconnect_rag(telemetry["rapid_reconnects"])
    marker_results.append({
        "marker": "Rapid Reconnects",
        "value": safe_value(telemetry["rapid_reconnects"]),
        "rag": reconnect_rag,
        "reason": reconnect_reason
    })

    connection_rag, connection_reason = calculate_connection_method_rag(
        telemetry["connection_method"],
        telemetry["device_type"]
    )
    marker_results.append({
        "marker": "Connection Method",
        "value": telemetry["connection_method"],
        "rag": connection_rag,
        "reason": connection_reason
    })

    freshness_rag, freshness_reason = calculate_telemetry_freshness_rag(
        telemetry["telemetry_age_minutes"]
    )
    marker_results.append({
        "marker": "Telemetry Freshness",
        "value": f"{telemetry['telemetry_age_minutes']} minutes old",
        "rag": freshness_rag,
        "reason": freshness_reason
    })

    line_rag, line_reason = calculate_line_health_rag(telemetry["line_health"])
    marker_results.append({
        "marker": "Line Health",
        "value": telemetry["line_health"],
        "rag": line_rag,
        "reason": line_reason
    })

    return marker_results


def roll_up_rag(marker_results):
    rags = [item["rag"] for item in marker_results]

    if "Grey" in rags:
        return "Grey"
    if "Red" in rags:
        return "Red"
    if "Amber" in rags:
        return "Amber"
    return "Green"

# ============================================================
# AGENTIC REASONING
# ============================================================

def validate_telemetry(telemetry, marker_results):
    notes = []

    if telemetry["known_outage"]:
        notes.append("Known outage is active, so standard troubleshooting should be suppressed.")

    if telemetry["telemetry_age_minutes"] > 120:
        notes.append("Telemetry is stale, so confidence should be reduced.")

    grey_markers = [m["marker"] for m in marker_results if m["rag"] == "Grey"]

    if grey_markers:
        notes.append(f"Some markers are Grey or unavailable: {', '.join(grey_markers)}.")

    if not notes:
        notes.append("Telemetry is available and suitable for demo diagnosis.")

    return notes


def build_hypotheses(telemetry, marker_results):
    marker_lookup = {m["marker"]: m for m in marker_results}
    hypotheses = []

    if telemetry["known_outage"]:
        hypotheses.append({
            "hypothesis": "Known outage or wider service issue",
            "evidence": [
                "Known outage flag is active",
                "Standard troubleshooting should be suppressed"
            ],
            "confidence": "High"
        })
        return hypotheses

    if marker_lookup["Telemetry Freshness"]["rag"] == "Grey":
        hypotheses.append({
            "hypothesis": "Unable to diagnose due to stale or missing telemetry",
            "evidence": [
                "Telemetry is too old or incomplete",
                "One or more markers are Grey"
            ],
            "confidence": "High"
        })

    if marker_lookup["Line Health"]["rag"] == "Red":
        hypotheses.append({
            "hypothesis": "Potential line or network-side issue",
            "evidence": [
                "Line Health marker is Red",
                "Customer symptom may relate to connection drop or loss of service"
            ],
            "confidence": "High"
        })

    if marker_lookup["RSSI"]["rag"] in ["Amber", "Red"] and telemetry["connection_method"] in ["2.4GHz WiFi", "5GHz WiFi"]:
        hypotheses.append({
            "hypothesis": "Poor WiFi signal or poor device placement",
            "evidence": [
                f"RSSI marker is {marker_lookup['RSSI']['rag']}",
                f"Connection method is {telemetry['connection_method']}"
            ],
            "confidence": "Medium"
        })

    if marker_lookup["Packet Loss"]["rag"] == "Red" and marker_lookup["Retransmission Rate"]["rag"] in ["Amber", "Red"]:
        hypotheses.append({
            "hypothesis": "WiFi interference or congestion",
            "evidence": [
                "Packet Loss is Red",
                f"Retransmission Rate is {marker_lookup['Retransmission Rate']['rag']}"
            ],
            "confidence": "Medium"
        })

    if marker_lookup["Rapid Reconnects"]["rag"] in ["Amber", "Red"]:
        hypotheses.append({
            "hypothesis": "Intermittent connectivity instability",
            "evidence": [
                f"Rapid Reconnects marker is {marker_lookup['Rapid Reconnects']['rag']}"
            ],
            "confidence": "Medium"
        })

    if not hypotheses:
        hypotheses.append({
            "hypothesis": "Service appears healthy based on available synthetic telemetry",
            "evidence": [
                "No Red markers detected",
                "Telemetry freshness is acceptable",
                "Line health is OK"
            ],
            "confidence": "High"
        })

    return hypotheses


def choose_best_hypothesis(hypotheses):
    priority = {
        "High": 3,
        "Medium": 2,
        "Low": 1
    }

    return sorted(
        hypotheses,
        key=lambda h: priority.get(h["confidence"], 0),
        reverse=True
    )[0]


def decide_action(telemetry, selected_hypothesis, overall_rag):
    hypothesis = selected_hypothesis["hypothesis"]

    if telemetry["known_outage"]:
        return {
            "action_type": "Suppress normal journey",
            "action": "Do not continue with standard troubleshooting. Show outage-aware messaging and monitor for restoration.",
            "risk": "Low",
            "requires_approval": "No",
            "agentic_level": "Level 2 - Recommend / route",
            "expected_result": "Customer receives clearer guidance and avoids unnecessary troubleshooting."
        }

    if "Unable to diagnose" in hypothesis:
        return {
            "action_type": "Gather more evidence",
            "action": "Refresh telemetry, re-run checks, or route to advisor if telemetry remains unavailable.",
            "risk": "Low",
            "requires_approval": "No",
            "agentic_level": "Level 1 - Explain",
            "expected_result": "Avoids false diagnosis caused by stale or missing data."
        }

    if "line or network-side" in hypothesis:
        return {
            "action_type": "Escalate or route",
            "action": "Route to line-health investigation path before suggesting in-home fixes.",
            "risk": "Medium",
            "requires_approval": "Yes",
            "agentic_level": "Level 3 - Guided action",
            "expected_result": "Avoids unnecessary WiFi troubleshooting when line evidence is stronger."
        }

    if "Poor WiFi signal" in hypothesis:
        return {
            "action_type": "Optimise in-home experience",
            "action": "Guide customer to improve device placement, check distance from hub or pod, and re-test before any engineer route.",
            "risk": "Low",
            "requires_approval": "No",
            "agentic_level": "Level 2 - Recommend",
            "expected_result": "Improves customer experience without unnecessary intervention."
        }

    if "interference or congestion" in hypothesis:
        return {
            "action_type": "Optimise WiFi conditions",
            "action": "Recommend WiFi optimisation path, check congestion or interference, and re-test after change.",
            "risk": "Low",
            "requires_approval": "No",
            "agentic_level": "Level 2 - Recommend",
            "expected_result": "Reduces retransmissions and packet loss."
        }

    if "Intermittent connectivity instability" in hypothesis:
        return {
            "action_type": "Stability investigation",
            "action": "Check recent reconnect pattern, repeat issue history, and advise a controlled re-test.",
            "risk": "Low",
            "requires_approval": "No",
            "agentic_level": "Level 2 - Recommend",
            "expected_result": "Confirms whether instability is recurring or temporary."
        }

    if overall_rag == "Green":
        return {
            "action_type": "Reassure and close",
            "action": "Explain that available checks look healthy and provide self-serve guidance if symptoms continue.",
            "risk": "Low",
            "requires_approval": "No",
            "agentic_level": "Level 1 - Explain",
            "expected_result": "Customer understands no fault was detected from available checks."
        }

    return {
        "action_type": "Advisor review",
        "action": "Present evidence and recommended path to advisor for judgement.",
        "risk": "Medium",
        "requires_approval": "Yes",
        "agentic_level": "Level 3 - Guided action",
        "expected_result": "Human review is used where evidence is mixed."
    }


def build_customer_message(telemetry, selected_hypothesis, action):
    if telemetry["known_outage"]:
        return (
            "There may be a wider service issue affecting the service. "
            "This demo suppresses normal troubleshooting and shows outage-aware guidance instead."
        )

    if "Unable to diagnose" in selected_hypothesis["hypothesis"]:
        return (
            "The demo could not complete a confident check because some telemetry is missing or out of date. "
            "The next best step is to refresh the data or route to advisor review."
        )

    return (
        f"The demo found signs of: {selected_hypothesis['hypothesis']}. "
        f"The next best step is to {action['action'].lower()}"
    )


def build_advisor_message(telemetry, selected_hypothesis, action, marker_results):
    red_markers = [m["marker"] for m in marker_results if m["rag"] == "Red"]
    amber_markers = [m["marker"] for m in marker_results if m["rag"] == "Amber"]
    grey_markers = [m["marker"] for m in marker_results if m["rag"] == "Grey"]

    return {
        "Summary": selected_hypothesis["hypothesis"],
        "Recommended action": action["action"],
        "Confidence": selected_hypothesis["confidence"],
        "Product": telemetry["product"],
        "Device type": telemetry["device_type"],
        "Connection method": telemetry["connection_method"],
        "Hub model": telemetry["hub_model"],
        "Pod present": "Yes" if telemetry["pod_present"] else "No",
        "Device category confidence": telemetry["device_category_confidence"],
        "Customer impact score": f"{telemetry['customer_impact_score']}/10",
        "Previous outcome": telemetry["previous_outcome"],
        "Test SC runs in 24h": telemetry["test_sc_runs_24h"],
        "Cost-to-assure risk": telemetry["cost_to_assure_risk"],
        "Digital containment risk": telemetry["digital_containment_risk"],
        "Red markers": ", ".join(red_markers) if red_markers else "None",
        "Amber markers": ", ".join(amber_markers) if amber_markers else "None",
        "Grey markers": ", ".join(grey_markers) if grey_markers else "None",
        "Repeat issue in last 7 days": "Yes" if telemetry["repeat_issue_7_days"] else "No",
        "Advisor override history": "Yes" if telemetry["advisor_override_history"] else "No",
        "Approval needed": action["requires_approval"],
        "Risk": action["risk"]
    }


def run_agentic_check(telemetry):
    marker_results = build_marker_results(telemetry)
    validation_notes = validate_telemetry(telemetry, marker_results)
    overall_rag = roll_up_rag(marker_results)
    hypotheses = build_hypotheses(telemetry, marker_results)
    selected_hypothesis = choose_best_hypothesis(hypotheses)
    action = decide_action(telemetry, selected_hypothesis, overall_rag)
    customer_message = build_customer_message(telemetry, selected_hypothesis, action)
    advisor_message = build_advisor_message(telemetry, selected_hypothesis, action, marker_results)

    return {
        "marker_results": marker_results,
        "validation_notes": validation_notes,
        "overall_rag": overall_rag,
        "hypotheses": hypotheses,
        "selected_hypothesis": selected_hypothesis,
        "action": action,
        "customer_message": customer_message,
        "advisor_message": advisor_message
    }

# ============================================================
# SESSION STATE
# ============================================================

if "audit_log" not in st.session_state:
    st.session_state.audit_log = []

# ============================================================
# PAGE HEADER
# ============================================================

st.title("🛰️ Test SC")
st.subheader("Agentic Reactive Journey Demo with Synthetic Telemetry")

st.info(
    "This is a working demo using made-up telemetry and demo thresholds. "
    "It shows how a diagnostic journey could observe telemetry, validate data, form hypotheses, choose a next best action, explain the decision, and create an audit trail."
)

st.warning(
    "All telemetry shown in this demo is synthetic. It does not use real customer data, internal documents, real system thresholds, or production logic."
)

# ============================================================
# SIDEBAR CONTROLS
# ============================================================

with st.sidebar:
    st.header("Demo controls")

    selected_scenario = st.selectbox(
        "Choose a synthetic telemetry scenario",
        list(SCENARIOS.keys())
    )

    base = SCENARIOS[selected_scenario].copy()

    st.divider()
    st.caption("Optional: manually adjust the synthetic telemetry")

    product = st.selectbox(
        "Product",
        PRODUCTS,
        index=PRODUCTS.index(base["product"]) if base["product"] in PRODUCTS else 0
    )

    device_type = st.selectbox(
        "Device type",
        DEVICE_TYPES,
        index=DEVICE_TYPES.index(base["device_type"]) if base["device_type"] in DEVICE_TYPES else 0
    )

    connection_method = st.selectbox(
        "Connection method",
        CONNECTION_METHODS,
        index=CONNECTION_METHODS.index(base["connection_method"]) if base["connection_method"] in CONNECTION_METHODS else 0
    )

    use_null_wifi = st.checkbox(
        "No WiFi marker telemetry available",
        value=base["rssi"] is None
    )

    if use_null_wifi:
        rssi = None
        retransmission_rate = None
    else:
        rssi = st.slider(
            "RSSI dBm",
            min_value=-95,
            max_value=-30,
            value=base["rssi"] if base["rssi"] is not None else -65
        )

        retransmission_rate = st.slider(
            "Retransmission rate %",
            min_value=0,
            max_value=50,
            value=base["retransmission_rate"] if base["retransmission_rate"] is not None else 5
        )

    packet_loss = st.slider(
        "Packet loss %",
        min_value=0.0,
        max_value=20.0,
        value=float(base["packet_loss"]) if base["packet_loss"] is not None else 0.0,
        step=0.1
    )

    rapid_reconnects = st.slider(
        "Rapid reconnects",
        min_value=0,
        max_value=20,
        value=base["rapid_reconnects"] if base["rapid_reconnects"] is not None else 0
    )

    telemetry_age_minutes = st.slider(
        "Telemetry age in minutes",
        min_value=0,
        max_value=600,
        value=base["telemetry_age_minutes"]
    )

    line_health = st.selectbox(
        "Line health",
        LINE_HEALTH_OPTIONS,
        index=LINE_HEALTH_OPTIONS.index(base["line_health"]) if base["line_health"] in LINE_HEALTH_OPTIONS else 0
    )

    known_outage = st.checkbox("Known outage active", value=base["known_outage"])
    repeat_issue_7_days = st.checkbox("Repeat issue in last 7 days", value=base["repeat_issue_7_days"])
    advisor_override_history = st.checkbox("Advisor override history", value=base["advisor_override_history"])

    customer_symptom = st.text_input(
        "Customer symptom",
        value=base["customer_symptom"]
    )

# ============================================================
# CURRENT TELEMETRY PAYLOAD
# ============================================================

telemetry = {
    "product": product,
    "device_type": device_type,
    "connection_method": connection_method,
    "rssi": rssi,
    "packet_loss": packet_loss,
    "retransmission_rate": retransmission_rate,
    "rapid_reconnects": rapid_reconnects,
    "telemetry_age_minutes": telemetry_age_minutes,
    "line_health": line_health,
    "known_outage": known_outage,
    "repeat_issue_7_days": repeat_issue_7_days,
    "advisor_override_history": advisor_override_history,
    "customer_symptom": customer_symptom,
    "test_sc_runs_24h": base["test_sc_runs_24h"],
    "previous_outcome": base["previous_outcome"],
    "hub_model": base["hub_model"],
    "pod_present": base["pod_present"],
    "device_category_confidence": base["device_category_confidence"],
    "customer_impact_score": base["customer_impact_score"],
    "cost_to_assure_risk": base["cost_to_assure_risk"],
    "digital_containment_risk": base["digital_containment_risk"]
}

result = run_agentic_check(telemetry)

# ============================================================
# SUMMARY CARDS
# ============================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Product", telemetry["product"])

with col2:
    st.metric("Overall RAG", rag_badge(result["overall_rag"]))

with col3:
    st.metric("Selected diagnosis", result["selected_hypothesis"]["hypothesis"])

with col4:
    st.metric("Confidence", result["selected_hypothesis"]["confidence"])

st.divider()

# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "1. Customer view",
    "2. Advisor view",
    "3. Telemetry",
    "4. Marker logic",
    "5. Agent reasoning",
    "6. Telemetry explained",
    "7. Audit log"
])

# ============================================================
# CUSTOMER VIEW
# ============================================================

with tab1:
    st.header("Customer-facing journey")

    st.subheader("Test SC result")

    if result["overall_rag"] == "Green":
        st.success(rag_badge(result["overall_rag"]))
    elif result["overall_rag"] == "Amber":
        st.warning(rag_badge(result["overall_rag"]))
    elif result["overall_rag"] == "Red":
        st.error(rag_badge(result["overall_rag"]))
    else:
        st.info(rag_badge(result["overall_rag"]))

    st.write(result["customer_message"])

    st.subheader("Next best action")
    st.write(result["action"]["action"])

    st.subheader("What this demo is showing")
    st.write(
        "Instead of sending the customer through a fixed journey, the demo checks available telemetry, validates whether the evidence is reliable, identifies the strongest hypothesis, and chooses the safest next step."
    )

# ============================================================
# ADVISOR VIEW
# ============================================================

with tab2:
    st.header("Advisor / operational view")

    advisor_df = pd.DataFrame(
        [{"Field": key, "Value": value} for key, value in result["advisor_message"].items()]
    )

    st.dataframe(advisor_df, use_container_width=True, hide_index=True)

    st.subheader("Recommended advisor handling")
    st.write(result["action"]["action"])

    st.subheader("Agentic level")
    st.write(result["action"]["agentic_level"])

    st.subheader("Expected result")
    st.write(result["action"]["expected_result"])

# ============================================================
# TELEMETRY VIEW
# ============================================================

with tab3:
    st.header("Synthetic telemetry payload")

    telemetry_df = pd.DataFrame([
        {"Telemetry field": "Product", "Value": telemetry["product"], "What it means": "Service area being checked"},
        {"Telemetry field": "Device type", "Value": telemetry["device_type"], "What it means": "Device involved in the journey"},
        {"Telemetry field": "Connection method", "Value": telemetry["connection_method"], "What it means": "How the device is connected"},
        {"Telemetry field": "RSSI", "Value": safe_value(telemetry["rssi"], " dBm"), "What it means": "WiFi signal strength"},
        {"Telemetry field": "Packet loss", "Value": safe_value(telemetry["packet_loss"], "%"), "What it means": "Percentage of packets dropping"},
        {"Telemetry field": "Retransmission rate", "Value": safe_value(telemetry["retransmission_rate"], "%"), "What it means": "How often data has to be resent"},
        {"Telemetry field": "Rapid reconnects", "Value": safe_value(telemetry["rapid_reconnects"]), "What it means": "Fast disconnect or reconnect events"},
        {"Telemetry field": "Telemetry age", "Value": f"{telemetry['telemetry_age_minutes']} minutes", "What it means": "How old the latest data is"},
        {"Telemetry field": "Line health", "Value": telemetry["line_health"], "What it means": "Simplified line check status"},
        {"Telemetry field": "Known outage", "Value": "Yes" if telemetry["known_outage"] else "No", "What it means": "Whether outage suppression should apply"},
        {"Telemetry field": "Repeat issue 7 days", "Value": "Yes" if telemetry["repeat_issue_7_days"] else "No", "What it means": "Whether the issue appears repeated"},
        {"Telemetry field": "Advisor override history", "Value": "Yes" if telemetry["advisor_override_history"] else "No", "What it means": "Whether an advisor previously overrode the journey"},
        {"Telemetry field": "Test SC runs in 24h", "Value": telemetry["test_sc_runs_24h"], "What it means": "How many times the customer has tried the journey"},
        {"Telemetry field": "Previous outcome", "Value": telemetry["previous_outcome"], "What it means": "What happened last time"},
        {"Telemetry field": "Hub model", "Value": telemetry["hub_model"], "What it means": "Synthetic hardware context"},
        {"Telemetry field": "Pod present", "Value": "Yes" if telemetry["pod_present"] else "No", "What it means": "Whether a pod or booster exists in the home"},
        {"Telemetry field": "Device category confidence", "Value": telemetry["device_category_confidence"], "What it means": "Confidence in device identification"},
        {"Telemetry field": "Customer impact score", "Value": f"{telemetry['customer_impact_score']}/10", "What it means": "Demo severity score"},
        {"Telemetry field": "Cost-to-assure risk", "Value": telemetry["cost_to_assure_risk"], "What it means": "Demo estimate of expensive intervention risk"},
        {"Telemetry field": "Digital containment risk", "Value": telemetry["digital_containment_risk"], "What it means": "Demo risk of customer leaking to advisor or contact"},
        {"Telemetry field": "Customer symptom", "Value": telemetry["customer_symptom"], "What it means": "What the customer says is wrong"}
    ])

    st.dataframe(telemetry_df, use_container_width=True, hide_index=True)
    st.caption("All telemetry in this demo is synthetic.")

# ============================================================
# MARKER LOGIC
# ============================================================

with tab4:
    st.header("Marker interpretation")

    marker_df = pd.DataFrame(result["marker_results"])
    marker_df["rag"] = marker_df["rag"].apply(rag_badge)

    st.dataframe(marker_df, use_container_width=True, hide_index=True)

    st.subheader("Marker RAG visual")

    chart_df = pd.DataFrame([
        {
            "Marker": item["marker"],
            "Severity": RAG_ORDER[item["rag"]]
        }
        for item in result["marker_results"]
    ])

    st.bar_chart(chart_df.set_index("Marker"))

    st.caption(
        "Severity scale in this demo: Green = 1, Amber = 2, Red = 3, Grey = 4. "
        "This is only for visualising the synthetic marker state."
    )

# ============================================================
# AGENT REASONING
# ============================================================

with tab5:
    st.header("Agentic reasoning loop")

    st.subheader("1. Observe")
    st.write("The demo reads the synthetic telemetry payload and customer symptom.")

    st.subheader("2. Validate")
    for note in result["validation_notes"]:
        st.write(f"- {note}")

    st.subheader("3. Interpret")
    st.write("The demo maps telemetry fields to marker-level RAG outcomes.")

    st.subheader("4. Hypothesise")
    for hypothesis in result["hypotheses"]:
        with st.expander(f"{hypothesis['hypothesis']} — Confidence: {hypothesis['confidence']}"):
            for evidence in hypothesis["evidence"]:
                st.write(f"- {evidence}")

    st.subheader("5. Decide")
    st.write(f"Selected hypothesis: **{result['selected_hypothesis']['hypothesis']}**")
    st.write(f"Action type: **{result['action']['action_type']}**")
    st.write(f"Risk: **{result['action']['risk']}**")
    st.write(f"Requires approval: **{result['action']['requires_approval']}**")

    st.subheader("6. Act")
    st.write(result["action"]["action"])

    st.subheader("7. Explain")
    st.write(result["customer_message"])

    st.subheader("8. Measure")
    st.write(
        "In a real version, measurement could check whether marker RAG improved, whether the customer re-ran the journey, whether an advisor overrode the result, whether repeat contact occurred, and whether cost-to-assure reduced."
    )

    st.subheader("9. Learn")
    st.write(
        "In a governed version, the system would not rewrite production logic automatically. It would create a learning record for review by SMEs."
    )

# ============================================================
# TELEMETRY EXPLAINED
# ============================================================

with tab6:
    st.header("Telemetry explained")

    st.write(
        "This demo uses synthetic telemetry to show how an agentic diagnostic journey could reason over service health. "
        "The values are made up and are only used to demonstrate the pattern."
    )

    telemetry_explainer = pd.DataFrame([
        {
            "Field": "RSSI",
            "Plain English meaning": "WiFi signal strength. A value closer to zero is stronger.",
            "Example": "-55 is good, -82 is poor",
            "How the demo uses it": "To detect weak WiFi signal or poor device placement"
        },
        {
            "Field": "Packet loss",
            "Plain English meaning": "How much data is being lost in transmission.",
            "Example": "0.3% is low, 9.5% is high",
            "How the demo uses it": "To detect instability, buffering, dropouts or degraded service"
        },
        {
            "Field": "Retransmission rate",
            "Plain English meaning": "How often data has to be resent.",
            "Example": "3% is low, 28% is high",
            "How the demo uses it": "To identify possible interference or congestion"
        },
        {
            "Field": "Rapid reconnects",
            "Plain English meaning": "How often a device disconnects and quickly reconnects.",
            "Example": "0 is stable, 10 suggests instability",
            "How the demo uses it": "To detect intermittent WiFi or device stability problems"
        },
        {
            "Field": "Telemetry age",
            "Plain English meaning": "How old the latest telemetry is.",
            "Example": "15 minutes is fresh, 420 minutes is stale",
            "How the demo uses it": "To decide whether the data is trustworthy"
        },
        {
            "Field": "Line health",
            "Plain English meaning": "Simplified view of whether the broadband line looks OK, unstable or failed.",
            "Example": "OK, Unstable, Fail, Unknown",
            "How the demo uses it": "To distinguish in-home issues from possible line or network issues"
        },
        {
            "Field": "Known outage",
            "Plain English meaning": "Whether a wider issue is active.",
            "Example": "Yes or No",
            "How the demo uses it": "To suppress normal troubleshooting if an outage is known"
        },
        {
            "Field": "Repeat issue 7 days",
            "Plain English meaning": "Whether the customer has seen a similar issue recently.",
            "Example": "Yes or No",
            "How the demo uses it": "To avoid repeating ineffective journeys"
        },
        {
            "Field": "Advisor override history",
            "Plain English meaning": "Whether an advisor previously overrode the standard outcome.",
            "Example": "Yes or No",
            "How the demo uses it": "To flag that the normal path may not have been suitable"
        },
        {
            "Field": "Device category confidence",
            "Plain English meaning": "How confident the system is that the device type is correct.",
            "Example": "High, Medium, Low, Unknown",
            "How the demo uses it": "To reduce confidence if the device has not been clearly identified"
        },
        {
            "Field": "Customer impact score",
            "Plain English meaning": "A made-up severity score for the demo.",
            "Example": "1/10 low impact, 10/10 high impact",
            "How the demo uses it": "To demonstrate prioritisation"
        },
        {
            "Field": "Cost-to-assure risk",
            "Plain English meaning": "A made-up indication of whether the journey may lead to expensive support.",
            "Example": "Low, Medium, High",
            "How the demo uses it": "To show how cost could be considered before escalating"
        },
        {
            "Field": "Digital containment risk",
            "Plain English meaning": "A made-up indication of whether the customer may need advisor support.",
            "Example": "Low, Medium, High",
            "How the demo uses it": "To show likelihood of digital journey failure"
        }
    ])

    st.dataframe(telemetry_explainer, use_container_width=True, hide_index=True)

    st.subheader("How to explain this in one sentence")
    st.success(
        "The demo uses synthetic telemetry that mimics service health signals such as WiFi strength, packet loss, reconnects, telemetry freshness, line health and journey history, so the agentic logic can reason before choosing the next best action."
    )

# ============================================================
# AUDIT LOG
# ============================================================

with tab7:
    st.header("Demo audit log")

    if st.button("Log this diagnostic run"):
        st.session_state.audit_log.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scenario": selected_scenario,
            "product": telemetry["product"],
            "device_type": telemetry["device_type"],
            "connection_method": telemetry["connection_method"],
            "hub_model": telemetry["hub_model"],
            "symptom": telemetry["customer_symptom"],
            "overall_rag": result["overall_rag"],
            "selected_hypothesis": result["selected_hypothesis"]["hypothesis"],
            "confidence": result["selected_hypothesis"]["confidence"],
            "customer_impact_score": telemetry["customer_impact_score"],
            "cost_to_assure_risk": telemetry["cost_to_assure_risk"],
            "digital_containment_risk": telemetry["digital_containment_risk"],
            "previous_outcome": telemetry["previous_outcome"],
            "action": result["action"]["action_type"],
            "approval_needed": result["action"]["requires_approval"]
        })

    if st.session_state.audit_log:
        log_df = pd.DataFrame(st.session_state.audit_log)
        st.dataframe(log_df, use_container_width=True, hide_index=True)
    else:
        st.info("No diagnostic runs logged yet.")

st.divider()

st.caption(
    "Prototype only. Uses synthetic telemetry and demo thresholds. "
    "Do not use real customer data, sensitive data, privileged content, internal documents, or unmanaged telemetry in this demo."
)

