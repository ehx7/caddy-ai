import streamlit as st
from streamlit_autorefresh import st_autorefresh
import random
import time
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt

st.title("Real-Time EEG Viewer")

# Load once, or reload each time if CSV is being updated
@st.cache_data(ttl=1.0)  # update every 1 sec
def load_data():
    return pd.read_csv("/workspaces/caddy-ai/current/downsampled_data.csv")

# Select channel
channel = st.selectbox("Choose EEG Channel", [f"Channel {i+1}" for i in range(8)])
channel_idx = int(channel.split()[-1]) - 1  # get index from label

# Main plotting loop
placeholder = st.empty()

for _ in range(100):  # or while True:
    df = load_data()
    y = df.iloc[:, channel_idx]  # EEG signal
    x = df.index  # time

    fig, ax = plt.subplots()
    ax.plot(x, y)
    ax.set_title(f"{channel} Signal")
    ax.set_xlabel("Time")
    ax.set_ylabel("Amplitude (uV)")
    ax.grid(True)

    placeholder.pyplot(fig)
    time.sleep(1)
# 🔧 Set up page and refresh

st_autorefresh(interval=1000, key="focus_refresh")
