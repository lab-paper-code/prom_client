from config import YOLO_INPUT_PATH, YOLO_OUTPUT_PATH, FFMPEG_INPUT_PATH, FFMPEG_OUTPUT_PATH, IP, Port, IPERF3_IP, IPERF3_Port, PROCESS_IMAGE, ISPLOT, MODE, DB_PATH, DATASET_PATH, COLLECTION_NAME
from yolo_image_predict import YOLOJob
#from vectordb_image_search import ChromaJob
from ffmpeg_video_size_reduction import FFMpegJob

import uvicorn
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse

from prometheus_client import make_asgi_app
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
from prometheus_client.registry import Collector

from computing_measure import get_network_bandwidth, get_cpu_utility, get_available_ram
import time
import datetime
import psutil
import matplotlib.pyplot as plt
import threading
import os
from tqdm import tqdm

from ultralytics import YOLO
import torch
from PIL import Image
import numpy as np

import scp_client 

def get_image_list(input_path):
        return [ f"{input_path}/{i}" for i in os.listdir(input_path)]

# 데이터셋 예열
def preload_images(image_paths, device='cuda'):
    images = []
    for path in tqdm(image_paths):
        # 이미지를 로드하고 필요한 전처리를 수행
        img = Image.open(path).convert('RGB')
        img = img.resize((640, 640))  # YOLO 입력 크기에 맞게 조정
        img = torch.from_numpy(np.array(img)).permute(2, 0, 1).unsqueeze(0).float() / 255.0
        img = img.to(device)
        images.append(img)
    return images

# 메인
def warm_cache():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    image_paths = get_image_list(YOLO_INPUT_PATH)
    
    # 이미지 데이터셋을 메모리에 예열
    preloaded_images = preload_images(image_paths, device=device)
    print(f"{len(preloaded_images)} images loaded into memory.")

    print("Model is warmed up and ready for inference.")

#warm_cache()


cpu_usages = []
memory_usages = []
disk_usages = []
network_send_packets = []
network_recv_packets = []
cpu_temps = []

yolo = YOLOJob()
yolo.set_input_path(YOLO_INPUT_PATH)
yolo.set_output_path(YOLO_OUTPUT_PATH)

# chroma = ChromaJob()
# chroma.set_db_path(DB_PATH)
# chroma.set_dataset_path(DATASET_PATH)
# chroma.set_collection_name(COLLECTION_NAME)

total_output_image = 0

mpeg = FFMpegJob()
mpeg.set_input_path(FFMPEG_INPUT_PATH)
mpeg.set_output_path(FFMPEG_OUTPUT_PATH)


# def set_total_output_image():
#     global total_output_image
#     total_output_image += file_count(f"{YOLO_OUTPUT_PATH}/{yolo.current_dir}")
#     return total_output_image

# Custom Metric Collector
#class CustomCollector(Collector):
#    def collect(self):
#        # yield GaugeMetricFamily('number_of_completed_tasks', 'number_of_completed_tasks', value=set_total_output_image())
#        yield GaugeMetricFamily('yolo_predict_task_status', 'True == Done, False == Not yet', value=yolo.operation_status)
#        yield GaugeMetricFamily('network_bandwidth','network_bandwidth',value=get_network_bandwidth(IPERF3_IP, IPERF3_Port))
#        yield GaugeMetricFamily('available_ram','available_ram',value=get_available_ram())
#        # c = CounterMetricFamily('my_counter_total', 'Help text', labels=['foo'])
#        # c.add_metric(['bar'], 1.7)
#        # c.add_metric(['baz'], 3.8)
#        # yield c
#REGISTRY.register(CustomCollector())


# GET - metric exporter
# Create app
app = FastAPI(debug=False)
# Add prometheus asgi middleware to route /metrics requests
#metrics_app = make_asgi_app(REGISTRY)
#app.mount("/metrics", metrics_app)

#### recovery 를 위함 #### sbkwon
@app.get("/health")
async def health_check():
    """
    The scheduler calls every 5 seconds to check if the worker is alive.
    It simply returns 200 OK, so response delay must be minimized.
    """
    return JSONResponse(status_code=200, content={"status": "ok"})
########################

@app.get("/computing_measure")
async def send_notification():
    bandwidth = get_network_bandwidth(IPERF3_IP, IPERF3_Port)
    RAM = get_available_ram()
    return {"network_latency": bandwidth, "memory" : RAM}

#@app.get("/computing_measure")
# async def send_notification():
#     return {"network_latency": BANDWIDTH, "cpu" : CPU, "memory" : MEM}

@app.get("/video_resize/{idxrange}")
async def send_notification(idxrange: str):
    start_idx, end_idx = [int(idx) for idx in idxrange.split("-")]
    mpeg.set_start_idx(start_idx)
    mpeg.set_end_idx(end_idx)

    result = mpeg.vid_resize()
    return {
        "result" : result
    }

# def chroma_query_func(idxrange) :
#     start_idx, end_idx = [int(idx) 
#                           for idx in idxrange.split("-")]
#     chroma.randomly_query(end_idx - start_idx)

# def chroma_insert_func() :
#     chroma.insert_dataset()

def image_predict_func(idxrange) :
    start_idx, end_idx = [int(idx) 
                          for idx in idxrange.split("-")]
    size = end_idx - start_idx
    compute_time = 0

    size_div = size // PROCESS_IMAGE
    size_mod = size % PROCESS_IMAGE

    for _ in range(size_div) :
        if start_idx + PROCESS_IMAGE  > 9000 :
            start_idx = 0
        yolo.set_start_idx(start_idx)
        start_idx += PROCESS_IMAGE
        yolo.set_end_idx(start_idx)
        comp_time, e = yolo.execute_yolo_predict()
        if e is not None :
            print(e)
        else :
            compute_time = compute_time + comp_time

    if start_idx + size_mod > 9000 :
        start_idx = 0
    if size_mod != 0 :
        yolo.set_start_idx(start_idx)
        yolo.set_end_idx(start_idx + size_mod)
        comp_time, e = yolo.execute_yolo_predict()
        if e is not None :
            print(e)
        else :
            compute_time = compute_time + comp_time

def monitor_resources(stop_event):
    old_net_io = psutil.net_io_counters()
    while not stop_event.is_set():
        # sbkwon
        temp = psutil.sensors_temperatures()
        first_key = list(temp.keys())[0]
        cpu_temp = temp[first_key][0].current

        # cpu_temp = psutil.sensors_temperatures()['cpu_thermal'][0].current
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent
        new_net_io = psutil.net_io_counters()
        send_packets = new_net_io.packets_sent - old_net_io.packets_sent
        recv_packets = new_net_io.packets_recv - old_net_io.packets_recv
        old_net_io = new_net_io

        cpu_temps.append(cpu_temp)
        cpu_usages.append(cpu_usage)
        memory_usages.append(memory_usage)
        disk_usages.append(disk_usage)
        network_send_packets.append(send_packets)
        network_recv_packets.append(recv_packets)

        print(f"CPU: {cpu_usage}%, Memory: {memory_usage}%, Disk: {disk_usage}%, Packets Sent: {send_packets}, Packets Received: {recv_packets}")
    print("Monitoring stopped.")

def run_function_in_thread(function, *args, **kwargs):
    func_thread = threading.Thread(target=function, args=args, kwargs=kwargs)
    func_thread.start()
    return func_thread

def log_maker(cpu_temp, cpu, memory, logname="") :
    dt = datetime.datetime.now()
    result = dt.strftime("%Y%m%d_%H%M%S")
    path_name = f"log_{logname}_{result}.txt"

    with open(path_name, "w") as f:
        f.write("cpu_temp\n")
        for i in cpu_temp :
            f.write(f"{i}\n")
        f.write("cpu\n")
        for i in cpu :
            f.write(f"{i}\n")
        f.write("memory\n")
        for i in memory :
            f.write(f"{i}\n")


def plot_resources(cpu_temp ,cpu, memory, disk, send_packets, recv_packets, plotname=""):
    fig, axs = plt.subplots(6, 1, figsize=(12, 20))  

    axs[0].plot(cpu_temp, label='CPU Temperatures (c)')
    axs[0].set_title('CPU Temperatures')
    axs[0].set_ylabel('CPU Temperatures')
    axs[0].legend()
    axs[0].grid(True)

    axs[1].plot(cpu, label='CPU Usage (%)')
    axs[1].set_title('CPU Usage Over Time')
    axs[1].set_ylabel('CPU Usage (%)')
    axs[1].legend()
    axs[1].grid(True)

    axs[2].plot(memory, label='Memory Usage (%)')
    axs[2].set_title('Memory Usage Over Time')
    axs[2].set_ylabel('Memory Usage (%)')
    axs[2].legend()
    axs[2].grid(True)

    axs[3].plot(disk, label='Disk Usage (%)')
    axs[3].set_title('Disk Usage Over Time')
    axs[3].set_ylabel('Disk Usage (%)')
    axs[3].legend()
    axs[3].grid(True)

    axs[4].plot(send_packets, label='Packets Sent')
    axs[4].set_title('Network Packets Sent Over Time')
    axs[4].set_ylabel('Packets Sent')
    axs[4].legend()
    axs[4].grid(True)

    axs[5].plot(recv_packets, label='Packets Received')
    axs[5].set_title('Network Packets Received Over Time')
    axs[5].set_ylabel('Packets Received')
    axs[5].legend()
    axs[5].grid(True)

    plt.xlabel('Time (seconds)')
    dt = datetime.datetime.now()
    result = dt.strftime("%Y%m%d_%H%M%S")
    path_name = f"resource_usage_{plotname}_{result}.png"
    plt.tight_layout()
    plt.savefig(path_name)


@app.get("/image_predict/{idxrange}")
async def send_notification(idxrange: str):
    
    stime = None
    etime = None

    if MODE == "yolo":
        stime = time.time()
        image_predict_func(idxrange)
        etime = time.time()

    # elif MODE == "chromadb_query":
    #     chroma.clinet_on()
    #     stime = time.time()
    #     chroma_query_func(idxrange)
    #     etime = time.time()

    # elif MODE == "chromadb_insert":
    #     chroma.clinet_on()
    #     stime = time.time()
    #     chroma_insert_func()
    #     etime = time.time()
    else: pass
        
    return{
        "elapsed_time" : float(etime - stime),
        "compute_time" : float(0)
    }

@app.get("/image_predict/{idxrange}/{savename}")
async def send_notification(idxrange: str, savename: str):
    
    stime = None
    etime = None

    if MODE == "yolo":
        if ISPLOT :
            stop_event = threading.Event()
            monitor_thread = threading.Thread(target=monitor_resources, args=(stop_event,))
            monitor_thread.start()

            stime = time.time()
            func_thread = run_function_in_thread(image_predict_func, idxrange)
            func_thread.join()
            etime = time.time()

            stop_event.set()
            monitor_thread.join()
            plot_resources(cpu_temps, cpu_usages, memory_usages, disk_usages, network_send_packets, network_recv_packets, plotname=savename)
            log_maker(cpu_temps, cpu_usages, memory_usages, logname=savename)
            scp_client.send_file_to_remote()
        else :
            stime = time.time()
            image_predict_func(idxrange)
            etime = time.time()

    # elif MODE == "chromadb_query":
    #     chroma.clinet_on()
    #     if ISPLOT :
    #         stop_event = threading.Event()
    #         monitor_thread = threading.Thread(target=monitor_resources, args=(stop_event,))
    #         monitor_thread.start()

    #         stime = time.time()
    #         func_thread = run_function_in_thread(chroma_query_func, idxrange)
    #         func_thread.join()
    #         etime = time.time()

    #         stop_event.set()
    #         monitor_thread.join()
    #         plot_resources(cpu_temps, cpu_usages, memory_usages, disk_usages, network_send_packets, network_recv_packets, plotname=savename)
    #         log_maker(cpu_temps, cpu_usages, memory_usages, logname=savename)
    #         scp_client.send_file_to_remote()

    #     else :
    #         stime = time.time()
    #         chroma_query_func(idxrange)
    #         etime = time.time()

    # elif MODE == "chromadb_insert":
    #     chroma.clinet_on()
    #     if ISPLOT :
    #         stop_event = threading.Event()
    #         monitor_thread = threading.Thread(target=monitor_resources, args=(stop_event,))
    #         monitor_thread.start()

    #         stime = time.time()
    #         func_thread = run_function_in_thread(chroma_insert_func)
    #         func_thread.join()
    #         etime = time.time()

    #         stop_event.set()
    #         monitor_thread.join()
    #         plot_resources(cpu_temps, cpu_usages, memory_usages, disk_usages, network_send_packets, network_recv_packets, plotname=savename)
    #         log_maker(cpu_temps, cpu_usages, memory_usages, logname=savename)
    #         scp_client.send_file_to_remote()

        # else :
        #     stime = time.time()
        #     chroma_insert_func()
        #     etime = time.time()
    else: pass
        
    return{
        "elapsed_time" : float(etime - stime),
        "compute_time" : float(0)
    }



if __name__ == "__main__":
    uvicorn.run(app, host=IP, port=Port)
