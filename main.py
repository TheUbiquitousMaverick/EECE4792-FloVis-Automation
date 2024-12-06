import subprocess
import psutil
import new_txt_read
import time


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


#while True:

    #g = input("Press any button")
    
# Example usage
kill_process_by_name('nios2-terminal.exe')

bat_file_path = "C:\\intelFPGA_lite\\18.0\\nios2eds\\Nios II Command Shell.bat"
process = subprocess.Popen([bat_file_path], text=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# C:\Users\nwalt\Downloads\DE1-SoC_v.5.1.3_HWrevF.revG_SystemCD\Demonstrations\FPGA\DE1_SoC_SDRAM_Nios_Test\software\DE1_SoC_SDRAM_Nios_Test

#downloadCmd = "nios2-download -g C:\\\\Users\\\\nwalt\\\\Downloads\\\\DE1-SoC_v.5.1.3_HWrevF.revG_SystemCD" \
#              "\\\\Demonstrations\\\\FPGA\\\\DE1_SoC_SDRAM_Nios_Test\\\\software\\\\DE1_SoC_SDRAM_Nios_Test" \
#              "\\\\DE1_SoC_SDRAM_Nios_Test.elf\r\nnios2-terminal > readings.txt "

downloadCmd = "nios2-download -g C:\\\\Users\\\\nwalt\\\\Downloads\\\\DE1-SoC_v.5.1.3_HWrevF.revG_SystemCD\\\\Demonstrations\\\\FPGA\\\\DE1_SoC_SDRAM_Nios_Test\\\\software\\\\DE1_SoC_SDRAM_Nios_Test\\\\DE1_SoC_SDRAM_Nios_Test.elf\r\nnios2-terminal > readings.txt"

# Send the input
try:
    process.communicate(input=downloadCmd, timeout=10)
except subprocess.TimeoutExpired:
    pass

process.kill()

# file_path = 'readings.txt'
# # Open the file and read its content
# with open(file_path, 'r') as file:
#     for line in file:
#         print(line, end='')

time.sleep(5)

trigger_phrase = "== IT'S ALIVE =="  # or another trigger phrase
downstream_data, upstream_data, temperature, img = new_txt_read.process_data_file("readings.txt", trigger_phrase)

