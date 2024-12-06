import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt, correlate, find_peaks
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import io

def time_lag_cross_correlation(us_data, ds_data):
    """
    Calculate the time lag using cross-correlation and visualize the result.

    Parameters:
        us_data (DataFrame): Upstream data with 'Second' and 'Voltage_Filtered' columns.
        ds_data (DataFrame): Downstream data with 'Second' and 'Voltage_Filtered' columns.

    Returns:
        float: The calculated time lag in seconds.
    """

    # Extract time and signal data
    us_time = us_data['Second'].values
    us_signal = us_data['Voltage_Filtered'].values
    ds_time = ds_data['Second'].values
    ds_signal = ds_data['Voltage_Filtered'].values

    # Interpolate signals to a common time base
    common_time = np.linspace(
        max(us_time.min(), ds_time.min()),
        min(us_time.max(), ds_time.max()),
        min(len(us_signal), len(ds_signal))
    )
    us_signal_interp = np.interp(common_time, us_time, us_signal)
    ds_signal_interp = np.interp(common_time, ds_time, ds_signal)

    # Compute cross-correlation
    cross_corr = np.correlate(us_signal_interp, ds_signal_interp, mode='full')

    # Find lag index and calculate time lag
    lag_index = np.argmax(cross_corr) - (len(ds_signal_interp) - 1)
    time_step = common_time[1] - common_time[0]
    time_lag = lag_index * time_step

    # Generate time lags for plotting
    time_lags = np.arange(-len(ds_signal_interp) + 1, len(us_signal_interp)) * time_step

    # Plot cross-correlation vs time lag
    plt.figure(figsize=(10, 6))
    plt.plot(time_lags, cross_corr, label='Cross-Correlation')
    plt.axvline(time_lag, color='r', linestyle='--', label=f'Max at {time_lag:.8f}s')
    plt.title('Cross-Correlation vs Time Lag')
    plt.xlabel('Time Lag (s)')
    plt.ylabel('Cross-Correlation Amplitude')
    plt.legend()
    plt.grid()
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)

    return time_lag, buf


def speed_of_sound_fahrenheit(fahrenheit_temp):

    # Data for temperature in Celsius and corresponding speed of sound
    temperatures_celsius = np.array([0, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    speed_of_sound = np.array([1403, 1427, 1447, 1481, 1507, 1526, 1541, 1552, 1555, 1555, 1550, 1543])

    # Interpolation function
    interpolation_func = interp1d(temperatures_celsius, speed_of_sound, kind='cubic')

    # Convert Fahrenheit to Celsius
    celsius_temp = (fahrenheit_temp - 32) * 5 / 9

    # Return interpolated speed of sound
    return interpolation_func(celsius_temp)


def flow_from_lag(time_lag,dist,speed_sound):

    flow=time_lag*(speed_sound**2)/(2*dist)

    return flow


def generate_flowrate_plot(flowrates):
    try:
        # Generate indices (1-based)
        indices = np.arange(1, len(flowrates) + 1)

        # Calculate the cumulative average (flow_average)
        flow_average = np.cumsum(flowrates) / indices

        # Create the plot
        plt.figure(figsize=(8, 6))
        plt.plot(indices, flowrates, 'o', label='Flowrate Points')  # Scatter plot for flowrates
        plt.plot(indices, flow_average, 'r-', label='Cumulative Average')  # Cumulative average line

        # Label the newest cumulative average value
        if len(flow_average) > 0:
            newest_avg_value = flow_average[-1]
            newest_avg_index = indices[-1]
            plt.text(
                newest_avg_index,
                newest_avg_value,
                f'{newest_avg_value:.2f}',
                color='red',
                fontsize=10,
                ha='right',
                va='bottom'
            )

        plt.title('Flowrate vs Index with Cumulative Average')
        plt.xlabel('Index')
        plt.ylabel('Flowrate')
        plt.legend()
        plt.grid()

        # Save the plot to a buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)  # Move to the start of the buffer
        plt.close()  # Close the plot to free memory

        return img_buffer
    except Exception as e:
        print(f"Error generating flowrate plot: {e}")
        return None

    except Exception as e:
        print(f"Error generating flowrate plot: {e}")
        return None

#print(flow_from_lag(2.1399938857170138e-07,0.0635, 1481))
