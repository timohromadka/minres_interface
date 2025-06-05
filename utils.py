import argparse
import os
from collections import defaultdict, namedtuple
import cv2
import heapq
import logging
import random
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Utils")

# ===================================
# VIDEO QUEUE
# ===================================
Video = namedtuple("Video", ["filename", "original_filename", "resolution", "label", "predicted_label", "explanation"])

class VideoSample:
    def __init__(self, filepath, resolution, label=None):
        self.filepath = filepath
        self.resolution = resolution
        self.predicted_label = None
        self.explanation = None

        self.filename = self.filepath.split('/')[-1]
        self.label = label if label else self.get_label()
        # self.transform = random.choice(['none', 'h_flip', 'v_flip', 'hv_flip'])
        self.transform = 'none'
        self.original_filename = os.path.basename(self.filepath).split("_")[0] + ".mp4" # extract the name before the suffix, with .mp4 at the end

    def get_label(self):
        return os.path.basename(os.path.dirname(self.filepath))

    def __repr__(self):
        return (f"VideoSample(filename={self.filename}, resolution={self.resolution}, "
                f"label={self.label}, predicted_label={self.predicted_label}, explanation={self.explanation})")

    def __lt__(self, other):
        if not isinstance(other, VideoSample):
            return NotImplemented
        return (self.resolution[0]*self.resolution[1]) < (other.resolution[0]*other.resolution[1])

class VideoQueue:
    def __init__(self, videos):
        self.heap = []  # Min-heap
        self.videos = videos
        self.processed_resolutions = defaultdict(set)
        self.successful_predictions = defaultdict(int) 

        for video in self.videos:
            heapq.heappush(self.heap, (video.resolution, video)) 

    def get_next_video(self):
        """Fetch the next video to process based on priority."""
        while self.heap:
            resolution, video = heapq.heappop(self.heap)

            # Skip videos with successful predictions >= 3
            if self.successful_predictions[video.original_filename] >= 3:
                video.predicted_label = "N/A"
                video.explanation = "Lower resolutions predicted successfully 3x"
                # print(f"Discarding higher resolution: {video}")
                continue

            # Check if all lower resolutions have been processed
            if all(res[0]*res[1] < resolution[0]*resolution[1] for res in self.processed_resolutions[video.original_filename]):
                self.processed_resolutions[video.original_filename].add(resolution)
                return video

        return None

    def update_predictions(self, video, predicted_label):
        """Update the video with predicted label."""
        video.predicted_label = predicted_label
        
        if video.label == predicted_label:
            self.successful_predictions[video.original_filename] += 1
        else:
            self.successful_predictions[video.original_filename] = 0  # Reset if prediction fails

        return video

# ===================================
# ARGS UTILITY
# ===================================
def parse_resolutions(res_str):
    """
    Parse a resolution string into a list of (width, height) tuples.
    Example input: "320x240,480x320,640x480"
    Output: [(320, 240), (480, 320), (640, 480)]
    """
    try:
        resolutions = []
        for item in res_str.split(','):
            width, height = map(int, item.split('x'))
            resolutions.append((width, height))
        return resolutions
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Resolutions must be a comma-separated list of WIDTHxHEIGHT pairs, e.g., '320x240,480x320'")
    
# ===================================
# VIDEO PROCESSING UTILITY
# ===================================
def make_resolution_copy(file, resolution):
    file_dir, file_name = os.path.split(file)
    file_base, file_ext = os.path.splitext(file_name)
    
    cap = cv2.VideoCapture(file)
    cap.open(file)
    if not cap.isOpened():
        print(f"Error: Could not open video file {file}")
        return

    width, height = resolution
    output_file = os.path.join(file_dir, f"{file_base}_{width}x{height}{file_ext}")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS)
    out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        resized_frame = cv2.resize(frame, (width, height))
        out.write(resized_frame)

    out.release()
    logger.info(f"\nCompressed video saved at {output_file}")

    cap.release()

def is_original(file):
    """
    Check if a video doesn't have a resolution suffix, meaning it's an original video to be processed.
    """
    # Regular expression to check for resolution suffix {int}x{int}
    resolution_pattern = re.compile(r"\d+x\d+")
    
    if resolution_pattern.search(file):
        logger.info(f'File <{file}> appears to have a resolution suffix and may already be processed.')
        return False
    
    else: return True