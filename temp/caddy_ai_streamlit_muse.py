import streamlit as st
from streamlit_autorefresh import st_autorefresh
from pylsl import StreamInlet, resolve_byprop
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time
import altair as alt

# Set page config and refresh
st.set_page_config(page_title="Caddy.ai + Muse 2", layout="centered")
st_autorefresh(interval=4000, key="focus_refresh")  # Refresh every 2 seconds

# Session state initialization
if "putt_log" not in st.session_state:
    st.session_state.putt_log = []
if "focus_log" not in st.session_state:
    st.session_state.focus_log = []
if "visible_focus_log" not in st.session_state:
    st.session_state.visible_focus_log = []
if "latest_focus" not in st.session_state:
    st.session_state.latest_focus = 3.0

# Connect to Muse LSL EEG stream (once per session)
if "inlet" not in st.session_state:
    st.write("🔌 Connecting to Muse EEG stream...")
    streams = resolve_byprop("type", "EEG", timeout=10)
    if not streams:
        st.error("No EEG stream found. Please run 'muselsl stream' in a terminal.")
        st.stop()
    st.session_state.inlet = StreamInlet(streams[0])
    st.success("✅ Connected to Muse EEG stream.")

inlet = st.session_state.inlet

# Calibration block (non-blocking)
if "calibrated" not in st.session_state:
    st.session_state.calibrated = False
    st.session_state.calibration_powers = []
    st.session_state.calibration_steps = 0

if not st.session_state.calibrated:
    st.title("🧘 Calibration In Progress")
    st.info(f"Step {st.session_state.calibration_steps + 1} of 6 – Please sit still...")

    eeg_window = [[], [], [], []]
    collected = 0
    while collected < 256:
        sample, _ = inlet.pull_sample(timeout=0.1)
        if sample and len(sample) >= 4:
            for i in range(4):
                eeg_window[i].append(sample[i])
            collected += 1

    eeg_data = np.array(eeg_window)
    powers = np.mean(np.square(eeg_data), axis=1)
    avg_power = np.mean(powers)

    st.session_state.calibration_powers.append(avg_power)
    st.session_state.calibration_steps += 1

    if st.session_state.calibration_steps >= 6:
        baseline = np.median(st.session_state.calibration_powers)
        spread = np.std(st.session_state.calibration_powers)
        st.session_state.focus_min = baseline + spread * 2
        st.session_state.focus_max = max(1000.0, baseline - spread * 2)
        st.session_state.calibrated = True
        st.rerun()
    else:
        st.stop()

def get_focus_score():
    eeg_window = [[], [], [], []]  # 4 Muse channels
    samples_needed = 256

    start_time = time.time()
    while len(eeg_window[0]) < samples_needed:
        if time.time() - start_time > 10:
            print("⚠️ Timeout while collecting EEG samples.")
            return st.session_state.latest_focus

        sample, _ = inlet.pull_sample(timeout=1.0)
        if sample and len(sample) >= 4:
            for i in range(4):  # TP9, AF7, AF8, TP10
                eeg_window[i].append(sample[i])

    eeg_data = np.array(eeg_window)
    powers = np.mean(np.square(eeg_data), axis=1)
    avg_power = np.mean(powers)

    focus_min = st.session_state.get("focus_min", 15000)
    focus_max = st.session_state.get("focus_max", 3000)
    power_clipped = np.clip(avg_power, focus_max, focus_min)
    normalized = 10 - ((power_clipped - focus_max) / (focus_min - focus_max)) * 9.0
    score = round(min(max(1.0, normalized), 10.0), 2)

    print(f"EEG Power (µV²): {avg_power:.2f} → Focus Score: {score}")
    return score

# Only run main app logic if calibration is complete
if not st.session_state.calibrated:
    st.stop()

# Always update focus score on refresh (every 4 seconds)
focus_score = get_focus_score()
timestamp = datetime.now().isoformat()
st.session_state.latest_focus = focus_score
st.session_state.focus_log.append({"timestamp": timestamp, "focus": focus_score})
st.session_state.visible_focus_log.append({"timestamp": timestamp, "focus": focus_score})

# UI
st.title("⛳ Caddy.ai – Live Focus from Muse 2")
st.metric("🧠 Focus Score", focus_score)
if focus_score < 3.5:
    st.error("🔴 Nudge Triggered: Take a Breath")
else:
    st.success("🟢 Focus is Stable")

# Real-time focus score trend with annotations
st.subheader("📈 Focus Trend")
if len(st.session_state.focus_log) > 1:
    focus_df = pd.DataFrame(st.session_state.focus_log)
    focus_df["timestamp"] = pd.to_datetime(focus_df["timestamp"])
    focus_df["event"] = ""
    focus_df["color"] = "blue"

    for putt in st.session_state.putt_log:
        t = pd.to_datetime(putt["timestamp"])
        closest_idx = focus_df["timestamp"].sub(t).abs().idxmin()
        if putt["nudge"]:
            focus_df.loc[closest_idx, ["event", "color"]] = ["Nudge", "yellow"]
        elif putt["result"] == "made":
            focus_df.loc[closest_idx, ["event", "color"]] = ["Made", "green"]
        elif putt["result"] == "miss":
            focus_df.loc[closest_idx, ["event", "color"]] = ["Miss", "red"]

    base = alt.Chart(focus_df).mark_line().encode(
        x="timestamp:T",
        y="focus:Q"
    )

    points = alt.Chart(focus_df).mark_circle(size=60).encode(
        x="timestamp:T",
        y="focus:Q",
        color=alt.Color("color", scale=None),
        tooltip=["timestamp:T", "focus:Q", "event"]
    ).transform_filter("datum.event != ''")

    st.altair_chart(base + points, use_container_width=True)
else:
    st.info("Focus trend will appear after a few updates.")

# Putt logging
col1, col2 = st.columns(2)

def log_putt(result_label):
    putt_time = datetime.now()
    last_putt_time = datetime.fromisoformat(st.session_state.putt_log[-1]["timestamp"]) if st.session_state.putt_log else datetime.fromisoformat(st.session_state.focus_log[0]["timestamp"])

    nudge_during_window = any(
        last_putt_time <= datetime.fromisoformat(entry["timestamp"]) <= putt_time and entry["focus"] < 2.2
        for entry in st.session_state.visible_focus_log
    )

    ten_sec_window = putt_time - timedelta(seconds=10)
    low_focus_last_10s = any(
        datetime.fromisoformat(entry["timestamp"]) >= ten_sec_window and entry["focus"] < 2.2
        for entry in st.session_state.focus_log
    )

    last_focus_entry = next(
        (entry for entry in reversed(st.session_state.focus_log)
         if datetime.fromisoformat(entry["timestamp"]) < putt_time), None
    )
    low_focus_last = last_focus_entry is not None and last_focus_entry["focus"] < 2.2

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

# Display logged data
st.subheader("🗃️ Shot Log")
if st.session_state.putt_log:
    df = pd.DataFrame(st.session_state.putt_log)
    st.dataframe(df)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", csv, "putt_log.csv", "text/csv")
else:
    st.info("No shots logged yet.")

