import cv2
import time
from ultralytics import YOLO


VIDEO_PATH = 'traffic.mp4'
WINDOW_SIZE = (1080,1920)
VEHICLE_CLASSES = ['car', 'truck', 'bus', 'motorcycle']
CONFIDENCE = 0.4


model = YOLO('yolov8n.pt')

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("video file nhi mila traffic.mp4 same folder m rkho.")
    exit()


    prev_time = 0
    paused = False 
    screenshot_count = 0
    fps = 0
    frame = 0

    print(" video chl rhi h...")
    print(" SPACE = paused/resume")
    print("s = screenshot")
    print("q = quit")


    while True:
        if not paused:
            ret,frame= cap.read()
            if not ret:
                print("video")
                break

            frame = cv2.resize(frame, WINDOEW_SIZE)
            