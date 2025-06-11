import argparse
import os
import cv2
import logging
import re

import utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Prepare Data")

def get_resolution(file_path):
    """Get the resolution of a video file."""
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {file_path}")
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return width, height


def main(args):
    for dir in args.data_directories:
        original_files = []
        for file in os.listdir(dir):
            if file.endswith(('.mp4', '.avi', '.MP4', '.AVI')):
                if utils.is_original(file):
                    file_path = os.path.join(dir, file)
                    original_files.append(file)
                    
        requested_files = []
        for _file in original_files:
            for sf in args.scale_factors:
                x_res, y_res = get_resolution(os.path.join(dir, _file))
                new_x_res = int(x_res*sf)
                new_y_res = int(y_res*sf)
                file_without_extension = _file.rsplit('.', 1)[0]
                formatted_filename = f"{file_without_extension}_{new_x_res}x{new_y_res}.mp4"
                requested_files.append((formatted_filename, _file, (new_x_res, new_y_res)))
                
        files_to_make = [(cf, of, r) for cf, of, r in requested_files if cf not in os.listdir(dir)]
        for _, original_file, target_res in files_to_make:
            utils.make_resolution_copy(os.path.join(dir, original_file), target_res)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Set up ultrasound data before running GUI tests.')
    parser.add_argument("--data-directories", type=str, nargs="+", default=["ultrasounds/healthy", "ultrasounds/unhealthy"], help="Directory in which ultrasound videos are located. One path for each label.")
    parser.add_argument("--scale-factors", type=float, nargs="+", default=[0.25, 0.4, 0.55, 0.7, 0.85, 1], help="Specify the resolution compression scales")
    
    args = parser.parse_args()
    main(args)