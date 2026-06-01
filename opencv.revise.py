import cv2
import numpy as np

canvas = np.zeros((480, 640, 3), dtype='uint8')
cv2.rectangle(canvas, (50, 50), (250, 200), (0, 255, 0), 2) 
cv2.circle(canvas, (400, 150), 60, (0, 0, 255), 3)
cv2.line(canvas, (0, 300), (640, 300), (255, 255, 0), 2)
cv2.imshow('Drawing', canvas)
cv2.waitKey(0)
cv2.destroyAllWindows()