# TODO
# make layout smaller/add scaling feature. During the largest resolution the video doesnt fit anymore on a regular laptop screen

import argparse
from collections import deque
import datetime
import sys
import os
import random
import re
import cv2
import pandas as pd
import logging

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QSlider, QVBoxLayout, QHBoxLayout,
    QWidget, QLabel, QStyle
)
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QPixmap, QImage

from utils import VideoSample, VideoQueue, parse_resolutions

class UltrasoundAssessment(QMainWindow):
    def __init__(self, video_dir):
        super().__init__()
        self.video_dir = video_dir
        self.log_file = f"assessment_log_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        # self.resolutions = resolutions
        self.previous_videos = deque()
        self.current_video = None
        self.current_resolution_idx = 0
        self.video_order = []
        self.video_transform = {}
        self.correct_predictions = {}
        self.start_time = None
        self.current_video_order = 1 # start at the first video
        
        # for cant tell option
        self.cant_tell_details_shown = False
        self.selected_reasons = []

        self.video_queue = self.get_video_queue()
        self.df = self.create_df()
        self.init_ui()
        

    def get_video_queue(self):
        self.videos = []
        for category in ['healthy', 'unhealthy']:
            folder_path = os.path.join(self.video_dir, category)
            for file in os.listdir(folder_path):
                if file.endswith(('.mp4', '.MP4', '.AVI', '.avi')):
                    # only select the processed resolution videos
                    if re.search(r"\d+x\d+", file):
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
                "video_name", "view_order", "resolution", "prediction", "time_taken", "true_label", "time_stamp"
            ]).to_csv(self.log_file, index=False)
            
        # self.video_order = random.sample(self.videos, len(self.videos))
        # self.video_transform = {
        #     video[0]: random.choice(['none', 'h_flip', 'v_flip', 'hv_flip']) for video in self.video_order
        # }
        # self.correct_predictions = {video[0]: 0 for video in self.video_order}

    def wheelEvent(self, event):
        self.slider.valueChanged.connect(self.seek_video_wheel_scroll)
        # Check the scroll direction: positive for up, negative for down
        delta = event.angleDelta().y()

        self.stop_video()
        step_size = 8
        if delta > 0:
            # Scroll up: increase the slider value
            self.slider.setValue(self.slider.value() + step_size)
        elif delta < 0:
            # Scroll down: decrease the slider value
            self.slider.setValue(self.slider.value() - step_size)

        # Prevent further propagation of the event (optional)
        event.accept()
        self.slider.valueChanged.disconnect(self.seek_video_wheel_scroll)


    def init_ui(self):
        self.setWindowTitle("Ultrasound Assessment")
        self.showMaximized()
        # self.showFullScreen()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212; /* Dark background */
            }
            QLabel {
                color: #ffffff; /* White text */
            }
            QPushButton {
                background-color: #2c2c2c; /* Dark button background */
                color: #ffffff; /* White button text */
                border-radius: 5px;
                padding: 10px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #3a3a3a; /* Slightly lighter for hover */
            }
            QSlider::groove:horizontal {
                background-color: #2c2c2c; /* Slider track color */
                height: 10px;
            }
            QSlider::handle:horizontal {
                background-color: #3a3a3a; /* Slider handle color */
                border: 1px solid #ffffff;
                width: 20px;
                height: 20px;
                border-radius: 10px;
            }
            QSlider::sub-page:horizontal {
                background-color: #0078d7; /* Filled section color */
            }
        """)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        
        # Top-Right Video Order Label
        self.video_order_label = QLabel(str(self.current_video_order))
        self.video_order_label.setStyleSheet("color: gray; font-size: 20px;")
        self.video_order_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        
        # buttons
        self.play_btn = QPushButton("Pause")
        self.play_btn.setFixedSize(80, 50)
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.clicked.connect(self.toggle_playback)
        
        
        self.backward_btn = QPushButton("<<")
        self.forward_btn = QPushButton(">>")
        self.backward_btn.setCursor(Qt.PointingHandCursor)
        self.forward_btn.setCursor(Qt.PointingHandCursor)
        self.backward_btn.clicked.connect(self.jump_backward)
        self.forward_btn.clicked.connect(self.jump_forward)
        
        self.healthy_btn = QPushButton("No Adenomyosis Signs Present")
        self.unhealthy_btn = QPushButton("Adenomyosis Signs Present")
        self.cant_tell_btn = QPushButton("Can't Tell")

        for btn in [self.healthy_btn, self.unhealthy_btn, self.cant_tell_btn]:
            btn.setStyleSheet(
                """
                QPushButton {
                    border-radius: 5px;
                    border: 2px solid #e3e3e3;
                    padding: 10px;
                    font-size: 24px;
                    background-color: #d4d4d4;
                    color: #404040;
                    
                }
                QPushButton:hover {
                    background-color: gray;
                    color: white;
                }
                
                QPushButton:checked {
                    background-color: #7b7c8c;
                    color: white;
                }
                QPushButton:checked:hover {
                    background-color: #616375;
                    color: white;
                }
                """
            )
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setFixedSize(360, 60)

        # styles for healthy and unhealthy
        healthy_btn_style = """
            QPushButton {
                background-color: #a0c99b;
                color: #3b3b3b;
            }
            QPushButton:hover {
                background-color: #769971;
            }
            """
        current_stylesheet = self.healthy_btn.styleSheet()
        self.healthy_btn.setStyleSheet(current_stylesheet + healthy_btn_style)

        unhealthy_btn_style ="""
            QPushButton {
                background-color: #cc9797;
                color: #3b3b3b;

            }
            QPushButton:hover {
                background-color: #a37474;
            }
            """
        current_stylesheet = self.unhealthy_btn.styleSheet()
        self.unhealthy_btn.setStyleSheet(current_stylesheet + unhealthy_btn_style)

        self.healthy_btn.clicked.connect(lambda: self.log_prediction("healthy"))
        self.unhealthy_btn.clicked.connect(lambda: self.log_prediction("unhealthy"))
        self.cant_tell_btn.clicked.connect(lambda: self.toggle_reasons_availability())

        self.reason_buttons = [
            QPushButton(reason)
            for reason in [
                "Need\nMore\nGain",
                "Too\nBlurry",
                "Image\nArtifact",
                "Poor\nContrast",
                "Video\nToo Fast",
                "Shadows\nObscuring\nView",
                "Incomplete\nEndometrium\nView",
                "Need Better\nMyometrium\nView",
                "Need\nDoppler\nImaging",
                "Other",
            ]
        ]
        for btn in self.reason_buttons:
            btn.setCheckable(True)
            btn.clicked.connect(self.toggle_reason)
    
            
        self.proceed_btn = QPushButton("Proceed")
        self.proceed_btn.setStyleSheet("""
            QPushButton {
                background-color: lightblue;
                font-size: 18px;
                padding: 10px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #5aa0d8;  /* darker light blue on hover */
            }
        """)
        self.proceed_btn.clicked.connect(lambda: self.log_prediction("Can't Tell: " + ", ".join(self.selected_reasons)))
        self.proceed_btn.clicked.connect(lambda: self.toggle_reasons_availability())
        self.proceed_btn.clicked.connect(lambda: self.switch_off_cant_tell())
        
        # video
        self.slider = QSlider(Qt.Horizontal)
        # self.slider.sliderMoved.connect(self.seek_video)
        self.slider.setMinimum(0)
        self.slider.sliderPressed.connect(self.stop_video)
        self.slider.sliderReleased.connect(self.seek_video_mouse_click)  # Update on release
        self.slider.valueChanged.connect(self.seek_video_wheel_scroll)
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



        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        # Layout for the main decision buttons
        decision_layout = QHBoxLayout()
        decision_layout.addWidget(self.healthy_btn)
        decision_layout.addWidget(self.unhealthy_btn)
        decision_layout.addWidget(self.cant_tell_btn)
        
        cant_tell_layout = QHBoxLayout()
        for btn in self.reason_buttons:
            cant_tell_layout.addWidget(btn)
        cant_tell_layout.addWidget(self.proceed_btn)
        cant_tell_layout.setSpacing(5)
        
        self.back_btn = QPushButton("Back")
        self.back_btn.setFixedSize(80, 50)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(lambda: self.load_next_video(next=False))
        
        # bottom controls for video playback
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.video_order_label)
        controls_layout.addWidget(self.back_btn)
        controls_layout.addWidget(self.backward_btn)
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.forward_btn)
        controls_layout.addWidget(self.slider)

        # main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(decision_layout)
        main_layout.addLayout(cant_tell_layout)
        main_layout.addWidget(self.video_label)
        main_layout.addLayout(controls_layout)
        
        # toggle visibility for the first time to avoid them appearing at start
        self.toggle_reasons_availability()

        self.central_widget.setLayout(main_layout)
        self.load_next_video()
        
    def check_cant_tell_enabled(self):
        return self.reason_buttons[0].isEnabled()

    def switch_off_cant_tell(self):
        # switch the button off if enabled
        if self.check_cant_tell_enabled():
            self.toggle_reasons_availability() 
    
    def toggle_reasons_availability(self):
        currently_enabled = self.reason_buttons[0].isEnabled()
        

        width, height = 140, 80
        if currently_enabled:
            # Disable reason buttons: light colored, not clickable, no hover
            for btn in self.reason_buttons + [self.proceed_btn]:
                btn.setEnabled(False)
                btn.setChecked(False)  # uncheck all
                btn.setCursor(Qt.ArrowCursor)
                btn.setFixedSize(width, height)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #545454;        
                        border: 1px solid #545454;
                        border-radius: 5px;
                        padding: 0px;
                        font-size: 20px;
                    }
                    QPushButton:hover {
                        background-color: transparent; 
                        color: #545454;                 
                        border-color: #545454;    
                    }
                """)
        else:
            # Enable reason buttons: normal active style with hover and click
            for btn in self.reason_buttons + [self.proceed_btn]:
                btn.setEnabled(True)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setFixedSize(width, height)
                if btn == self.proceed_btn:
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #8cb3de;  /* green */
                            font-size: 20px;
                            padding: 0px;
                            border-radius: 5px;
                            color: white;
                        }
                        QPushButton:hover {
                            background-color: #6b8db3;  /* dark green */
                            color: white;
                        }
                    """)
                else:
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #cccccc;
                            font-size: 20px;
                            padding: 0px;
                            border-radius: 5px;
                            color: black;
                        }
                        QPushButton:hover {
                            background-color: #adadad;
                            color: white;
                        }
                        QPushButton:checked {
                            background-color: #5b5d69;
                            color: white;
                        }
                        QPushButton:checked:hover {
                            background-color: #7b809e;
                            color: white;
                        }
                    """)


            
    def toggle_reason(self):
        sender = self.sender()
        if sender.isChecked():
            self.selected_reasons.append(sender.text())
        else:
            self.selected_reasons.remove(sender.text())

    def load_next_video(self, next=True):
        if next:
            self.current_video = self.video_queue.get_next_video() # returns a VideoSample object
        else:
            if not self.previous_videos:
                return # stay where we are if no previous videos present
            self.current_video = self.previous_videos.pop()
            self.current_video_order -= 1
            
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

    def update_frame(self, set_slider=True):
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
        # avoid recursion with slider value changing by using a flag
        if set_slider:
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
        
    def seek_video_mouse_click(self):
        frame_idx = self.slider.value()
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        if self.timer.isActive(): # we want to stop the video, so toggle only if video is playing
            self.toggle_playback()
        self.update_frame()
        # self.toggle_playback() 
        
    def seek_video_wheel_scroll(self, frame_position):

        if not hasattr(self, 'cap') or self.cap is None:
            raise RuntimeError("VideoCapture object is not initialized. Load a video first.")
        
        # Set the position in the VideoCapture object
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)
        self.slider.setValue(frame_position)

        ret, frame = self.cap.read()
        if ret:
            self.update_frame(set_slider=False)
        # don't do anything if we are over video limit

    
    def display_frame(self, frame):
        """
        Displays a single frame on the QLabel.
        """
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame_rgb.shape
        bytes_per_line = 3 * width
        qimage = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)

        # Scale while preserving aspect ratio
        scaled_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(scaled_pixmap)



    def jump_backward(self):
        current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, current_frame - self.cap.get(cv2.CAP_PROP_FPS)))
        self.update_frame()

    def jump_forward(self):
        current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame + self.cap.get(cv2.CAP_PROP_FPS))
        self.update_frame()
        
    def write_to_csv(self, prediction):
        time_taken = (pd.Timestamp.now() - self.start_time).total_seconds()
        log_data = {
            "video_name": self.current_video.filename,
            "view_order": self.current_video_order,
            "resolution": self.current_video.resolution,
            "prediction": prediction,
            "time_taken": time_taken,
            "true_label": self.current_video.label,
            "time_stamp": datetime.datetime.now(),
        }
        pd.DataFrame([log_data]).to_csv(self.log_file, mode="a", header=False, index=False)

    def log_prediction(self, prediction):      
        # update predictions and log
        self.video_queue.update_predictions(self.current_video, prediction)
        self.write_to_csv(prediction)
        
        # wrap up
        self.current_video_order += 1
        self.cap.release()
        self.timer.stop()

        # reset cant tell button
        self.switch_off_cant_tell()

        # add current video to stack
        self.previous_videos.append(self.current_video)
        
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
        exit_btn.setStyleSheet("""
            QPushButton {
                border-radius: 25px;
                padding: 10px;
                font-size: 18px;
                background-color: lightgreen;
            }
            QPushButton:hover {
                background-color: darkgreen;
            }
        """)
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
    # parser.add_argument("--resolutions", type=parse_resolutions, default=[(320, 240), (480, 320), (640, 480), (800, 600), (1024, 768), (1280, 720)], help="Specify the resolution for compression, e.g. [(420,300), (800,600)].")
    
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    window = UltrasoundAssessment(args.video_dir)
    window.show()
    sys.exit(app.exec_())
