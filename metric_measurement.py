from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import threading
import time
import psutil
import scp_client
import os
import matplotlib.pyplot as plt

app = FastAPI()

# 전역 변수 설정
measuring = False
info_list = []
measure_thread = None
log_file_name = None
plot_file_name = None
old_net_io = psutil.net_io_counters()

def measure_machine_info(filename: str):
    global measuring, info_list, old_net_io
    measure_time = 0

    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            f.write("#cpu_usage, memory_usage, disk_usage, send_packets, recv_packets, cpu_temp\n")

    while measuring:
        try:
            cpu_temp = 0
            temps = psutil.sensors_temperatures()
            for key in temps.keys():
                if key in ["coretemp", "cpu_thermal"] :
                    for i in temps[key]:
                        cpu_temp = (cpu_temp + i.current)/2 if cpu_temp != 0 else i.current
                elif key == "thermal-fan-est":
                    cpu_temp = float(os.popen("cat /sys/devices/virtual/thermal/thermal_zone0/temp").read().rstrip())/1000
                else : 
                    cpu_temp = 0
            cpu_usage = psutil.cpu_percent(interval=1)
            cpufreq = psutil.cpu_freq().current
            memory_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent
            new_net_io = psutil.net_io_counters()
            send_packets = new_net_io.packets_sent - old_net_io.packets_sent
            recv_packets = new_net_io.packets_recv - old_net_io.packets_recv
            old_net_io = new_net_io

            info_list.append((cpu_temp,cpu_usage,memory_usage,cpufreq,disk_usage,send_packets,recv_packets))
            time.sleep(1)
        finally:
            measure_time += 1    
            if measure_time == 60 or not measuring:
                with open(filename, 'a') as f:
                    for info in info_list:
                        f.write(' '.join(map(str, info))+ '\n')
                info_list = []
                measure_time = 0

def plot_resources(logfilename,plotfilename):
    
    cpu_temp = []
    cpu_usage = []
    cpufreq = []
    memory = []
    disk = []
    send_packets = []
    recv_packets = []

    with open(logfilename, "r") as f:
        lines = f.readlines()[1:]
    for line in lines :
        line_splited = line.rstrip().split()
        cpu_temp.append(line_splited[0])
        cpu_usage.append(line_splited[1])
        cpufreq.append(line_splited[2])
        memory.append(line_splited[3])
        disk.append(line_splited[4])
        send_packets.append(line_splited[5])
        recv_packets.append(line_splited[6])
        
    fig, axs = plt.subplots(7, 1, figsize=(12, 20))  

    axs[0].plot(cpu_temp, label='CPU Temperatures (c)')
    axs[0].set_title('CPU Temperatures')
    axs[0].set_ylabel('CPU Temperatures (C)')
    axs[0].legend()
    axs[0].grid(True)

    axs[1].plot(cpu_usage, label='CPU Usage (%)')
    axs[1].set_title('CPU Usage Over Time')
    axs[1].set_ylabel('CPU Usage (%)')
    axs[1].legend()
    axs[1].grid(True)

    axs[2].plot(cpufreq, label='CPU Usage (%)')
    axs[2].set_title('CPU Frequency')
    axs[2].set_ylabel('CPU Frequency (Mhz)')
    axs[2].legend()
    axs[2].grid(True)

    axs[3].plot(memory, label='Memory Usage (%)')
    axs[3].set_title('Memory Usage Over Time')
    axs[3].set_ylabel('Memory Usage (%)')
    axs[3].legend()
    axs[3].grid(True)

    axs[4].plot(disk, label='Disk Usage (%)')
    axs[4].set_title('Disk Usage Over Time')
    axs[4].set_ylabel('Disk Usage (%)')
    axs[4].legend()
    axs[4].grid(True)

    axs[5].plot(send_packets, label='Packets Sent')
    axs[5].set_title('Network Packets Sent Over Time')
    axs[5].set_ylabel('Packets Sent')
    axs[5].legend()
    axs[5].grid(True)

    axs[6].plot(recv_packets, label='Packets Received')
    axs[6].set_title('Network Packets Received Over Time')
    axs[6].set_ylabel('Packets Received')
    axs[6].legend()
    axs[6].grid(True)

    plt.xlabel('Time (seconds)')
    plt.tight_layout()
    plt.savefig(plotfilename)

@app.post("/start/{filename}")
async def start_measurement(filename : str):
    global measuring, measure_thread, log_file_name, plot_file_name
    if not measuring:
        measuring = True
        log_file_name = filename + ".txt"
        plot_file_name = filename + ".png"
        measure_thread = threading.Thread(target=measure_machine_info, args=(log_file_name,))
        measure_thread.start()
        return JSONResponse(content={"status": "Measurement started"}, status_code=200)
    else:
        return JSONResponse(content={"status": "Measurement already in progress"}, status_code=200)

@app.post("/stop")
async def stop_measurement():
    global measuring, log_file_name, plot_file_name
    if measuring:
        measuring = False
        measure_thread.join()
        plot_resources(logfilename=log_file_name, plotfilename=plot_file_name)
        scp_client.send_file_to_remote(matchstring=[log_file_name,plot_file_name])
        return JSONResponse(content={"status": "Measurement stopped and data saved"}, status_code=200)
    else:
        return JSONResponse(content={"status": "No measurement in progress"}, status_code=200)

@app.get("/status")
async def status():
    return JSONResponse(content={"measuring": measuring, "data_points": len(info_list), "log_file_name": log_file_name}, status_code=200)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)
