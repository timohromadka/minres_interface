# TODO
# add number to each ultrasound video displayed
# this number (index) will also get logged to the CSV
# just in case the clinician makes a mistake and wants to edit the response

import argparse
import datetime
import sys
import os
import random
import cv2
import pandas as pd
import logging

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QSlider, QVBoxLayout, QHBoxLayout,
    QWidget, QLabel, QStyle
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage

from utils import VideoSample, VideoQueue, parse_resolutions

class UltrasoundAssessment(QMainWindow):
    def __init__(self, video_dir, resolutions):
        super().__init__()
        self.video_dir = video_dir
        self.log_file = f"assessment_log_{datetime.datetime.now().strftime('%H_%M_%S')}.csv"
        self.resolutions = resolutions
        self.current_video = None
        self.current_resolution_idx = 0
        self.video_order = []
        self.video_transform = {}
        self.correct_predictions = {}
        self.start_time = None
        self.current_video_order = 1 # start at the first video

        self.video_queue = self.get_video_queue()
        self.df = self.create_df()
        self.init_ui()
        
    class CorruptFileException(Exception):
        """Custom exception for corrupt video files."""
        pass
        

    def get_video_queue(self):
        self.videos = []
        for category in ['healthy', 'unhealthy']:
            folder_path = os.path.join(self.video_dir, category)
            for file in os.listdir(folder_path):
                if file.endswith('.mp4'):
                    video_path = os.path.join(folder_path, file)
                    res_w = cv2.VideoCapture(video_path).get(cv2.CAP_PROP_FRAME_WIDTH)
                    res_h = cv2.VideoCapture(video_path).get(cv2.CAP_PROP_FRAME_HEIGHT)
                    # instantiate object
                    if res_w == 0 or res_h == 0:
                        raise self.CorruptFileException(f"Corrupt file detected: {video_path}")
                    video_object = VideoSample(video_path, (res_w, res_h))
                    self.videos.append(video_object)
                    
        video_queue = VideoQueue(self.videos)
        return video_queue
    
    
    def create_df(self):
        if not os.path.exists(self.log_file):
            pd.DataFrame(columns=[
                "video_name", "view_order", "resolution", "prediction", "time_taken", "true_label", "time_stamp", "explanation"
            ]).to_csv(self.log_file, index=False)
            
        # self.video_order = random.sample(self.videos, len(self.videos))
        # self.video_transform = {
        #     video[0]: random.choice(['none', 'h_flip', 'v_flip', 'hv_flip']) for video in self.video_order
        # }
        # self.correct_predictions = {video[0]: 0 for video in self.video_order}



    def init_ui(self):
        self.setWindowTitle("Ultrasound Assessment")
        self.showMaximized()
        # self.showFullScreen()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        
        # Top-Right Video Order Label
        self.video_order_label = QLabel(str(self.current_video_order))
        self.video_order_label.setStyleSheet("color: gray; font-size: 20px;")
        self.video_order_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        
        # buttons
        self.healthy_btn = QPushButton("Healthy")
        self.unhealthy_btn = QPushButton("Unhealthy")
        self.cant_tell_btn = QPushButton("Can't Tell")

        for btn in [self.healthy_btn, self.unhealthy_btn, self.cant_tell_btn]:
            btn.setStyleSheet(
                "border-radius: 25px; padding: 10px; font-size: 18px; background-color: lightblue;"
            )
            btn.setFixedSize(150, 50)
            btn.setCursor(Qt.PointingHandCursor)

        self.healthy_btn.clicked.connect(lambda: self.log_prediction("Healthy"))
        self.unhealthy_btn.clicked.connect(lambda: self.log_prediction("Unhealthy"))
        self.cant_tell_btn.clicked.connect(lambda: self.log_prediction("Can't Tell"))
        

        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.toggle_playback)

        # video
        self.slider = QSlider(Qt.Horizontal)
        # self.slider.sliderMoved.connect(self.seek_video)
        self.slider.setMinimum(0)
        self.slider.sliderPressed.connect(self.stop_video)
        self.slider.sliderReleased.connect(self.seek_video)  # Update on release
        self.slider.setCursor(Qt.PointingHandCursor)
        self.slider.setStyleSheet("""
            QSlider::handle:horizontal {
                background-color: #085a9c;  /* Handle color */
                width: 30px;  /* Increased handle width */
                height: 30px;  /* Increased handle height */
                border-radius: 15px;  /* Makes it a rounded circle */
                margin: -20px 0;  /* Expands clickable area */
            }
            QSlider::handle:horizontal:pressed {
                background-color: #499dd7;  /* Lighter blue when pressed */
            }
            QSlider::groove:horizontal {
                background-color: #d3d3d3;  /* Slider track color */
                height: 10px;  /* Groove height */
                border-radius: 5px;  /* Rounded edges */
            }
            QSlider::sub-page:horizontal {
                background-color: #0078d7;  /* Filled section color */
                border-radius: 5px;
            }
            QSlider::groove:horizontal:hover {
                background-color: #e0e0e0;  /* Highlight groove when hovered */
            }
        """)


        self.backward_btn = QPushButton("⏪")
        self.forward_btn = QPushButton("⏩")
        self.backward_btn.clicked.connect(self.jump_backward)
        self.forward_btn.clicked.connect(self.jump_forward)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.healthy_btn)
        button_layout.addWidget(self.unhealthy_btn)
        button_layout.addWidget(self.cant_tell_btn)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.video_order_label)
        controls_layout.addWidget(self.backward_btn)
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.forward_btn)
        controls_layout.addWidget(self.slider)

        main_layout = QVBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.video_label)
        main_layout.addLayout(controls_layout)

        self.central_widget.setLayout(main_layout)
        self.load_next_video()

    def load_next_video(self):
        self.current_video  = self.video_queue.get_next_video() # returns a VideoSample object
        if not self.current_video:
            self.show_end_screen()
            return
        self.start_time = pd.Timestamp.now()
        
        # display index 
        self.video_order_label.setText(str(self.current_video_order))

        self.cap = cv2.VideoCapture(self.current_video.filepath)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.current_video.resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.current_video.resolution[1])

        self.slider.setMaximum(int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return

        if self.current_video.transform == "h_flip":
            frame = cv2.flip(frame, 1)
        elif self.current_video.transform == "v_flip":
            frame = cv2.flip(frame, 0)
        elif self.current_video.transform == "hv_flip":
            frame = cv2.flip(frame, -1)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame.shape
        qimg = QImage(frame.data, w, h, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qimg))

        self.slider.setValue(int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)))

    def toggle_playback(self):
        if self.timer.isActive():
            self.timer.stop()
            self.play_btn.setText("Play")
        else:
            self.timer.start(30)
            self.play_btn.setText("Pause")
            
    def stop_video(self):
        self.timer.stop()
        self.play_btn.setText("Play")
        
    def seek_video(self):
        frame_idx = self.slider.value()
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        if self.timer.isActive(): # we want to stop the video, so toggle only if video is playing
            self.toggle_playback()
        self.update_frame()
        self.toggle_playback() 

    def jump_backward(self):
        current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, current_frame - self.cap.get(cv2.CAP_PROP_FPS)))
        self.update_frame()

    def jump_forward(self):
        current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame + self.cap.get(cv2.CAP_PROP_FPS))
        self.update_frame()

    def log_prediction(self, prediction, explanation="Not Implemented Yet"):
        time_taken = (pd.Timestamp.now() - self.start_time).total_seconds()
        # TODO explanation
        self.video_queue.update_predictions(self.current_video, prediction, explanation)

        log_data = {
            "video_name": self.current_video.filename,
            "view_order": self.current_video_order,
            "resolution": self.current_video.resolution,
            "prediction": prediction,
            "time_taken": time_taken,
            "true_label": self.current_video.label,
            "time_stamp": datetime.datetime.now(),
            "explanation": self.current_video.explanation
        }
        pd.DataFrame([log_data]).to_csv(self.log_file, mode="a", header=False, index=False)
        
        self.current_video_order += 1
        self.cap.release()
        self.timer.stop()

        # Load the next video
        self.load_next_video()

    def show_end_screen(self):
        self.timer.stop()
        self.central_widget.deleteLater()
        end_widget = QWidget()
        layout = QVBoxLayout()
        label = QLabel("Thank You")
        label.setStyleSheet("color: black; font-size: 48px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        exit_btn = QPushButton("Exit")
        exit_btn.setStyleSheet("border-radius: 25px; padding: 10px; font-size: 18px; background-color: lightgreen")
        exit_btn.setCursor(Qt.PointingHandCursor)
        exit_btn.clicked.connect(self.close)
        layout.addWidget(exit_btn)
        layout.setAlignment(Qt.AlignCenter)

        end_widget.setLayout(layout)
        end_widget.setStyleSheet("background-color: white;")
        self.setCentralWidget(end_widget)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Set up ultrasound data before running GUI tests.')
    parser.add_argument("--video_dir", type=str, default="ultrasounds", help="Directory in which ultrasound videos are located.")
    parser.add_argument("--resolutions", type=parse_resolutions, default=[(320, 240), (480, 320), (640, 480), (800, 600), (1024, 768), (1280, 720)], help="Specify the resolution for compression, e.g. [(420,300), (800,600)].")
    
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    window = UltrasoundAssessment(args.video_dir, args.resolutions)
    window.show()
    sys.exit(app.exec_())
