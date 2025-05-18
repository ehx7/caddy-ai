import streamlit as st
from streamlit_autorefresh import st_autorefresh
from pylsl import StreamInlet, resolve_byprop
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time
import altair as alt
import random


st.set_page_config(page_title="Caddy.ai + Muse 2", layout="centered")
st_autorefresh(interval=2000, key="focus_refresh")


# --- Session state init ---
default_states = {
   "start": False,
   "start_time": None,
   "history": [],
   "focus_log": [],
   "putt_log": [],
   "visible_focus_log": [],
   "session_summary": None,
   "latest_focus": 3.0,
   "calibrated": False,
   "calibration_powers": [],
   "calibration_steps": 0,
}
for key, val in default_states.items():
   if key not in st.session_state:
       st.session_state[key] = val


# --- Muse Connection ---
if "inlet" not in st.session_state:
   st.write("🔌 Connecting to Muse EEG stream...")
   streams = resolve_byprop("type", "EEG", timeout=10)
   if not streams:
       st.error("No EEG stream found. Please run 'muselsl stream' in a terminal.")
       st.stop()
   st.session_state.inlet = StreamInlet(streams[0])
   st.success("✅ Connected to Muse EEG stream.")
inlet = st.session_state.inlet


# --- Calibration ---
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
   avg_power = np.mean(np.mean(np.square(eeg_data), axis=1))


   st.session_state.calibration_powers.append(avg_power)
   st.session_state.calibration_steps += 1


   if st.session_state.calibration_steps >= 6:
       baseline = np.median(st.session_state.calibration_powers)
       spread = np.std(st.session_state.calibration_powers)
       st.session_state.focus_min = baseline + spread * 2
       st.session_state.focus_max = max(1000.0, baseline - spread * 2)
       st.session_state.calibrated = True
       st.experimental_rerun()
   else:
       st.stop()


# --- Get Focus Score ---
def get_focus_score():
   eeg_window = [[], [], [], []]
   samples_needed = 256
   start_time = time.time()


   while len(eeg_window[0]) < samples_needed:
       if time.time() - start_time > 10:
           return st.session_state.latest_focus
       sample, _ = inlet.pull_sample(timeout=1.0)
       if sample and len(sample) >= 4:
           for i in range(4):
               eeg_window[i].append(sample[i])


   eeg_data = np.array(eeg_window)
   avg_power = np.mean(np.mean(np.square(eeg_data), axis=1))


   focus_min = st.session_state.get("focus_min", 15000)
   focus_max = st.session_state.get("focus_max", 3000)
   power_clipped = np.clip(avg_power, focus_max, focus_min)
   normalized = 10 - ((power_clipped - focus_max) / (focus_min - focus_max)) * 9.0
   score = round(min(max(1.0, normalized), 10.0), 2)
   return score


# --- Always update the focus score ---
focus_score = get_focus_score()
st.session_state.latest_focus = focus_score


if st.session_state.start:
   timestamp = datetime.now().isoformat()
   st.session_state.focus_log.append({"timestamp": timestamp, "focus": focus_score})
   st.session_state.visible_focus_log.append({"timestamp": timestamp, "focus": focus_score})


# --- Timer Display ---
def show_timer():
   if st.session_state.start and st.session_state.start_time:
       elapsed = int(time.time() - st.session_state.start_time)
       h, r = divmod(elapsed, 3600)
       m, s = divmod(r, 60)
       st.write(f"⏱️ Elapsed Time: {h:02}:{m:02}:{s:02}")


# --- Log Putt ---
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


# --- Toggle Session ---
def toggle_session():
   if st.button("Start" if not st.session_state.start else "End"):
       st.session_state.start = not st.session_state.start
       if st.session_state.start:
           st.session_state.start_time = time.time()
           st.session_state.focus_log = []
           st.session_state.putt_log = []
           st.session_state.visible_focus_log = []
           st.session_state.session_summary = None
       else:
           end_time = time.time()
           duration = str(timedelta(seconds=int(end_time - st.session_state.start_time)))
           st.session_state.session_summary = {
               "start": datetime.fromtimestamp(st.session_state.start_time).strftime("%Y-%m-%d %H:%M:%S"),
               "end": datetime.fromtimestamp(end_time).strftime("%Y-%m-%d %H:%M:%S"),
               "duration": duration,
               "focus_log": st.session_state.focus_log.copy(),
               "putt_log": st.session_state.putt_log.copy(),
           }
           st.session_state.history.append(st.session_state.session_summary)
           st.session_state.start_time = None
       st.rerun()


# --- Draw Focus Trend ---
def draw_focus_trend(focus_log, putt_log):
   if len(focus_log) < 2:
       st.info("Focus trend will appear after a few updates.")
       return


   df = pd.DataFrame(focus_log)
   df["timestamp"] = pd.to_datetime(df["timestamp"])
   df["event"] = ""
   df["color"] = "blue"


   for putt in putt_log:
       t = pd.to_datetime(putt["timestamp"])
       idx = df["timestamp"].sub(t).abs().idxmin()
       if putt["nudge"]:
           df.loc[idx, ["event", "color"]] = ["Nudge", "yellow"]
       elif putt["result"] == "made":
           df.loc[idx, ["event", "color"]] = ["Made", "green"]
       elif putt["result"] == "miss":
           df.loc[idx, ["event", "color"]] = ["Miss", "red"]


   base = alt.Chart(df).mark_line().encode(x="timestamp:T", y="focus:Q")
   points = alt.Chart(df).mark_circle(size=60).encode(
       x="timestamp:T", y="focus:Q", color=alt.Color("color", scale=None),
       tooltip=["timestamp:T", "focus:Q", "event"]
   ).transform_filter("datum.event != ''")


   st.altair_chart(base + points, use_container_width=True)


# --- Pages ---
def home():
   st.title("⛳ Caddy.ai")
   toggle_session()
   show_timer()
   st.metric("🧠 Focus Score", focus_score)
   if focus_score < 2.2:
       st.error("🔴 Nudge Triggered: Take a Breath")
   else:
       st.success("🟢 Focus is Stable")
   draw_focus_trend(st.session_state.focus_log, st.session_state.putt_log)


   col1, col2 = st.columns(2)
   if col1.button("✅ Made Putt"):
       log_putt("made")
   if col2.button("❌ Missed Putt"):
       log_putt("miss")


   st.subheader("🗃️ Shot Log")
   if st.session_state.putt_log:
       st.dataframe(pd.DataFrame(st.session_state.putt_log))
   else:
       st.info("No putts logged yet.")


def session_page():
   st.title("🧾 Most Recent Session")
   if not st.session_state.session_summary:
       st.info("No session completed yet.")
       return
   summary = st.session_state.session_summary
   st.write(f"**Start:** {summary['start']}")
   st.write(f"**End:** {summary['end']}")
   st.write(f"**Duration:** {summary['duration']}")
   st.write("**Focus Readings:**", len(summary["focus_log"]))
   st.write("**Putts:**", len(summary["putt_log"]))
   draw_focus_trend(summary["focus_log"], summary["putt_log"])


def history_page():
   st.title("📜 Session History")
   if not st.session_state.history:
       st.info("No sessions recorded yet.")
       return


   for i, session in enumerate(reversed(st.session_state.history), 1):
       with st.expander(f"Session {len(st.session_state.history) - i + 1} | {session['start']} → {session['end']}"):
           st.write(f"**Duration:** {session['duration']}")
           st.write(f"**Focus Logs:** {len(session['focus_log'])}")
           st.write(f"**Putts:** {len(session['putt_log'])}")
           draw_focus_trend(session["focus_log"], session["putt_log"])


   if st.button("🗑️ Clear History"):
       for key in ["history", "focus_log", "putt_log", "visible_focus_log", "session_summary"]:
           st.session_state[key] = []
       st.success("Session history cleared.")
       st.rerun()


# --- Navigation ---
st.sidebar.title("🏌️‍♂️ Navigation")
page = st.sidebar.radio("Go to", ["Home", "Most Recent Session", "History"])


if page == "Home":
   home()
elif page == "Most Recent Session":
   session_page()
elif page == "History":
   history_page()



