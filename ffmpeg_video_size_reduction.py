import ffmpeg
import os

class FFMpegJob:
    def __init__(self):
        self.operation_status = False
        self.input_path = None
        self.output_path = None
        self.start_idx = None
        self.end_idx = None

    def set_input_path(self,input_path):
        self.input_path = input_path   
    def set_output_path(self,output_path):
        self.output_path = output_path    
    def set_start_idx(self,start_idx):
        self.start_idx = start_idx
    def set_end_idx(self,end_idx):
        self.end_idx = end_idx
    def set_end_idx(self,end_idx):
        self.end_idx = end_idx
    
    def switch_operation_status(self):
        self.operation_status += 1
    def get_video_list(self, save_file="mylist.txt"):
        return os.listdir(self.input_path)[self.start_idx:self.end_idx]
        
    def vid_resize(self):
        try:
            vid_list = self.get_video_list()
            for vid in vid_list :
                ffmpeg.input(f"{self.input_path}/{vid}").output(f"{self.output_path}/output_{vid}", vf='scale=640:480').run()
            self.switch_operation_status()
            return True
        except Exception as e:
            return False


    
