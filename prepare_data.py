import argparse
import os
import cv2
import logging
import re

import utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Prepare Data")


def main(args):
    for label in ['healthy', 'unhealthy']:
        original_files = []
        label_path = os.path.join(args.data_path, label)
        for file in os.listdir(label_path):
            if utils.is_original(file):
                file_path = os.path.join(label_path, file)
                original_files.append(file)
                
        requested_files = []
        for _file in original_files:
            for res in args.resolutions:
                file_without_extension = _file.rsplit('.', 1)[0]
                formatted_filename = f"{file_without_extension}_{res[0]}x{res[1]}.mp4"
                requested_files.append((formatted_filename, _file, res)) # compressed filename, original filename, target resolution
                
        files_to_make = [(cf, of, r) for cf, of, r in requested_files if cf not in os.listdir(label_path)]
        for _, original_file, target_res in files_to_make:
            utils.make_resolution_copy(os.path.join(label_path, original_file), target_res)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Set up ultrasound data before running GUI tests.')
    parser.add_argument("--data-path", type=str, default="ultrasounds", help="Directory in which ultrasound videos are located.")
    parser.add_argument("--resolutions", type=utils.parse_resolutions, default=[(320, 240), (480, 320), (640, 480), (800, 600), (1024, 768), (1280, 720)], help="Specify the resolution for compression, e.g. [(420,300), (800,600)].")
    
    args = parser.parse_args()
    main(args)