import socket
import argparse
import pip
import os
import subprocess


def install(package):
    if hasattr(pip, 'main'):
        pip.main(['install', package])
    else:
        pip._internal.main(['install', package])

def create_directory(directory_path):
    # 디렉토리가 존재하지 않으면 생성
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"디렉토리 생성: {directory_path}")
    else:
        print(f"디렉토리 이미 존재: {directory_path}")

def get_current_directory():
    return str(os.getcwd())

install("prometheus-client")
install("uvicorn")
install("fastapi")
install("ultralytics")
install("ffmpeg-python")
install("iperf3")
install("paramiko")
install("scp")
#install('chromadb==0.5.0')

subprocess.Popen(['sudo', 'apt-get', 'install', "iperf3"])


parser = argparse.ArgumentParser()
parser.add_argument("--yolo_input_path", type=str, default="/uploads/images")
parser.add_argument("--yolo_output_path", type=str, default="/uploads")
parser.add_argument("--ffmpeg_input_path", type=str, default=".")
parser.add_argument("--ffmpeg_output_path", type=str, default=".")
parser.add_argument("--port",type=int, default=8000)
parser.add_argument("--process_img",type=int, default=1)
parser.add_argument('--plotting', dest='isPlot', action='store_true')
parser.add_argument('--no-plotting', dest='isPlot', action='store_false')
parser.add_argument('--dest-', dest='isPlot', action='store_false')
parser.set_defaults(isPlot=False)

parser.add_argument("--db_path", type=str, default="/uploads")
parser.add_argument("--dataset_path", type=str, default=".")
parser.add_argument("--collection_name", type=str, default="lfw_faces")

# mode : yolo, chromadb_query , chromadb_insert
parser.add_argument("--mode", type=str, default="yolo")

args = parser.parse_args()

# IP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
IP = s.getsockname()[0]
s.close()

YOLO_INPUT_PATH = args.yolo_input_path
YOLO_OUTPUT_PATH = args.yolo_output_path
FFMPEG_INPUT_PATH = args.ffmpeg_input_path
FFMPEG_OUTPUT_PATH = args.ffmpeg_output_path
Port = args.port
PROCESS_IMAGE = args.process_img
ISPLOT = args.isPlot
DB_PATH = args.db_path
DATASET_PATH = args.dataset_path
COLLECTION_NAME = args.collection_name
MODE = args.mode

# if MODE == "yolo":
#     create_directory(YOLO_OUTPUT_PATH)
#     create_directory(f"{YOLO_OUTPUT_PATH}/predict")
#     create_directory(FFMPEG_OUTPUT_PATH)

# from computing_measure import get_available_ram, get_network_bandwidth


# bandwidth = get_network_bandwidth("155.230.36.27", 5202)
# mem = get_available_ram()



with open("config.py","w") as f:
    f.write(f'YOLO_INPUT_PATH = "{YOLO_INPUT_PATH}"\n')
    f.write(f'YOLO_OUTPUT_PATH = "{YOLO_OUTPUT_PATH}"\n')
    f.write(f'FFMPEG_INPUT_PATH = "{FFMPEG_INPUT_PATH}"\n')
    f.write(f'FFMPEG_OUTPUT_PATH = "{FFMPEG_OUTPUT_PATH}"\n')
    f.write(f'BANDWIDTH = 1\n')
    f.write(f'MEM = 1\n')
    f.write(f'IP = "{IP}"\n')
    f.write(f'Port = {Port}\n')
    f.write(f'IPERF3_IP = "155.230.36.27"\n')
    f.write(f'IPERF3_Port = 5201\n')
    f.write(f'PROCESS_IMAGE = {PROCESS_IMAGE}\n')
    f.write(f'ISPLOT = {ISPLOT}\n')
    f.write(f'DB_PATH = "{DB_PATH}"\n')
    f.write(f'DATASET_PATH = "{DATASET_PATH}"\n')
    f.write(f'COLLECTION_NAME = "{COLLECTION_NAME}"\n')
    f.write(f'MODE = "{MODE}"\n')
