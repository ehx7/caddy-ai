import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time
import random
from datetime import datetime, timedelta
import pandas as pd
from focus import get_mindfulness_score, setup_board

# 🔧 Set up page and refresh
st.set_page_config(page_title="Caddy.ai", layout="centered")
st_autorefresh(interval=1000, key="focus_refresh")

# 🧠 Session state setup
if "putt_log" not in st.session_state:
    st.session_state.putt_log = []
if "focus_log" not in st.session_state:
    st.session_state.focus_log = []
if "visible_focus_log" not in st.session_state:
    st.session_state.visible_focus_log = []

# 📊 Simulate focus score + timestamp
# focus_score = round(random.uniform(1.5, 4.5), 2)
#focus_score = get_mindfulness_score(data, eeg_channels, sampling_rate)



# Run tracking loop
if st.session_state.running:
    board, board_id, eeg_channels, sampling_rate = setup_board()
    
    window_duration = 10  # seconds of data per calculation
    refresh_interval = 5  # seconds between updates
    buffer_size = sampling_rate * window_duration

    st.success("Tracking started. Live mindfulness scores below.")

    try:
        while st.session_state.running:
            time.sleep(refresh_interval)
            data = board.get_current_board_data(buffer_size)
            score = get_mindfulness_score(data, eeg_channels, sampling_rate)
            focus_score = score
            st.session_state.scores.append(score)
            #score_chart.add_rows([[score]])
            st.write(f"Latest Mindfulness Score: **{score:.2f}**")
            #st.write(score)

    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        board.stop_stream()
        board.release_session()
        st.success("Tracking stopped.")


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