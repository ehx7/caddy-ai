# sample data
import streamlit as st
import pandas as pd
import numpy as np



def session_history():
    st.title("Session History")

    if st.session_state.sessions:
        session_data = []
        for i, seconds in enumerate(st.session_state.sessions, 1):
            h, r = divmod(seconds, 3600)
            m, s = divmod(r, 60)
            session_data.append({
                "Session": f"Session {i}",
                "Duration": f"{h:02}:{m:02}:{s:02}"
            })

        df = pd.DataFrame(session_data)
        st.table(df)
    else:
        st.info("No sessions recorded yet.")




df = pd.DataFrame({
    'Session #': ['A', 'B', 'C'],
    'Wave1': [1.2, 0.5, 0.9],
    'Wave2': [100, 200, 150]
})

st.title("Previous Sessions")
st.write("Data:")
st.dataframe(df)


progress_bar = st.sidebar.progress(0)
status_text = st.sidebar.empty()
last_rows = np.random.randn(1, 1)
chart = st.line_chart(last_rows)

for i in range(1, 10):
    new_rows = last_rows[-1, :] + np.random.randn(5, 1).cumsum(axis=0)
    status_text.text("%i%% Complete" % i)
    chart.add_rows(new_rows)
    progress_bar.progress(i)
    last_rows = new_rows

progress_bar.empty()

st.button("Re-run")