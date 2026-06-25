import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# ----- Synthetic scenarios -----
SCENARIOS = {
    "Healthy connection": { ... },  # (Use your full scenario dictionary here)
    "Buffering on streaming device": { ... }
}

# ----- Helper functions -----

def safe_value(value, suffix=""):
    return "Not available" if value is None else f"{value}{suffix}"

def rag_badge(rag):
    return {"Green":"🟢 Green","Amber":"🟠 Amber","Red":"🔴 Red","Grey":"⚪ Grey"}.get(rag, rag)

# Add all your calculate_*_rag, build_marker_results, rollup_rag...
# build_hypotheses, choose_best_hypothesis and decide_action functions here exactly as in your working code.

def randomise_scenario(base):
    t = base.copy()
    # ... (your randomisation logic here)
    return t

def generate_synthetic_history(scenario_key):
    base = SCENARIOS[scenario_key]
    history = []
    now = datetime.now()
    for i in range(10):
        timestamp = now - timedelta(hours=10 - i)
        # Apply jitter for synthetic history values
        # ...
    return history

def plot_trends(history):
    df = pd.DataFrame(history).set_index('timestamp')
    st.line_chart(df[['rssi','packet_loss','retransmission_rate','rapid_reconnects']])
    return df

def summarize_trends(df):
    # ... (your summarize_trends function with .iloc indexing)
    return "Summary text"

def build_detailed_customer_message(t, markers, action):
    # Combine markers+action into a customer-friendly explanation
    return "Customer friendly explanation"

def build_detailed_advisor_message(t, markers, action, hyps):
    # Combine detailed markers, hypotheses and recommendations for advisor
    return "Advisor detailed explanation"

def run_agentic_test(t, scenario_key):
    # Performs full diagnostic logic, returns all needed detail (including explainers and history)
    return {
        "marker_results": [],
        "overall_rag": "Green",
        "hypotheses": [],
        "chosen": {},
        "action": {},
        "detailed_customer_message": "",
        "detailed_advisor_message": "",
        "diagnostic_trace_text": "",
        "history": []
    }


# ----- Streamlit UI -----

if 'result' not in st.session_state:
    st.session_state.result = None
if 'telemetry' not in st.session_state:
    st.session_state.telemetry = None
if 'scenario_used' not in st.session_state:
    st.session_state.scenario_used = None

st.title("🛰️ Test SC Agentic AI Demo")

random_mode = st.sidebar.checkbox("Random scenario every test", True)
selected_scenario = st.sidebar.selectbox("Or pick scenario", list(SCENARIOS.keys()))

if st.button("🚀 Test my connection"):
    scenario = random.choice(list(SCENARIOS.keys())) if random_mode else selected_scenario
    telemetry = randomise_scenario(SCENARIOS[scenario])
    st.session_state.telemetry = telemetry
    st.session_state.scenario_used = scenario
    st.session_state.result = run_agentic_test(telemetry, scenario)

if st.session_state.result:
    result = st.session_state.result
    action = result['action']
    telemetry = st.session_state.telemetry

    cols = st.columns(5)
    cols[0].metric("Overall Status", rag_badge(result["overall_rag"]))
    cols[1].metric("Outcome", action["Outcome"])
    cols[2].metric("Confidence", result["chosen"].get("Confidence", "N/A"))
    cols[3].metric("Risk", action.get("Risk", "N/A"))
    cols[4].metric("Next Step Type", action.get("Agentic_level", "N/A"))

    # Tabs for organized views
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
            # ... add all telemetry fields here ...
        ]
        st.table(pd.DataFrame(telemetry_info).set_index("Field"))

    with tab2:
        st.header("Agentic AI Reasoning")
        st.text_area("Diagnostic Narrative", result["diagnostic_trace_text"], height=250, disabled=True)
        st.subheader("Telemetry trends")
        df_hist = pd.DataFrame(result["history"]).set_index("timestamp")
        st.line_chart(df_hist[['rssi', 'packet_loss', 'retransmission_rate', 'rapid_reconnects']])
        st.info(summarize_trends(df_hist))

    with tab3:
        st.header("Marker Results")
        marker_df = pd.DataFrame(result["marker_results"])
        marker_df["RAG Status"] = marker_df["RAG"].apply(rag_badge)
        st.table(marker_df[['Marker', 'Value', 'RAG Status', 'Reason']])

    with tab4:
        st.header("Advisor View")
        advisor_summary = {
            "Field": ["Outcome", "Recommended Action", "Chosen Hypothesis", "Confidence Level", "Risk Level"],
            "Value": [
                action["Outcome"],
                action["Action"],
                result["chosen"].get("Hypothesis", "N/A"),
                result["chosen"].get("Confidence", "N/A"),
                action.get("Risk", "N/A"),
            ]
        }
        st.table(pd.DataFrame(advisor_summary))
        st.subheader("Hypotheses & Evidence")
        for h in result["hypotheses"]:
            st.markdown(f"**{h['Hypothesis']}** (Confidence: {h['Confidence']})")
            st.write(", ".join(h["Evidence"]))
            st.markdown("---")

    with tab5:
        st.header("Customer View")
        customer_advice_map = {
            # Map outcomes to user-friendly advice
            "Weak WiFi signal": "Try moving your device closer to your router or WiFi booster.",
            "WiFi interference detected": "Optimize your WiFi setup by reducing interference or changing channels.",
            # ... add more mappings ...
        }
        advice = customer_advice_map.get(action["Outcome"], action.get("Customer_message", ""))
        st.success(advice)
        st.markdown(f"**Next step:** {action.get('Action', '')}")

else:
    st.info("Click 'Test my connection' to run the diagnostic.")


