import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# Define summarize_trends FIRST so it's available when called
def summarize_trends(df):
    summaries = []
    # Use .iloc to access by position rather than label (to avoid KeyErrors)
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

# Minimal synthetic telemetry history generator
def generate_synthetic_history():
    now = datetime.now()
    history = []
    base_values = {"rssi": -60, "packet_loss": 1.0, "retransmission_rate": 5.0, "rapid_reconnects": 1}
    for i in range(10):
        timestamp = now - timedelta(hours=10 - i)
        history.append({
            "timestamp": timestamp,
            "rssi": base_values["rssi"] + random.uniform(-5,5),
            "packet_loss": base_values["packet_loss"] + random.uniform(-0.5,0.5),
            "retransmission_rate": base_values["retransmission_rate"] + random.uniform(-2,2),
            "rapid_reconnects": int(base_values["rapid_reconnects"] + random.randint(-1,1))
        })
    return pd.DataFrame(history).set_index('timestamp')

st.title("Connection Test Demo")

if st.button("Run test"):
    df = generate_synthetic_history()
    st.line_chart(df)
    summary = summarize_trends(df)
    st.info(summary)
else:
    st.info("Click 'Run test' to generate telemetry trends and summary.")

