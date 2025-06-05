import argparse
import cv2
import os
from pathlib import Path

def crop_video(input_path, output_path, crop_top, crop_bottom, crop_left, crop_right):
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        print(f"Failed to open {input_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    new_width = width - crop_left - crop_right
    new_height = height - crop_top - crop_bottom

    if new_width <= 0 or new_height <= 0:
        print(f"Video {input_path} is too small to crop the specified dimensions")
        cap.release()
        return

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (new_width, new_height))

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cropped_frame = frame[crop_top:height - crop_bottom, crop_left:width - crop_right, :]
        out.write(cropped_frame)
        frame_count += 1

    cap.release()
    out.release()
    print(f"Processed {frame_count} frames from {input_path.name} -> {output_path.name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crop videos in a directory and save them to another directory.")
    parser.add_argument("--src_dir", type=str, required=True, help="Source directory containing original videos.")
    parser.add_argument("--dst_dir", type=str, required=True, help="Destination directory for cropped videos.")
    parser.add_argument("--crop_top", type=int, default=74, help="Height to crop from the top of the video.")
    parser.add_argument("--crop_bottom", type=int, default=0, help="Height to crop from the bottom of the video.")
    parser.add_argument("--crop_left", type=int, default=0, help="Width to crop from the left of the video.")
    parser.add_argument("--crop_right", type=int, default=0, help="Width to crop from the right of the video.")

    args = parser.parse_args()

    src_dir = Path(args.src_dir)
    dst_dir = Path(args.dst_dir)
    crop_top = args.crop_top
    crop_bottom = args.crop_bottom
    crop_left = args.crop_left
    crop_right = args.crop_right

    dst_dir.mkdir(parents=True, exist_ok=True)

    video_exts = {".mp4", ".MP4", ".avi", ".AVI"}

    for file_path in src_dir.iterdir():
        if file_path.suffix in video_exts:
            output_name = file_path.stem + "_cropped" + file_path.suffix
            output_path = dst_dir / output_name

            crop_video(file_path, output_path, crop_top, crop_bottom, crop_left, crop_right)
