import streamlit as st
import time
import numpy as np

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter
from brainflow.ml_model import MLModel, BrainFlowMetrics, BrainFlowClassifiers, BrainFlowModelParams


def setup_board():
    BoardShim.enable_dev_board_logger()
    params = BrainFlowInputParams()
    params.serial_port = '/dev/cu.usbserial-D200QSOE'  # Change if needed
    board_id = BoardIds.CYTON_BOARD.value
    board = BoardShim(board_id, params)
    board.prepare_session()
    board.start_stream()
    eeg_channels = BoardShim.get_eeg_channels(board_id)
    sampling_rate = BoardShim.get_sampling_rate(board_id)
    return board, board_id, eeg_channels, sampling_rate


def get_mindfulness_score(data, eeg_channels, sampling_rate):
    bands = DataFilter.get_avg_band_powers(data, eeg_channels, sampling_rate, apply_filter=True)
    feature_vector = bands[0]
    mindfulness_params = BrainFlowModelParams(BrainFlowMetrics.MINDFULNESS.value,
                                              BrainFlowClassifiers.DEFAULT_CLASSIFIER.value)
    mindfulness = MLModel(mindfulness_params)
    mindfulness.prepare()
    score = mindfulness.predict(feature_vector)
    mindfulness.release()
    return score


# Streamlit UI
st.title("🧠 Real-Time Mindfulness Tracker")
start_button = st.button("Start Mindfulness Tracking")
stop_button = st.button("Stop")

if 'running' not in st.session_state:
    st.session_state.running = False

# Control logic
if start_button:
    st.session_state.running = True
    st.session_state.scores = []
elif stop_button:
    st.session_state.running = False

# Display plot placeholder
score_chart = st.line_chart()

# Run tracking loop
if st.session_state.running:
    board, board_id = setup_board()
    eeg_channels = BoardShim.get_eeg_channels(board_id)
    sampling_rate = BoardShim.get_sampling_rate(board_id)

    window_duration = 4  # seconds of data per calculation
    refresh_interval = 2  # seconds between updates
    buffer_size = sampling_rate * window_duration

    st.success("Tracking started. Live mindfulness scores below.")

    try:
        while st.session_state.running:
            time.sleep(refresh_interval)
            data = board.get_current_board_data(buffer_size)
            score = get_mindfulness_score(data, eeg_channels, sampling_rate)
            st.session_state.scores.append(score)
            score_chart.add_rows([[score]])
            st.write(f"Latest Mindfulness Score: **{score:.2f}**")
            st.write(score)

    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        board.stop_stream()
        board.release_session()
        st.success("Tracking stopped.")

