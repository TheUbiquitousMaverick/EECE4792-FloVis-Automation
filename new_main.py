import subprocess
import psutil
from new_txt_read import process_data_file
import tkinter as tk
from tkinter import StringVar
from PIL import Image, ImageTk
import io
from new_tof_and_cross_corr import time_lag_cross_correlation, flow_from_lag
import math
import threading
import time


class CustomGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Custom GUI")
        self.root.geometry("1600x800")  # Updated window size

        # Variables
        self.flowrates = []
        self.pipe_dia_inner = 0  # Inner diameter
        self.pipe_dia_outer = 0  # Outer diameter
        self.speed_sound = 0
        self.running = False  # Flag to control loop execution

        # Left Frame for Inputs
        self.left_frame = tk.Frame(self.root, width=300, bg="lightgray")
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.input_vars = [StringVar(value="0") for _ in range(3)]
        input_labels = ['Pipe Inner Diameter', 'Pipe Outer Diameter', 'Speed of Sound']
        for i in range(3):
            tk.Label(self.left_frame, text=input_labels[i], bg="lightgray").pack(pady=2)
            tk.Entry(self.left_frame, textvariable=self.input_vars[i]).pack(pady=5)

        # Buttons
        self.run_button = tk.Button(self.left_frame, text="Run", command=self.run_pressed)
        self.run_button.pack(pady=5)
        self.stop_button = tk.Button(self.left_frame, text="Stop", command=self.stop_execution)
        self.stop_button.pack(pady=5)

        # Middle Frame for Image and Text Output
        self.middle_frame = tk.Frame(self.root, width=450)
        self.middle_frame.grid(row=0, column=1, sticky="nsew")
        self.image1_label = tk.Label(self.middle_frame, width=800, height=600)  # Increased size
        self.image1_label.pack()
        self.textout1 = tk.Text(self.middle_frame, height=10, width=60)  # Adjusted size
        self.textout1.insert(tk.END, "flowrate:\ntemperature:\n")
        self.textout1.pack()

        # Right Frame for Second Display and Text Output
        self.right_frame = tk.Frame(self.root, width=450)
        self.right_frame.grid(row=0, column=2, sticky="nsew")
        self.image2_label = tk.Label(self.right_frame, width=800, height=600)  # Increased size
        self.image2_label.pack()
        self.textout2 = tk.Text(self.right_frame, height=10, width=60)  # Adjusted size
        self.textout2.insert(tk.END, "reynold number:\nshear rate:\n")
        self.textout2.pack()

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
        white_box = Image.new("RGB", (800, 600), color="white")  # Updated size
        img_tk = ImageTk.PhotoImage(white_box)

        self.image1_label.config(image=img_tk)
        self.image1_label.image = img_tk  # Keep a reference to avoid garbage collection

        self.image2_label.config(image=img_tk)
        self.image2_label.image = img_tk  # Keep a reference to avoid garbage collection

    def kill_process_by_name(self, process_name):
        """Kill a process by its name."""
        for proc in psutil.process_iter(['pid', 'name']):
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
            img = img.resize((800, 600))  # Updated size
            img_tk = ImageTk.PhotoImage(img)
            self.image2_label.config(image=img_tk)
            self.image2_label.image = img_tk
        except Exception as e:
            print(f"Error updating image2: {e}")

    def update_textout1(self, text):
        """Update text in textout1."""
        self.textout1.delete("1.0", tk.END)
        self.textout1.insert(tk.END, text)

    def update_textout2(self, text):
        """Update text in textout2."""
        self.textout2.delete("1.0", tk.END)
        self.textout2.insert(tk.END, text)

    def run_pressed(self):
        """Start the continuous loop when Run is pressed."""
        self.stop_execution()  # Stop any running loop
        self.flowrates = []  # Clear flowrates
        self.initialize_images()  # Reset displays
        self.update_textout1("flowrate:\ntemperature:\n")
        self.update_textout2("reynold number:\nshear rate:\n")

        # Update input variables
        try:
            self.pipe_dia_inner = float(self.input_vars[0].get())
            self.pipe_dia_outer = float(self.input_vars[1].get())
            self.speed_sound = float(self.input_vars[2].get())
            print(f"Updated Inputs: Pipe Inner Diameter: {self.pipe_dia_inner}, "
                  f"Pipe Outer Diameter: {self.pipe_dia_outer}, Speed of Sound: {self.speed_sound}")
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

    def single_iteration(self):
        """Perform a single iteration of subprocess logic."""
        self.kill_process_by_name('nios2-terminal.exe')

        # Start subprocess for Nios II
        bat_file_path = "C:\\intelFPGA_lite\\18.0\\nios2eds\\Nios II Command Shell.bat"
        process = subprocess.Popen(
            [bat_file_path],
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        download_cmd = (
            "nios2-download -c USB-Blaster -g "
            "C:\\Users\\nwalt\\Downloads\\DE10-Lite_v.2.1.0_SystemCD\\Demonstrations\\SDRAM_Nios_Test\\" 
            "software\\DE10_LITE_SDRAM_Nios_Test\\DE10_LITE_SDRAM_Nios_Test.elf\r\n" 
            "nios2-terminal -c USB-Blaster > readings.txt"
        )

        try:
            process.communicate(input=download_cmd, timeout=7)
        except subprocess.TimeoutExpired:
            pass

        process.kill()

        # Process readings file
        trigger_phrase = "== IT'S ALIVE =="

        try:
            downstream_data, upstream_data, temperature, img_buffer = process_data_file(
                "readings.txt", trigger_phrase
            )

            if img_buffer:
                self.update_image1(img_buffer)
                self.update_image2(img_buffer)
            time_lag = time_lag_cross_correlation(upstream_data, downstream_data)
            flowrate = flow_from_lag(time_lag, math.sqrt(2) * self.pipe_dia_inner, self.speed_sound)
            self.flowrates.append(flowrate)
            self.update_textout1(f"flowrate:\n{flowrate}\ntemperature:\n{temperature}°C\n")
            self.update_textout2(f"reynold number:\n{'placeholder'}\nshear rate:\nCalculated Placeholder\n")

        except Exception as e:
            print(f"Error processing data: {e}")

    def on_close(self):
        """Handle GUI close event."""
        self.stop_execution()
        self.root.destroy()


# Initialize and run the GUI
gui = CustomGUI()
gui.root.mainloop()
