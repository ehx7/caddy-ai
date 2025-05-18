# page1.py or streamlit_app.py
import streamlit as st


# title
def render_page_title(title: str = "Caddy", subtitle: str = "Caddy.ai – Live Focus Score"):
    st.markdown(f"<h1 style='margin-bottom:0;'>{title}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='margin-top:0;'>{subtitle}</p>", unsafe_allow_html=True)
    #st.markdown("---")

# session button
def login_logout():
    if not st.session_state.start:
        if st.button("Start"):
            
            st.session_state.start = True
            #st.session_state.page = "page_2"
            st.rerun()
            
    else:
        st.success("Session is active.")
        if st.button("End"):
            st.session_state.start = False
            st.rerun()



# Unified toggle button with timer logic
def toggle_session():
    if st.button("Start" if not st.session_state.start else "End"):
        st.session_state.start = not st.session_state.start

        if st.session_state.start:
            st.session_state.start_time = time.time()  # Save start time
            st.session_state.page = "page_2"
        else:
            st.session_state.page = "home"
        
        st.rerun()

# timer
def show_timer():
    if st.session_state.start and st.session_state.start_time is not None:
        elapsed = int(time.time() - st.session_state.start_time)
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        st.info(f"Elapsed Time: {hours:02}:{minutes:02}:{seconds:02} ⏱️ ")


def home():
    st.title("⛳ Caddy.ai")
    st.write("Welcome")
    toggle_session()
    show_timer()
    

def page_2():
    st.title("Session")
    st.success("Session is active.")
    st.write("This is Page 2.")
    show_timer()
    toggle_session()
    
    


