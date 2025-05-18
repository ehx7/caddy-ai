import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import random
import altair as alt

# Auto-refresh every second
st_autorefresh(interval=2000, key="focus_refresh")

# --- Initialize session state ---
if "start" not in st.session_state:
    st.session_state.start = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "history" not in st.session_state:
    st.session_state.history = []
if "focus_log" not in st.session_state:
    st.session_state.focus_log = []
if "putt_log" not in st.session_state:
    st.session_state.putt_log = []
if "visible_focus_log" not in st.session_state:
    st.session_state.visible_focus_log = []
if "latest_focus" not in st.session_state:
    st.session_state.latest_focus = None
if "session_summary" not in st.session_state:
    st.session_state.session_summary = None

# --- Timer display ---
def show_timer():
    if st.session_state.start and st.session_state.start_time:
        elapsed = int(time.time() - st.session_state.start_time)
        h, r = divmod(elapsed, 3600)
        m, s = divmod(r, 60)
        st.write(f"⏱️ Elapsed Time: {h:02}:{m:02}:{s:02}")

# --- Log Putt Function ---
def log_putt(result_label):
    putt_time = datetime.now()
    last_putt_time = datetime.fromisoformat(st.session_state.putt_log[-1]["timestamp"]) if st.session_state.putt_log else datetime.fromisoformat(st.session_state.focus_log[0]["timestamp"])

    # Nudge occurred between last putt and now
    nudge_during_window = any(
        last_putt_time <= datetime.fromisoformat(entry["timestamp"]) <= putt_time and entry["focus"] < 2.2
        for entry in st.session_state.visible_focus_log
    )

    # Any low focus in last 10s
    ten_sec_window = putt_time - timedelta(seconds=10)
    low_focus_last_10s = any(
        datetime.fromisoformat(entry["timestamp"]) >= ten_sec_window and entry["focus"] < 2.2
        for entry in st.session_state.focus_log
    )

    # Was the last focus entry before this one also low?
    last_focus_entry = next(
        (entry for entry in reversed(st.session_state.focus_log)
         if datetime.fromisoformat(entry["timestamp"]) < putt_time), None
    )
    low_focus_last = last_focus_entry is not None and last_focus_entry["focus"] < 2.2

    # Log it
    st.session_state.putt_log.append({
        "timestamp": putt_time.isoformat(),
        "focus": st.session_state.latest_focus,
        "result": result_label,
        "nudge": nudge_during_window,
        "low_focus_last_10s": low_focus_last_10s,
        "low_focus_last": low_focus_last
    })

# --- Start/End Session Toggle ---
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
            elapsed = int(end_time - st.session_state.start_time)
            duration = str(timedelta(seconds=elapsed))

            session_data = {
                "start": datetime.fromtimestamp(st.session_state.start_time).strftime("%Y-%m-%d %H:%M:%S"),
                "end": datetime.fromtimestamp(end_time).strftime("%Y-%m-%d %H:%M:%S"),
                "duration": duration,
                "focus_log": st.session_state.focus_log.copy(),
                "putt_log": st.session_state.putt_log.copy(),
            }

            st.session_state.history.append(session_data)
            st.session_state.session_summary = session_data
            st.session_state.start_time = None
        st.rerun()


# --- Pages ---
def home():
    st.title("⛳ Caddy.ai")
    st.write("Welcome to the Focus Timer")
    toggle_session()
    show_timer()

    if st.session_state.start:
        # Simulate a focus score
        focus_score = round(random.uniform(1.5, 4.5), 2)
        timestamp = datetime.now().isoformat()
        st.session_state.latest_focus = focus_score
        st.metric("🧠 Focus Score", focus_score)

        st.session_state.focus_log.append({"timestamp": timestamp, "focus": focus_score})
        st.session_state.visible_focus_log.append({"timestamp": timestamp, "focus": focus_score})

        # Display nudges
        if focus_score < 2.2:
            st.error("🔴 Nudge Triggered: Take a Breath")
        else:
            st.success("🟢 Focus is Stable")

        # --- Focus Trend Chart with Annotations ---
        st.subheader("📈 Focus Trend")
        if len(st.session_state.focus_log) > 1:
            focus_df = pd.DataFrame(st.session_state.focus_log)
            focus_df["timestamp"] = pd.to_datetime(focus_df["timestamp"])
            focus_df["event"] = ""
            focus_df["color"] = "purple"

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

        # --- Putt Logging ---
        col1, col2 = st.columns(2)
        if col1.button("✅ Made Putt"):
            log_putt("made")
        if col2.button("❌ Missed Putt"):
            log_putt("miss")

        # --- Putt Log Display ---
        st.subheader("Shot Log")
        if st.session_state.putt_log:
            df = pd.DataFrame(st.session_state.putt_log)
            st.dataframe(df)
            #csv = df.to_csv(index=False).encode("utf-8")
            #st.download_button("📥 Download CSV", csv, "putt_log.csv", "text/csv")
        else:
            st.info("No shots logged yet.")

    elif st.session_state.session_summary:
        st.markdown("---")
        st.subheader("🧾 Session Summary")
        summary = st.session_state.session_summary
        st.write(f"**Start:** {summary['start']}")
        st.write(f"**End:** {summary['end']}")
        st.write(f"**Duration:** {summary['duration']}")
        st.write("**Focus Readings:**", len(summary["focus_log"]))
        st.write("**Putts:**", len(summary["putt_log"]))

def session_page():
    st.title("Session Recap")
    if not st.session_state.history:
            st.info("No putts have been logged yet.")


    if not st.session_state.start and st.session_state.start_time is None and st.session_state.focus_log:

        # 1. Putt Outcomes Pie Chart
        st.subheader("🏌️‍♂️ Putt Outcomes")
        if st.session_state.putt_log:
            putt_df = pd.DataFrame(st.session_state.putt_log)
            pie_data = putt_df["result"].value_counts().reset_index()
            pie_data.columns = ["Result", "Count"]
            st.altair_chart(
                alt.Chart(pie_data).mark_arc().encode(
                    theta=alt.Theta(field="Count", type="quantitative"),
                    color=alt.Color(field="Result", type="nominal"),
                    tooltip=["Result", "Count"]
                ),
                use_container_width=True
            )
        

        # 2. Nudges Count
        st.markdown("---")
        st.subheader("⚠️ Nudges Triggered")
        nudge_count = sum(p["nudge"] for p in st.session_state.putt_log)
        st.metric("Total Nudges", nudge_count)

        # 3. Focus Score Distribution Histogram
        st.subheader("📶 Focus Score Distribution")
        focus_df = pd.DataFrame(st.session_state.focus_log)
        st.altair_chart(
            alt.Chart(focus_df).mark_bar().encode(
                alt.X("focus:Q", bin=True, title="Focus Score"),
                y='count()',
            ),
            use_container_width=True
        )

        # 4. Session Duration Summary
        if st.session_state.history:
            st.markdown("---")
            last_session = st.session_state.history[-1]
            st.subheader("⏱️ Session Duration")
            st.write(f"Start: {last_session['start']}\n\nEnd: {last_session['end']}\n\nDuration: {last_session['duration']}")

        

def history_page():
    st.title("📜 Session History")

    if not st.session_state.history:
        st.info("No sessions recorded yet.")
    else:
        for i, session in enumerate(reversed(st.session_state.history), 1):
            with st.expander(f"Session {len(st.session_state.history) - i + 1} | {session['start']} → {session['end']}"):
                st.write(f"**Duration:** {session['duration']}")
                st.write(f"**Focus Logs:** {len(session['focus_log'])}")
                st.write(f"**Putts:** {len(session['putt_log'])}")

                if session["focus_log"]:
                    st.write("Focus Log")
                    st.dataframe(pd.DataFrame(session["focus_log"]))

                if session["putt_log"]:
                    st.write("Putt Log")
                    st.dataframe(pd.DataFrame(session["putt_log"]))

        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.session_state.focus_log = []
            st.session_state.putt_log = []
            st.session_state.visible_focus_log = []
            st.session_state.session_summary = None
            st.success("Session history cleared.")
            st.rerun()


# --- Navigation ---
st.sidebar.title("🏌️‍♂️ Navigation")
selected_page = st.sidebar.radio("Go to", ["Home", "Most Recent Session", "History"])

if selected_page == "Home":
    home()
elif selected_page == "Most Recent Session":
    session_page()
elif selected_page == "History":
    history_page()
