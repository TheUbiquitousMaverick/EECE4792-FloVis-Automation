import subprocess
import psutil
from new_txt_read import process_data_file, calculate_average_time_of_flight
import tkinter as tk
from tkinter import StringVar
from PIL import Image, ImageTk
import io
from new_tof_and_cross_corr import time_lag_cross_correlation, flow_from_lag, generate_flowrate_plot
import math
import numpy as np
import matplotlib.pyplot as plt
import os
import time


def kill_process_by_name(process_name):
    """Terminate a process by its name."""
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            try:
                psutil.Process(proc.info['pid']).terminate()
                print(f"Terminated process {process_name} with PID {proc.info['pid']}")
            except Exception as e:
                print(f"Error terminating process {process_name}: {e}")


class CustomGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Custom GUI")
        self.root.geometry("1600x800")  # Updated window size

        # Variables
        self.flowrates = []
        self.pipe_dia_inner = 0  # Inner diameter
        self.pipe_dia_outer = 0  # Outer diameter
        self.speed_sound_pipe = 0
        self.speed_sound_medium = 0

        # Left Frame for Inputs
        self.left_frame = tk.Frame(self.root, width=300, bg="lightgray")
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.input_vars = [StringVar(value="0") for _ in range(4)]
        input_labels = [
            'Pipe Inner Diameter(m)',
            'Pipe Outer Diameter(m)',
            'Speed of Sound in Pipe(m/s)',
            'Speed of Sound in Medium(m/s)'
        ]
        for i in range(4):
            tk.Label(self.left_frame, text=input_labels[i], bg="lightgray").pack(pady=2)
            tk.Entry(self.left_frame, textvariable=self.input_vars[i], width=50).pack(pady=5)

        # Buttons
        self.run_button = tk.Button(self.left_frame, text="Run", command=self.run_pressed)
        self.run_button.pack(pady=5)
        self.stop_button = tk.Button(self.left_frame, text="Stop", command=self.stop_pressed)
        self.stop_button.pack(pady=5)

        self.textout1 = tk.Text(self.left_frame, height=10, width=60, state='disabled')
        self.textout1.insert(tk.END, "flowrate:\ntemperature:\nReynold number:\nShear Rate:")
        self.textout1.pack()

        # Middle Frame for Image and Text Output
        self.middle_frame = tk.Frame(self.root, width=450)
        self.middle_frame.grid(row=0, column=1, sticky="nsew")
        self.image1_label = tk.Label(self.middle_frame, width=450, height=350)
        self.image1_label.pack()
        self.image4_label = tk.Label(self.middle_frame, width=450, height=350)
        self.image4_label.pack()

        # Right Frame for Second Display and Text Output
        self.right_frame = tk.Frame(self.root, width=450)
        self.right_frame.grid(row=0, column=2, sticky="nsew")
        self.image2_label = tk.Label(self.right_frame, width=450, height=350)
        self.image2_label.pack()
        self.image3_label = tk.Label(self.right_frame, width=450, height=350)
        self.image3_label.pack()

        # Initialize images to a white box
        self.initialize_images()

        # Configure Grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)

        # Protocol to handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def initialize_images(self):
        """Initialize images to a blank state."""
        white_box = Image.new("RGB", (450, 350), color="white")
        img_tk = ImageTk.PhotoImage(white_box)

        self.image1_label.config(image=img_tk)
        self.image1_label.image = img_tk
        self.image2_label.config(image=img_tk)
        self.image2_label.image = img_tk
        self.image3_label.config(image=img_tk)
        self.image3_label.image = img_tk
        self.image4_label.config(image=img_tk)
        self.image4_label.image = img_tk

    def stop_pressed(self):
        """Clear all outputs."""
        self.flowrates = []  # Clear flowrates
        self.initialize_images()  # Reset displays
        self.update_textout1("Outputs cleared.")

    def update_image(self, label, img_buffer):
        """Update a specific image label with a new image."""
        try:
            img = Image.open(io.BytesIO(img_buffer.getvalue()))
            img = img.resize((450, 350))
            img_tk = ImageTk.PhotoImage(img)
            label.config(image=img_tk)
            label.image = img_tk
        except Exception as e:
            print(f"Error updating image: {e}")

    def update_textout1(self, text):
        """Update text in the output box."""
        self.textout1.config(state='normal')
        self.textout1.delete("1.0", tk.END)
        self.textout1.insert(tk.END, text)
        self.textout1.config(state='disabled')

    def run_pressed(self):
        """Run the process once."""
        kill_process_by_name('nios2-terminal.exe')  # Kill any existing processes
        #self.stop_pressed()  # Clear previous outputs

        # Update input variables
        try:
            self.pipe_dia_inner = float(self.input_vars[0].get())
            self.pipe_dia_outer = float(self.input_vars[1].get())
            self.speed_sound_pipe = float(self.input_vars[2].get())
            self.speed_sound_medium = float(self.input_vars[3].get())
            print(
                f"Inputs updated: {self.pipe_dia_inner}, {self.pipe_dia_outer}, {self.speed_sound_pipe}, {self.speed_sound_medium}")
        except ValueError:
            print("Invalid input values. Please enter valid numbers.")
            return

        # Run the FPGA process
        bat_file_path = "C:\\intelFPGA_lite\\18.0\\nios2eds\\Nios II Command Shell.bat"
        process = subprocess.Popen([bat_file_path], text=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        download_cmd = (
            "nios2-download -g C:\\\\Users\\\\nwalt\\\\Downloads\\\\DE1-SoC_v.5.1.3_HWrevF.revG_SystemCD\\\\Demonstrations\\\\FPGA"
            "\\\\DE1_SoC_SDRAM_Nios_Test\\\\software\\\\DE1_SoC_SDRAM_Nios_Test\\\\DE1_SoC_SDRAM_Nios_Test.elf\r\n"
            "nios2-terminal > readings.txt"
        )

        try:
            process.communicate(input=download_cmd, timeout=10)
        except subprocess.TimeoutExpired:
            print("Process timeout expired.")
        finally:
            process.kill()  # Ensure the process is terminated

        # Wait for the file to be written
        time.sleep(5)

        # Process the readings file
        trigger_phrase = "== IT'S ALIVE =="
        try:
            downstream_data, upstream_data, temperature, img_buffer = process_data_file("readings.txt", trigger_phrase)

            # Update images and text in the GUI
            if img_buffer:
                self.update_image(self.image1_label, img_buffer)

            time_lag, img_cc = time_lag_cross_correlation(upstream_data, downstream_data)
            self.update_image(self.image2_label, img_cc)

            if self.speed_sound_medium != 0:
                speed_sound = self.speed_sound_medium
            else:
                time_pipe = (self.pipe_dia_outer - self.pipe_dia_inner) / self.speed_sound_pipe
                time_water = calculate_average_time_of_flight(downstream_data,
                                                                           upstream_data) - 0.00003220801425 - time_pipe
                speed_sound = time_water / math.sqrt(2) * self.pipe_dia_inner

            flowrate = flow_from_lag(time_lag, math.sqrt(2) * self.pipe_dia_inner, speed_sound)
            self.flowrates.append(flowrate)
            img_flowrates_plot=generate_flowrate_plot(self.flowrates)
            self.update_image(self.image4_label,img_flowrates_plot)
            self.update_textout1(f"flowrate:\n{flowrate}\ntemperature:\n{temperature}°F\n")
        except Exception as e:
            print(f"Error processing data: {e}")

    def on_close(self):
        """Handle GUI close event."""
        self.root.destroy()


# Initialize and run the GUI
gui = CustomGUI()
gui.root.mainloop()
