# MinRes interface for viewing ultrasounds

This code is to create an ultrasound display viewer
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
    - what the prediction was


## Questions:
- will resizing ruin the proportions, thus intuition of clinicans? shall we keep proportion of original video (whatever that is)

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
```
python -m venv minres_venv
.\minres_venv\Scripts\activate
pip install pyqt5 opencv-python-headless pandas
```

If you are on LINUX, then write this in terminal
```
export QT_QPA_PLATFORM=offscreen 
```
(to solve a bug: https://github.com/NVlabs/instant-ngp/discussions/300)
