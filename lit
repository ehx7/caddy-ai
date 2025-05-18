import streamlit as st
from streamlit_autorefresh import st_autorefresh
import serial.tools.list_ports
from datetime import datetime
import pandas as pd

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter
from brainflow.ml_model import MLModel, BrainFlowMetrics, BrainFlowClassifiers, BrainFlowModelParams

# Serial Port Detection
def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    return [(port.device, f"{port.device} - {port.description}") for port in ports]

# EEG Setup
def setup_board(selected_port):
    BoardShim.enable_dev_board_logger()
    params = BrainFlowInputParams()
    params.serial_port = selected_port
    board_id = BoardIds.CYTON_BOARD.value
    board = BoardShim(board_id, params)
    board.prepare_session()
    board.start_stream()
    eeg_channels = BoardShim.get_eeg_channels(board_id)
    sampling_rate = BoardShim.get_sampling_rate(board_id)
    return board, board_id, eeg_channels, sampling_rate

# Mindfulness Calculation
def get_mindfulness_score(data, eeg_channels, sampling_rate):
    bands = DataFilter.get_avg_band_powers(data, eeg_channels, sampling_rate, apply_filter=True)
    feature_vector = bands[0]
    mindfulness_params = BrainFlowModelParams(BrainFlowMetrics.MINDFULNESS,
                                              BrainFlowClassifiers.DEFAULT_CLASSIFIER)
    mindfulness = MLModel(mindfulness_params)
    mindfulness.prepare()
    score = mindfulness.predict(feature_vector)
    mindfulness.release()
    return score

# Streamlit Page Config
st.set_page_config(page_title="Caddy.ai", layout="centered")
st.title("⛳ Caddy.ai – Live Focus Score + Real-time Plot")

# Serial Port Selector UI
st.sidebar.title("🔌 EEG Board Setup")
available_ports = list_serial_ports()

if not available_ports:
    st.sidebar.error("No serial ports found. Plug in your Cyton dongle.")
    st.stop()

port_options = [label for _, label in available_ports]
label_to_port = {label: device for device, label in available_ports}
selected_label = st.sidebar.selectbox("Select Serial Port", port_options)
selected_port = label_to_port[selected_label]
st.sidebar.success(f"Using: {selected_port}")

# Sidebar header
with st.sidebar:
    st.markdown("## 🏌️‍♂️ Caddy")
    st.markdown("**Caddy.ai – Live Focus Score**")
    st.markdown("---")

# Initialize session state for board and data if not present
if "board" not in st.session_state:
    try:
        board, board_id, eeg_channels, sampling_rate = setup_board(selected_port)
        st.session_state.board = board
        st.session_state.board_id = board_id
        st.session_state.eeg_channels = eeg_channels
        st.session_state.sampling_rate = sampling_rate
        st.session_state.scores = []
        st.session_state.timestamps = []
        st.success("EEG board connected successfully!")
    except Exception as e:
        st.error(f"Failed to initialize board: {e}")
        st.stop()
else:
    board = st.session_state.board
    board_id = st.session_state.board_id
    eeg_channels = st.session_state.eeg_channels
    sampling_rate = st.session_state.sampling_rate

# Autorefresh every 5 seconds
st_autorefresh(interval=5000, key="datarefresh")

try:
    window_duration = 10  # seconds of data per calculation
    buffer_size = sampling_rate * window_duration

    # Get latest EEG data and calculate score
    data = board.get_current_board_data(buffer_size)
    score = get_mindfulness_score(data, eeg_channels, sampling_rate)

    # Append new score + timestamp
    st.session_state.scores.append(score)
    st.session_state.timestamps.append(datetime.now())

    # Display current score
    st.metric("🧠 Focus Score", f"{score:.2f}")

    # Plot the score history as a line chart
    df_scores = pd.DataFrame({
        "Time": st.session_state.timestamps,
        "Focus Score": st.session_state.scores
    }).set_index("Time")

    st.line_chart(df_scores)

    if score < 2.2:
        st.error("🔴 Nudge: Take a breath.")
    else:
        st.success("🟢 Focus is stable.")

except Exception as e:
    st.error(f"❌ Error reading data or calculating score: {e}")

# Shutdown button to cleanly stop the board session
if st.button("Stop EEG Stream and Release"):
    try:
        board.stop_stream()
        board.release_session()
        st.session_state.clear()
        st.success("EEG session stopped and released.")
    except Exception as e:
        st.error(f"Failed to stop/release board: {e}")
