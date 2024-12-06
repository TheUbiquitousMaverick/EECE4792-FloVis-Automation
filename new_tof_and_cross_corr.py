import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt, correlate, find_peaks
from scipy.interpolate import interp1d


def time_lag_cross_correlation(us_data, ds_data):

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

    return time_lag


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

