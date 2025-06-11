# MinRes interface for viewing ultrasounds

This code is to create an ultrasound display viewer. Clinicians will be able to view different resolutions of ultrasounds and make predictions as to what the label is.

## Prerequisites
You must have Python installed on the system. Download the latest version of Python from [python.org](https://www.python.org/).  
During installation, be sure to select:
- _Add Python to Path_
- _Ensure_ `pip` _is included_
  
To verify installation, open up a terminal window and type
```
python --version
```

## Installation
First, clone the repository:
```
git clone https://github.com/timohromadka/minres_interface.git
```

Then, setup the python environment
```
python -m venv minres_venv
.\minres_venv\Scripts\activate
pip install pyqt5 pandas opencv-python-headless
```

If you are on LINUX, then write this in terminal to enable the GUI
```
export QT_QPA_PLATFORM=offscreen 
```
(to solve a bug: https://github.com/NVlabs/instant-ngp/discussions/300)

## Running

### Data Preparation
First, we need to prepare the data. 
1) Download the ultrasounds (.mp4) into the `ultrasounds/` directory
2) Put all healthy ultrasound scans into `ultrasounds/healthy_original` and all unhealthy into `ultrasounds/unhealthy_original`
3) Crop the videos to anonymize its data
   ```
   python crop_data.py --src_dir ultrasounds/healthy_original --dst_dir ultrasounds/healthy
   python crop_data.py --src_dir ultrasounds/unhealthy_original --dst_dir ultrasounds/unhealthy
   ```
4) Next, for each video create all of its resolution copies using the following command:
   ```
   python prepare_data.py --data-path ultrasounds --resolutions "320x240, 480x320, 640x480, 800x600, 1024x768, 1280x720"
   ```

### Running the Experiment
Now, we can run the experiment and launch the UI
```
python run.py --video_dir ultrasounds
```

## Details of Experiment
- randomize order of displaying ultrasound videos
    - this includes random flips
    - viewing healthy and unhealthy samples in random order
    - viewing samples in increasing order of resolution (after 3 consecutive correct identifications, that sample isn't viewed anymore)
        - 320x240
        - 480x320
        - 640x480 (standard)
        - 800x600
        - 1024x768 (standard)
        - 1280x720 (standard)
- saving and logging of results
    - time taken
    - prediction
 

### For Cropping (Temporary)
```
brew install ffmpeg
```

```
ffmpeg -i INPUT_VIDEO_PATH.mp4 -filter:v "crop=in_w-LEFT-RIGHT:in_h-TOP-BOTTOM:LEFT:TOP" OUTPUT_VIDEO_PATH.mp4
```

```
ffmpeg -i INPUT_VIDEO_PATH.mp4 -filter:v "crop=in_w-0-0:in_h-74-0:0:0" OUTPUT_VIDEO_PATH.mp4
```

```
nano crop_videos.sh
```

```
#!/bin/bash

input_dir=$1
output_dir=$2
top=$3
left=$4
bottom=$5
right=$6
# depth of recursive search, defaults to 0
depth=${7:-0}

mkdir -p "$output_dir"

if [[ "$depth" -gt 0 ]]; then
    depth_option="-maxdepth $depth"
else
    depth_option=""
fi

# Recursively find videos in directory
counter=0
find "$input_dir" $depth_option -type f \( -iname "*.mp4" -o -iname "*.avi" \) | while IFS= read -r filepath; do
    filename=$(basename "$filepath")
    filename_noext="${filename%.*}"
    extension="${filename##*.}"
    
    # Create output directory structure matching input
    relative_path="${filepath#$input_dir/}"
    relative_dir=$(dirname "$relative_path")
    mkdir -p "$output_dir/$relative_dir"
    
    output_path="$output_dir/$relative_dir/${filename_noext}_anonymized.${extension}"
    
    # Run ffmpeg crop command
    ffmpeg -i "$filepath" -filter:v "crop=in_w-${left}-${right}:in_h-${top}-${bottom}:${left}:${top}" "$output_path" -y -loglevel error
    
    # Increment counter and print status every 100 videos
    counter=$((counter + 1))
    if (( counter % 100 == 0 )); then
        echo "Anonymized $counter videos"
    fi
done

echo "All videos saved to $output_dir"
```

```
Control + O
Enter
Control + X
```

```
chmod +x crop_videos.sh
```

```
./crop_videos.sh INPUT_DIRECTORY OUTPUT_DIRECTORY 74 0 0 0 0
```
