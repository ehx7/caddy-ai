# page1.py or streamlit_app.py
import streamlit as st



def render_page_title(title: str = "Caddy", subtitle: str = "Caddy.ai – Live Focus Score"):
    st.markdown(f"<h1 style='margin-bottom:0;'>{title}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='margin-top:0;'>{subtitle}</p>", unsafe_allow_html=True)
    #st.markdown("---")
