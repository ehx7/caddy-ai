import streamlit as st
import time
import random
from datetime import datetime, timedelta
import pandas as pd



# 🧠 Session state setup
for key in ["putt_log", "focus_log", "visible_focus_log", "latest_focus"]:
    if key not in st.session_state:
        st.session_state[key] = [] if "log" in key else None

# 📊 Simulate focus score + timestamp
focus_score = round(random.uniform(1.5, 4.5), 2)
timestamp = datetime.now().isoformat()

# Avoid duplicates during reruns
if not st.session_state.focus_log or st.session_state.focus_log[-1]["timestamp"] != timestamp:
    # Log every score
    st.session_state.focus_log.append({
        "timestamp": timestamp,
        "focus": focus_score
    })

    # Log visible scores
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

    # Last putt time fallback
    if st.session_state.putt_log:
        last_putt_time = datetime.fromisoformat(st.session_state.putt_log[-1]["timestamp"])
    elif st.session_state.focus_log:
        last_putt_time = datetime.fromisoformat(st.session_state.focus_log[0]["timestamp"])
    else:
        last_putt_time = putt_time - timedelta(seconds=10)  # fallback
