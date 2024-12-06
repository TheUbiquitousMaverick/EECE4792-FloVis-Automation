import subprocess
import psutil
from new_txt_read import process_data_file, calculate_average_time_of_flight
import tkinter as tk
from tkinter import StringVar
from PIL import Image, ImageTk
import io
from new_tof_and_cross_corr import time_lag_cross_correlation, flow_from_lag
import math
import threading
import numpy as np
import time
import matplotlib as plt
import os


def kill_process_by_name(process_name):
    # Iterate over all running processes
    for proc in psutil.process_iter(['pid', 'name']):
        # Check if process name matches
        if proc.info['name'] == process_name:
            try:
                psutil.Process(proc.info['pid']).terminate()
                print(f"Terminated process {process_name} with PID {proc.info['pid']}")
            except psutil.NoSuchProcess:
                print(f"No such process: {process_name}")
            except psutil.AccessDenied:
                print(f"Access denied when trying to terminate {process_name}")
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
        self.speed_sound_medium = 0  # New input
        self.running = False  # Flag to control loop execution

        # Left Frame for Inputs
        self.left_frame = tk.Frame(self.root, width=300, bg="lightgray")
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.input_vars = [StringVar(value="0") for _ in range(4)]  # Increased to 4 inputs
        input_labels = [
            'Pipe Inner Diameter(m)',
            'Pipe Outer Diameter(m)',
            'Speed of Sound in Pipe(m/s)',
            'Speed of Sound in Medium(m/s)'  # New input label
        ]
        for i in range(4):  # Adjusted for 4 inputs
            tk.Label(self.left_frame, text=input_labels[i], bg="lightgray").pack(pady=2)
            tk.Entry(self.left_frame, textvariable=self.input_vars[i], width=50).pack(pady=5)  # Increased width

        # Buttons
        self.run_button = tk.Button(self.left_frame, text="Run", command=self.run_pressed)
        self.run_button.pack(pady=5)
        self.stop_button = tk.Button(self.left_frame, text="Stop", command=self.stop_execution)
        self.stop_button.pack(pady=5)

        self.textout1 = tk.Text(self.left_frame, height=10, width=60, state='disabled')  # Disabled state
        self.textout1.insert(tk.END, "flowrate:\ntemperature:\nReynold number:\nShear Rate:")
        self.textout1.pack()

        # Middle Frame for Image and Text Output
        self.middle_frame = tk.Frame(self.root, width=450)
        self.middle_frame.grid(row=0, column=1, sticky="nsew")
        self.image1_label = tk.Label(self.middle_frame, width=800, height=400)  # Increased size
        self.image1_label.pack()
        self.image4_label = tk.Label(self.middle_frame, width=800, height=400)  # Increased size
        self.image4_label.pack()

        # Right Frame for Second Display and Text Output
        self.right_frame = tk.Frame(self.root, width=450)
        self.right_frame.grid(row=0, column=2, sticky="nsew")
        self.image2_label = tk.Label(self.right_frame, width=800, height=400)  # Increased size
        self.image2_label.pack()
        self.image3_label = tk.Label(self.right_frame, width=800, height=400)  # Increased size
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
        """Initialize image1 and image2 to white boxes."""
        white_box = Image.new("RGB", (450, 350), color="white")  # Updated size
        img_tk = ImageTk.PhotoImage(white_box)

        #img = Image.open("snoopy.jpg")
        #img = img.resize((450, 350), Image.Resampling.LANCZOS)
        #img_tk = ImageTk.PhotoImage(img)

        self.image1_label.config(image=img_tk)
        self.image1_label.image = img_tk  # Keep a reference to avoid garbage collection

        self.image2_label.config(image=img_tk)
        self.image2_label.image = img_tk  # Keep a reference to avoid garbage collection

        self.image3_label.config(image=img_tk)
        self.image3_label.image = img_tk
        self.image4_label.config(image=img_tk)
        self.image4_label.image=img_tk

    def stop_execution(self):
        """Stop the continuous loop."""
        self.running = False
        print("Execution stopped.")

    def update_image1(self, img_buffer):
        """Update image1 with an image from a buffer."""
        try:
            img = Image.open(io.BytesIO(img_buffer.getvalue()))
            img = img.resize((800, 600))  # Updated size
            img_tk = ImageTk.PhotoImage(img)
            self.image1_label.config(image=img_tk)
            self.image1_label.image = img_tk
        except Exception as e:
            print(f"Error updating image1: {e}")

    def update_image2(self, img_buffer):
        """Update image2 with an image from a buffer."""
        try:
            img = Image.open(io.BytesIO(img_buffer.getvalue()))
            img = img.resize((800, 400))  # Updated size
            img_tk = ImageTk.PhotoImage(img)
            self.image2_label.config(image=img_tk)
            self.image2_label.image = img_tk
        except Exception as e:
            print(f"Error updating image2: {e}")

    def update_image3(self, img_buffer):
        """Update image2 with an image from a buffer."""
        try:
            img = Image.open(io.BytesIO(img_buffer.getvalue()))
            img = img.resize((450, 350))  # Updated size
            img_tk = ImageTk.PhotoImage(img)
            self.image3_label.config(image=img_tk)
            self.image3_label.image = img_tk
        except Exception as e:
            print(f"Error updating image2: {e}")

    def update_image4(self, img_buffer):
        """Update image2 with an image from a buffer."""
        try:
            img = Image.open(io.BytesIO(img_buffer.getvalue()))
            img = img.resize((450, 350))  # Updated size
            img_tk = ImageTk.PhotoImage(img)
            self.image4_label.config(image=img_tk)
            self.image4_label.image = img_tk
        except Exception as e:
            print(f"Error updating image2: {e}")

    def update_textout1(self, text):
        """Update text in textout1."""
        self.textout1.config(state='normal')  # Enable text box
        self.textout1.delete("1.0", tk.END)
        self.textout1.insert(tk.END, text)
        self.textout1.config(state='disabled')  # Disable text box again

    def run_pressed(self):
        """Start the continuous loop when Run is pressed."""
        self.stop_execution()  # Stop any running loop
        self.flowrates = []  # Clear flowrates
        self.initialize_images()  # Reset displays
        self.update_textout1("\nBeginning Loop\n")

        # Update input variables
        try:
            self.pipe_dia_inner = float(self.input_vars[0].get())
            self.pipe_dia_outer = float(self.input_vars[1].get())
            self.speed_sound_pipe = float(self.input_vars[2].get())
            self.speed_sound_medium = float(self.input_vars[3].get())  # Parse new input
            print(f"Updated Inputs: Pipe Inner Diameter: {self.pipe_dia_inner}, "
                  f"Pipe Outer Diameter: {self.pipe_dia_outer}, "
                  f"Speed of Sound in Pipe: {self.speed_sound_pipe}, "
                  f"Speed of Sound in Medium: {self.speed_sound_medium}")
        except ValueError:
            print("Invalid input values. Please enter valid numbers.")
            return

        # Start the continuous loop
        self.running = True
        threading.Thread(target=self.continuous_loop, daemon=True).start()

    def continuous_loop(self):
        """Continuously call single_iteration until stopped."""
        while self.running:
            self.single_iteration()
            time.sleep(2)

    def single_iteration(self):
        """Perform a single iteration of subprocess logic."""
        kill_process_by_name('nios2-terminal.exe')

        # Specify the file path
        file_path = 'readings.txt'
        # Check if the file exists
        if os.path.exists(file_path):
        # Delete the file
            os.remove(file_path)
            print(f"{file_path} has been deleted.")
        else:
            print(f"{file_path} does not exist.")

        # Start subprocess for Nios II
        bat_file_path = "C:\\intelFPGA_lite\\18.0\\nios2eds\\Nios II Command Shell.bat"
        process = subprocess.Popen(
            [bat_file_path],
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        download_cmd = "nios2-download -g C:\\\\Users\\\\nwalt\\\\Downloads\\\\DE1-SoC_v.5.1.3_HWrevF.revG_SystemCD\\\\Demonstrations\\\\FPGA\\\\DE1_SoC_SDRAM_Nios_Test\\\\software\\\\DE1_SoC_SDRAM_Nios_Test\\\\DE1_SoC_SDRAM_Nios_Test.elf\r\nnios2-terminal > readings.txt"

        try:
            process.communicate(input=download_cmd, timeout=7)
        except subprocess.TimeoutExpired:
            pass

        process.kill()

        time.sleep(8)

        # Process readings file
        trigger_phrase = "== IT'S ALIVE =="

        try:
            downstream_data, upstream_data, temperature, img_buffer = process_data_file(
                "C:\\Users\\nwalt\\Desktop\\EECE4792-FloVis-Automation\\readings.txt", trigger_phrase
            )


            if img_buffer:
                self.update_image1(img_buffer)
                self.update_image2(img_buffer)

            time_lag,img_cc = time_lag_cross_correlation(upstream_data, downstream_data)
            self.update_image2(img_cc)
            if self.speed_sound_medium != 0:
                speed_sound=self.speed_sound_medium
            else:
                time_pipe=(self.pipe_dia_outer-self.pipe_dia_inner)/self.speed_sound_pipe
                time_water=calculate_average_time_of_flight(downstream_data,upstream_data)-0.00003220801425-time_pipe
                speed_sound=time_water/math.sqrt(2) * self.pipe_dia_inner
            flowrate = flow_from_lag(time_lag, math.sqrt(2) * self.pipe_dia_inner, speed_sound)
            self.flowrates.append(flowrate)

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
            self.update_image4(generate_flowrate_plot(self.flowrates))
            reynold=0
            self.update_textout1(f"flowrate:\n{flowrate}\ntemperature:\n{temperature}°F\nReynold Number: placeholder\nShear Rate: placholder\n")

        except Exception as e:
            print(f"Error processing data: {e}")

    def on_close(self):
        """Handle GUI close event."""
        self.stop_execution()
        self.root.destroy()


# Initialize and run the GUI
gui = CustomGUI()
gui.root.mainloop()
