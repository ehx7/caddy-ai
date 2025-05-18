import streamlit as st
import pandas as pd
import time
import matplotlib.pyplot as plt

import argparse
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
import numpy as np
from brainflow.data_filter import DataFilter, AggOperations


def main():
    BoardShim.enable_dev_board_logger()

    parser = argparse.ArgumentParser()
    # use docs to check which parameters are required for specific board, e.g. for Cyton - set serial port
    parser.add_argument('--timeout', type=int, help='timeout for device discovery or connection', required=False,
                        default=0)
    parser.add_argument('--ip-port', type=int, help='ip port', required=False, default=0)
    parser.add_argument('--ip-protocol', type=int, help='ip protocol, check IpProtocolType enum', required=False,
                        default=0)
    parser.add_argument('--ip-address', type=str, help='ip address', required=False, default='')
    parser.add_argument('--serial-port', type=str, help='serial port', required=False, default='')
    parser.add_argument('--mac-address', type=str, help='mac address', required=False, default='')
    parser.add_argument('--other-info', type=str, help='other info', required=False, default='')
    parser.add_argument('--serial-number', type=str, help='serial number', required=False, default='')
    parser.add_argument('--board-id', type=int, help='board id, check docs to get a list of supported boards',
                        required=False)
    parser.add_argument('--file', type=str, help='file', required=False, default='')
    parser.add_argument('--master-board', type=int, help='master board id for streaming and playback boards',
                        required=False, default=BoardIds.NO_BOARD)
    args = parser.parse_args()

    params = BrainFlowInputParams()
    params.ip_port = args.ip_port
    params.serial_port = args.serial_port
    params.mac_address = args.mac_address
    params.other_info = args.other_info
    params.serial_number = args.serial_number
    params.ip_address = args.ip_address
    params.ip_protocol = args.ip_protocol
    params.timeout = args.timeout
    params.file = args.file
    params.master_board = args.master_board
    
    board_id = BoardIds.CYTON_BOARD.value
    print(board_id)
    board = BoardShim(board_id, params)
    BoardShim.enable_board_logger()
    board.prepare_session()
    board.start_stream()
    time.sleep(10)
    # data = board.get_current_board_data (256) # get latest 256 packages or less, doesnt remove them from internal buffer
    data = board.get_board_data()  # get all data and remove it from internal buffer
    board.stop_stream()
    board.release_session()

    ##
    eeg_channels = BoardShim.get_eeg_channels(BoardIds.CYTON_BOARD.value)
    df = pd.DataFrame(np.transpose(data))
    df.to_csv('raw_data.csv', index = False)
    print('Data From the Board')
    print(df.head(10))
    print(eeg_channels)

    downsampled_data_list = []
    for count, channel in enumerate(eeg_channels):
        print('Original data for channel %d:' % channel)
        print(data[channel])
        if count == 0:
            downsampled_data = DataFilter.perform_downsampling(data[channel], 3, AggOperations.MEDIAN.value)
        elif count == 1:
            downsampled_data = DataFilter.perform_downsampling(data[channel], 2, AggOperations.MEAN.value)
        else:
            downsampled_data = DataFilter.perform_downsampling(data[channel], 2, AggOperations.EACH.value)
        downsampled_data_list.append(downsampled_data)

    # Find the minimum length across all downsampled arrays
    min_len = min(len(arr) for arr in downsampled_data_list)

    # Trim all arrays to this length
    trimmed = [arr[:min_len] for arr in downsampled_data_list]

    # Now you can safely convert to a 2D array
    downsampled_data_collection = np.array(trimmed)

    # Save to CSV
    pd.DataFrame(downsampled_data_collection.T).to_csv('downsampled_data.csv', index=False)

if __name__ == "__main__":
    main()


# FIGURES

df = pd.read_csv('downsampled_data.csv')
sampling_rate = 250
num_points = len(df)
time_axis = np.arange(num_points) / sampling_rate

plt.figure(figsize=(12, 10))
for i in range(8):  # assuming 8 EEG channels
    plt.subplot(8, 1, i + 1)
    plt.plot(time_axis, df.iloc[:, i])
    plt.title(f'Channel {i + 1}')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.tight_layout()

plt.show()

st.title("Live Streaming EEG Plot")

WINDOW_SIZE = 100  # number of points to show in moving window
CSV_PATH = "downsampled_data.csv"

# Placeholder for the plot to update it in place
plot_placeholder = st.empty()

while True:
    try:
        # Load data
        df = pd.read_csv(CSV_PATH)

        # Keep only last WINDOW_SIZE samples
        if df.shape[0] > WINDOW_SIZE:
            df_window = df.tail(WINDOW_SIZE)
        else:
            df_window = df

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 5))
        for i in range(df_window.shape[1]):
            ax.plot(df_window.index, df_window.iloc[:, i], label=f'Channel {i+1}')
        ax.legend(loc='upper right')
        ax.set_title("EEG Channels (Downsampled) - Moving Window")
        ax.set_xlabel("Sample Index (time)")
        ax.set_ylabel("Amplitude")

        # Show plot in Streamlit
        plot_placeholder.pyplot(fig)

        # Wait before next update
        time.sleep(1)

    except Exception as e:
        st.write(f"Error loading or plotting data: {e}")
        time.sleep(2)
