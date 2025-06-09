import os

def count_files_in_directory(directory):
    try:
        # 해당 디렉토리의 파일 리스트를 얻어옴
        files = os.listdir(directory)
        # 파일의 개수를 세어 반환
        return len(files)
    except Exception as e:
        print(f"Error counting files in directory {directory}: {e}")
        return 0