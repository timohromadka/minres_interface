# MinRes interface for viewing ultrasounds

This code is to create an ultrasound display viewer
- randomize order of displaying ultrasound videos
    - this includes random flips
    - viewinghealthy and unhealthy samples in random order
    - viewing samples in increasing order of resolution (after 3 consecutive correct identifications, that samples isn't viewed anymore)
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

## Installation
```
python -m venv minres_venv
.\minres_venv\Scripts\activate
pip install pyqt5 opencv-python-headless pandas
```

Then, run this in console:
```
export QT_QPA_PLATFORM=offscreen 
```
(to solve a bug: https://github.com/NVlabs/instant-ngp/discussions/300)
