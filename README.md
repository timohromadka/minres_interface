# MinRes interface for viewing ultrasounds

This code is to create an ultrasound display viewer. Clinicians will be able to view different resolutions of ultrasounds and make predictions as to what the label is.

<img width="1000" alt="image" src="https://github.com/user-attachments/assets/f4ca8acf-ace7-41d9-9dcc-d833232023fa" />

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
