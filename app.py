import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime, timedelta
import plotly.graph_objs as go

# ===============================
# Constants & Synthetic Telemetry
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
    # (More scenarios can be added here)
}

# ===============================
# HELPER FUNCTIONS (Original + Enhanced)
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

# Diagnostic RAG calculations
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
        return "Grey", "Telemetry is too old to support confident diagnosis"

def calculate_equipment_health_rag(equipment_health):
    if equipment_health == "OK":
        return "Green", "No suspected equipment fault"
    if equipment_health == "Suspected fault":
        return "Red", "Equipment fault suspected"
    return "Grey", "Equipment health is unknown"

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

    equipment_rag, equipment_reason = calculate_equipment_health_rag(t["equipment_health"])
    results.append({
        "Marker": "Equipment health",
        "Value": t["equipment_health"],
        "RAG": equipment_rag,
        "Reason": equipment_reason
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

# Hypotheses generation and choice (same as original)
def build_hypotheses(t, marker_results):
    lookup = {m["Marker"]: m for m in marker_results}
    hypotheses = []

    if t["known_outage"]:
        hypotheses.append({
            "Hypothesis": "Known wider service issue",
            "Evidence": [
                "Known outage flag is active",
                "Normal troubleshooting should be stopped",
                "Customer does not need engineer or replacement action from this journey"
            ],
            "Confidence": "High"
        })
        return hypotheses

    if lookup["Telemetry freshness"]["RAG"] == "Grey":
        hypotheses.append({
            "Hypothesis": "Test cannot complete because telemetry is missing or stale",
            "Evidence": [
                "Telemetry is too old or unavailable",
                "One or more markers are Grey"
            ],
            "Confidence": "High"
        })

    if lookup["Equipment health"]["RAG"] == "Red":
        hypotheses.append({
            "Hypothesis": "Equipment replacement may be required",
            "Evidence": [
                "Equipment health is flagged as suspected fault",
                "Issue has repeated after previous outcome",
                "Connection instability is present"
            ],
            "Confidence": "High"
        })

    if lookup["Line health"]["RAG"] == "Red":
        hypotheses.append({
            "Hypothesis": "Engineer visit may be required",
            "Evidence": [
                "Line health is Red",
                "Customer symptom indicates loss, drops or instability",
                "Issue may not be fixable through self-serve steps"
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
                "Line health is OK",
                "No equipment fault suspected"
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
            "Outcome": "Known outage detected",
            "Action": "No action needed from the customer. We’ll keep the customer updated while the issue is fixed.",
            "Customer_message": "There is a known issue affecting the service. The customer does not need to do anything right now — the issue is already being worked on.",
            "Advisor_message": "Known outage path. Do not send engineer or offer replacement from this journey.",
            "Agentic_level": "Suppress normal troubleshooting",
            "Risk": "Low"
        }

    if "Test cannot complete" in h:
        return {
            "Outcome": "Test could not complete",
            "Action": "Ask the customer to run the test again. If it fails again, route to advisor support.",
            "Customer_message": "The test could not complete because some connection information was missing or out of date. Please try the test again.",
            "Advisor_message": "Telemetry missing or stale. Do not make a firm diagnosis from this run.",
            "Agentic_level": "Retry / gather evidence",
            "Risk": "Low"
        }

    if "Equipment replacement" in h:
        return {
            "Outcome": "Replacement recommended",
            "Action": "Offer replacement equipment.",
            "Customer_message": "The test found signs that the equipment may be causing the issue. The next step is to arrange a replacement.",
            "Advisor_message": "Equipment fault suspected. Replacement route recommended if eligibility checks pass.",
            "Agentic_level": "Recommend replacement",
            "Risk": "Medium"
        }

    if "Engineer visit" in h:
        return {
            "Outcome": "Engineer visit required",
            "Action": "Book an engineer visit.",
            "Customer_message": "The test found an issue that is unlikely to be fixed by simple self-serve steps. The next step is to book an engineer.",
            "Advisor_message": "Line/network evidence indicates engineer route. Do not loop the customer through repeated WiFi self-serve steps.",
            "Agentic_level": "Escalate to engineer",
            "Risk": "Medium"
        }

    if "Poor WiFi signal" in h:
        if t["pod_present"]:
            next_step = "Move closer to the hub or pod, then test again."

