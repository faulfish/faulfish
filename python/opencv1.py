import cv2
import numpy as np

# opencv 4.8.0
print(cv2.__version__)

# 讀取影片
cap = cv2.VideoCapture("test.mp4")

# 建立物件偵測模型
model = cv2.CascadeClassifier("haarcascade_fullbody.xml")

# 偵測物件
while True:
    ret, frame = cap.read()
    if not ret:
        break

    faces = model.detectMultiScale(frame, 1.1, 4)

    # 框選出物件
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # 顯示影像
    cv2.imshow("Video", frame)
    cv2.waitKey(1)

cv2.destroyAllWindows()
