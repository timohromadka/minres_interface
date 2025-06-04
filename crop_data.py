import argparse
import cv2
import os
from pathlib import Path

def crop_video_top(input_path, output_path, crop_y):
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        print(f"Failed to open {input_path}")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    new_height = height - crop_y
    if new_height <= 0:
        print(f"Video {input_path} is too short to crop {crop_y} rows")
        cap.release()
        return
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, new_height))

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cropped_frame = frame[crop_y:, :, :]
        out.write(cropped_frame)
        frame_count += 1
    
    cap.release()
    out.release()
    print(f"Processed {frame_count} frames from {input_path.name} -> {output_path.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crop videos in a directory and save them to another directory.")
    parser.add_argument("--src_dir", type=str, required=True, help="Source directory containing original videos.")
    parser.add_argument("--dst_dir", type=str, required=True, help="Destination directory for cropped videos.")
    parser.add_argument("--crop_height", type=int, default=74, help="Height to crop from the top of the video.")

    args = parser.parse_args()

    src_dir = Path(args.src_dir)
    dst_dir = Path(args.dst_dir)
    crop_height = args.crop_height

    dst_dir.mkdir(parents=True, exist_ok=True)

    video_exts = {".mp4", ".MP4", ".avi", ".AVI"}

    for file_path in src_dir.iterdir():
        if file_path.suffix in video_exts:
            output_name = file_path.stem + "_cropped" + file_path.suffix
            output_path = dst_dir / output_name

            crop_video_top(file_path, output_path, crop_height)

