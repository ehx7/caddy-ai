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

# 🧠 Session state setup
if "putt_log" not in st.session_state:
    st.session_state.putt_log = []
if "focus_log" not in st.session_state:
    st.session_state.focus_log = []
if "visible_focus_log" not in st.session_state:
    st.session_state.visible_focus_log = []

# 📊 Simulate focus score + timestamp
focus_score = round(random.uniform(1.5, 4.5), 2)
timestamp = datetime.now().isoformat()

# Log every score internally
st.session_state.focus_log.append({
    "timestamp": timestamp,
    "focus": focus_score
})

# Log only displayed scores to separate list
st.session_state.visible_focus_log.append({
    "timestamp": timestamp,
    "focus": focus_score
})

# 🧠 UI display
st.title("⛳ Caddy.ai – Live Focus Score + Shot Logger")
st.metric("🧠 Focus Score", focus_score)
st.session_state.latest_focus = focus_score

if focus_score < 2.2:
    st.error("🔴 Nudge Triggered: Take a Breath")
else:
    st.success("🟢 Focus is Stable")

# 🖱️ Putt logging buttons
col1, col2 = st.columns(2)

def log_putt(result_label):
    putt_time = datetime.now()

    # Last putt time or fallback to session start
    if st.session_state.putt_log:
        last_putt_time = datetime.fromisoformat(st.session_state.putt_log[-1]["timestamp"])
    else:
        last_putt_time = datetime.fromisoformat(st.session_state.focus_log[0]["timestamp"])

    # ✅ NEW: Only check visible (displayed) values for nudge logic
    nudge_during_window = any(
        last_putt_time <= datetime.fromisoformat(entry["timestamp"]) <= putt_time
        and entry["focus"] < 2.2
        for entry in st.session_state.visible_focus_log
    )

    # ⏱ Check last 10 seconds for low focus
    ten_sec_window = putt_time - timedelta(seconds=10)
    low_focus_last_10s = any(
        datetime.fromisoformat(entry["timestamp"]) >= ten_sec_window and entry["focus"] < 2.2
        for entry in st.session_state.focus_log
    )

    # 🧠 Check if most recent score before putt was low
    last_focus_entry = None
    for entry in reversed(st.session_state.focus_log):
        if datetime.fromisoformat(entry["timestamp"]) < putt_time:
            last_focus_entry = entry
            break
    low_focus_last = last_focus_entry is not None and last_focus_entry["focus"] < 2.2

    # 📝 Log it
    st.session_state.putt_log.append({
        "timestamp": putt_time.isoformat(),
        "focus": focus_score,
        "result": result_label,
        "nudge": nudge_during_window,
        "low_focus_last_10s": low_focus_last_10s,
        "low_focus_last": low_focus_last
    })

if col1.button("✅ Made Putt"):
    log_putt("made")

if col2.button("❌ Missed Putt"):
    log_putt("miss")

# 📋 Show shot log
st.subheader("🗃️ Shot Log")
if st.session_state.putt_log:
    df = pd.DataFrame(st.session_state.putt_log)
    st.dataframe(df)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", csv, "putt_log.csv", "text/csv")
else:
    st.info("No shots logged yet.")
