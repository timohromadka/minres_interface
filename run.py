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


class UltrasoundAssessment(QMainWindow):
    def __init__(self, video_dir):
        super().__init__()
        self.video_dir = video_dir
        self.log_file = "assessment_log.csv"
        self.resolutions = [(320, 240), (480, 320), (640, 480), (800, 600), (1024, 768), (1280, 720)]
        self.current_video = None
        self.current_resolution_idx = 0
        self.video_order = []
        self.video_transform = {}
        self.correct_predictions = {}
        self.start_time = None

        self.init_video_data()
        self.init_ui()

    def init_video_data(self):
        self.videos = []
        for category in ['healthy', 'unhealthy']:
            folder_path = os.path.join(self.video_dir, category)
            for file in os.listdir(folder_path):
                if file.endswith('.mp4'):
                    video_path = os.path.join(folder_path, file)
                    resolution = cv2.VideoCapture(video_path).get(cv2.CAP_PROP_FRAME_HEIGHT)
                    self.videos.append((video_path, resolution, category))
        self.videos.sort(key=lambda x: x[1])

        self.video_order = random.sample(self.videos, len(self.videos))
        self.video_transform = {
            video[0]: random.choice(['none', 'h_flip', 'v_flip', 'hv_flip']) for video in self.video_order
        }
        self.correct_predictions = {video[0]: 0 for video in self.video_order}

        if not os.path.exists(self.log_file):
            pd.DataFrame(columns=[
                "video_name", "resolution", "prediction", "time_taken", "category"
            ]).to_csv(self.log_file, index=False)

    def init_ui(self):
        self.setWindowTitle("Ultrasound Assessment")
        self.showMaximized()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)

        self.healthy_btn = QPushButton("Healthy")
        self.unhealthy_btn = QPushButton("Unhealthy")
        self.cant_tell_btn = QPushButton("Can't Tell")

        for btn in [self.healthy_btn, self.unhealthy_btn, self.cant_tell_btn]:
            btn.setStyleSheet(
                "border-radius: 25px; padding: 10px; font-size: 18px; background-color: lightblue;"
            )
            btn.setFixedSize(150, 50)

        self.healthy_btn.clicked.connect(lambda: self.log_prediction("Healthy"))
        self.unhealthy_btn.clicked.connect(lambda: self.log_prediction("Unhealthy"))
        self.cant_tell_btn.clicked.connect(lambda: self.log_prediction("Can't Tell"))
        

        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.toggle_playback)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.sliderMoved.connect(self.seek_video)
        self.slider.setMinimum(0)

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
        if not self.video_order:
            self.show_end_screen()
            return

        self.current_video, resolution, category = self.video_order.pop(0)
        self.current_resolution_idx = 0
        self.start_time = pd.Timestamp.now()

        self.cap = cv2.VideoCapture(self.current_video)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolutions[self.current_resolution_idx][0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolutions[self.current_resolution_idx][1])

        self.slider.setMaximum(int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return

        transform = self.video_transform[self.current_video]
        if transform == "h_flip":
            frame = cv2.flip(frame, 1)
        elif transform == "v_flip":
            frame = cv2.flip(frame, 0)
        elif transform == "hv_flip":
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

    def seek_video(self, frame_idx):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        self.update_frame()

    def jump_backward(self):
        current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, current_frame - self.cap.get(cv2.CAP_PROP_FPS)))
        self.update_frame()

    def jump_forward(self):
        current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame + self.cap.get(cv2.CAP_PROP_FPS))
        self.update_frame()

    def log_prediction(self, prediction):
        time_taken = (pd.Timestamp.now() - self.start_time).total_seconds()
        resolution = f"{self.resolutions[self.current_resolution_idx][0]}x{self.resolutions[self.current_resolution_idx][1]}"
        video_name = os.path.basename(self.current_video)

        log_data = {
            "video_name": video_name,
            "resolution": resolution,
            "prediction": prediction,
            "time_taken": time_taken,
            "true_label": self.get_category(self.current_video),
            "time_stamp": datetime.datetime.now()
        }
        pd.DataFrame([log_data]).to_csv(self.log_file, mode="a", header=False, index=False)

        if prediction.lower() == self.get_category(self.current_video):
            self.correct_predictions[self.current_video] += 1
            if self.correct_predictions[self.current_video] >= 3:
                return self.load_next_video()

        self.current_resolution_idx += 1
        if self.current_resolution_idx >= len(self.resolutions):
            self.load_next_video()

    def get_category(self, video_path):
        return "healthy" if "healthy" in video_path else "unhealthy"

    def show_end_screen(self):
        self.timer.stop()
        self.central_widget.deleteLater()
        end_widget = QWidget()
        layout = QVBoxLayout()
        label = QLabel("Thank You")
        label.setStyleSheet("color: white; font-size: 48px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        exit_btn = QPushButton("Exit")
        exit_btn.setStyleSheet("font-size: 24px;")
        exit_btn.clicked.connect(self.close)
        layout.addWidget(exit_btn)
        layout.setAlignment(Qt.AlignCenter)

        end_widget.setLayout(layout)
        end_widget.setStyleSheet("background-color: black;")
        self.setCentralWidget(end_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    video_dir = "ultrasounds"  # Update with your path
    window = UltrasoundAssessment(video_dir)
    window.show()
    sys.exit(app.exec_())
