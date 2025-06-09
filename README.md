# README.md

## Environment Setup
### Requirement
```
sudo apt update
sudo apt-get install ffmpeg
sudo apt-get install iperf3

```

### 1. Clone the repository:
```
git clone https://github.com/jangscon/prom_client.git
```

### 2. Run setup.py:
- The script takes four parameters: the path to the image for prediction, the path to save the prediction results, the path to the video for resizing, and the path to save the results.
- If you don't enter a path, it is set to the current directory.
- Execute setup.sh with parameters as shown in the example below:
  ```bash
  python3 setup.py --yolo_input_path "/YOLO_IMAGE_PATH" --db_path "db_path" --dataset_path "dataset_path" --mode "yolo"

  python3 setup.py --yolo_input_path "/YOLO_IMAGE_PATH" --mode "yolo"

  python3 setup.py --db_path "db_path" --dataset_path "dataset_path" --mode "chromadb"
  ```
- After this command, Running prom_client.py will start the FastAPI application.
  ```bash
  python3 prom_client.py 
  ```

## Testing
### get metrics
- Communication is possible on port 8000. To retrieve metrics, execute the following command using curl on the client:
```bash
curl -o test.txt "http://[ServerIP]:8000/metrics/"
```
- Check test.txt to verify if metrics have been retrieved correctly.

### task requests
- To send a request to the server, execute the following command:
-   This command instructs the server to perform prediction tasks for images numbered 0 to 29.
 ```bash
curl -X GET "http://[ServerIP]:8000/image_predict/0-30"
```

- This command instructs the server to perform a size reduction operation on videos 0 through 29.
```bash
curl -X GET "http://[ServerIP]:8000/video_resize/0-30"
```