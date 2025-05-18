import streamlit as st
import pandas as pd
import time
import matplotlib.pyplot as plt
import numpy as np
import argparse
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, AggOperations


def run_streaming_app():
    BoardShim.enable_dev_board_logger()

    # Set up connection parameters for Cyton
    params = BrainFlowInputParams()
    params.serial_port = '/dev/cu.usbserial-D200QSOE'  # <- UPDATE if needed

    board_id = BoardIds.CYTON_BOARD.value
    board = BoardShim(board_id, params)

    try:
        BoardShim.enable_board_logger()
        board.prepare_session()
        board.start_stream()

        st.title("Live EEG Streaming: 8 Channel Moving Plots")
        WINDOW_SIZE = 240  # enough for short display

        plot_placeholders = [st.empty() for _ in range(8)]

        while True:
            board_data = board.get_current_board_data(WINDOW_SIZE)
            eeg_channels = BoardShim.get_eeg_channels(board_id)

            downsampled_data_list = []
            for count, channel in enumerate(eeg_channels):
                if count == 0:
                    downsampled = DataFilter.perform_downsampling(
                        board_data[channel], 3, AggOperations.MEDIAN.value)
                elif count == 1:
                    downsampled = DataFilter.perform_downsampling(
                        board_data[channel], 2, AggOperations.MEAN.value)
                else:
                    downsampled = DataFilter.perform_downsampling(
                        board_data[channel], 2, AggOperations.EACH.value)
                downsampled_data_list.append(downsampled)

            min_len = min(len(arr) for arr in downsampled_data_list)
            trimmed = [arr[:min_len] for arr in downsampled_data_list]
            Df = pd.DataFrame(np.array(trimmed).T)

            for i in range(8):
                fig, ax = plt.subplots()
                ax.plot(Df.iloc[:, i])
                ax.set_title(f"Channel {i + 1}")
                ax.set_xlabel("Time")
                ax.set_ylabel("Amplitude")
                plot_placeholders[i].pyplot(fig)

            time.sleep(1)

    except Exception as e:
        st.error(f"Error occurred: {e}")
    finally:
        board.stop_stream()
        board.release_session()


if __name__ == '__main__':
    run_streaming_app()
