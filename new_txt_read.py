import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
import numpy as np
import io



def process_data_file(file_path, trigger_phrase):
    """
    Process the data file, parse upstream and downstream data, apply filtering,
    and create a single plot. The plot is returned as an image buffer.
    """
    cutoff_frequency = 1000000
    sampling_rate = 50e6

    downstream_data = []
    upstream_data = []
    temperature = None

    # Read the file
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Parse the file
    start_reading = False
    for line in lines:
        line = line.strip()
        if not start_reading:
            if line.startswith(trigger_phrase):
                start_reading = True
            continue  # Skip lines until the trigger phrase is found

        if line.startswith("=="):
            continue
        if line.startswith("temperature: "):
            temperature = float(line.split("temperature: ")[1].strip())
        elif line.startswith("DONE"):
            break  # Stop reading after "DONE"
        elif line.startswith("us") or line.startswith("ds"):
            # Parse upstream or downstream data
            parts = line.split()
            if len(parts) != 3:
                continue  # Skip invalid lines
            prefix, sample, voltage = parts
            sample = float(sample)
            voltage = float(voltage)
            if prefix == "us":
                upstream_data.append((sample, voltage))
            elif prefix == "ds":
                downstream_data.append((sample, voltage))
        else:
            continue

    downstream_data = downstream_data[25:]
    # Convert to DataFrame
    downstream_df = pd.DataFrame(downstream_data, columns=["Sample", "Voltage"])
    upstream_df = pd.DataFrame(upstream_data, columns=["Sample", "Voltage"])

    # Convert to seconds
    downstream_df["Second"] = downstream_df["Sample"] / sampling_rate
    upstream_df["Second"] = upstream_df["Sample"] / sampling_rate

    # Drop sample column
    downstream_df.drop(columns=["Sample"], inplace=True)
    upstream_df.drop(columns=["Sample"], inplace=True)

    # Butterworth filter
    def butter_lowpass_filter(data, cutoff, fs, order=5):
        nyquist = 0.5 * fs
        normal_cutoff = cutoff / nyquist
        try:
            b, a = butter(order, normal_cutoff, btype='low', analog=False)
            return filtfilt(b, a, data)
        except Exception as e:
            print(f"Filtering failed with error: {e}. Returning original data.")
            return data

    # Apply filtering
    downstream_df["Voltage_Filtered"] = butter_lowpass_filter(downstream_df["Voltage"], cutoff_frequency, sampling_rate)
    upstream_df["Voltage_Filtered"] = butter_lowpass_filter(upstream_df["Voltage"], cutoff_frequency, sampling_rate)

    # Create a single plot and save to buffer
    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot downstream data
    ax.plot(downstream_df["Second"], downstream_df["Voltage"], label="Downstream Original", alpha=0.7)
    ax.plot(downstream_df["Second"], downstream_df["Voltage_Filtered"], label="Downstream Filtered", linewidth=2)

    # Plot upstream data
    ax.plot(upstream_df["Second"], upstream_df["Voltage"], label="Upstream Original", alpha=0.7)
    ax.plot(upstream_df["Second"], upstream_df["Voltage_Filtered"], label="Upstream Filtered", linewidth=2)

    # Add labels and legend
    ax.set_xlabel("Time (Seconds)")
    ax.set_ylabel("Voltage (Volts)")
    ax.set_title("Upstream and Downstream Data")
    ax.legend()
    ax.grid()

    # Save the plot to a buffer
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)

    return downstream_df, upstream_df, temperature, buf


# Example usage
#trigger_phrase = "== IT'S ALIVE =="  # or another trigger phrase
#downstream_data, upstream_data, temperature = process_data_file("readings.txt", trigger_phrase)
