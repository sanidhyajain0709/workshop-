import cv2

cap = cv2.VideoCapture('traffic.mp4')

if not cap.isOpened():
    print("video file nahi mila!")
    exit()
print("video ready hai!")
print(f"total frames: {int(cap.get(cv2.CAP_PROP_FRAME_COUNT))}")
print(f"original FPS: {cap.get(cv2.CAP_PROP_FPS)}")
