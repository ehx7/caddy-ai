import streamlit as st
import pandas as pd
import numpy as np
import altair as alt


if "start" not in st.session_state:
    st.session_state.start = False

def login_logout():
    if not st.session_state.start:
        if st.button("Start"):
            st.session_state.start = True
            st.rerun()
    else:
        st.success("Session is active.")
        if st.button("End"):
            st.session_state.start = False
            st.rerun()

dash = st.Page(login_logout, title="Start", icon=":material/login:")
# end_page = st.Page(logout, title="End", icon=":material/logout:")

dashboard = st.Page(
    "current/eegplot.py", title="Dashboard", icon=":material/dashboard:")
plots = st.Page("current/plots.py", title="Plots", icon=":material/clock_loader_20:")

search = st.Page("history/search.py", title="Search", icon=":material/search:")
history = st.Page("history/history.py", title="History", icon=":material/history:")


if st.session_state.start:
    pg = st.navigation(
        {
            "Account": [dash],
            "Reports": [dashboard, plots],
            "Tools": [search, history],
        }
    )
else:
    pg = st.navigation([dash])

pg.run()

# sidebar header
with st.sidebar:
    st.markdown("## 🏌️‍♂️ Caddy")
    st.markdown("**Caddy.ai – Live Focus Score**")
    st.markdown("---")


# x = st.slider("Select a value")
# st.write(x, "squared is", x * x)
