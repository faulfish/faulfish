import cv2
import numpy as np
import sys
from opencv3 import calculate_similarity, detect_largest_circle

# opencv 4.8.0
print(cv2.__version__)

# 读取影片
cap = cv2.VideoCapture("test.mp4")
image1 = cv2.imread('test5.png')

# 幀計數器
frame_count = 0

# 记录圆形位置和帧数的列表
circle_info = []

pause = False  # 初始化暂停状态

# 颜色范围定义
color_lower = np.array([45*0.99, 61*0.99, 224*0.99])
color_upper = np.array([45*1.01, 61*1.01, 224*1.01])

# 偵測物件
while True:
    if not pause:
        ret, frame = cap.read()
        if not ret:
            break

    # 将影像转换成灰度图像
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    '''
    circle = detect_largest_circle(frame)
    if circle is not None:
        x, y, radius = circle
        cv2.circle(frame, (x, y), radius, (0, 255, 255), 4)
        cv2.putText(frame, f"radius: {radius}",(x,y),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.imshow('im_hsv',frame)
        # 检查是否按下 键
        key = cv2.waitKey(0)
    '''

    # 使用霍夫圆检测来查找圆形
    circles = cv2.HoughCircles(
        gray, cv2.HOUGH_GRADIENT, dp=1, minDist=1000, param1=20, param2=30, minRadius=4, maxRadius=20
    )

    if circles is not None:
        circles = np.uint16(np.around(circles))
        for circle in circles[0, :]:
            x, y, radius = circle

            # 提取圆形区域内的像素
            circle_region = frame[y - radius:y + radius, x - radius:x + radius]
                
            # 计算相似度
            resized_circle = cv2.resize(circle_region, (image1.shape[1], image1.shape[0]))
            similarity_percentage = calculate_similarity(image1, resized_circle)
            print(f"相似度: {similarity_percentage:.2f}%")
                
            # 如果相似度大于50%，输出相似度信息
            if similarity_percentage > 60:
                cv2.rectangle(frame, (x - radius, y - radius), (x + radius, y + radius), (0, 0, 255), 2)
                cv2.circle(frame, (x, y), radius, (0, 255, 0), 4)
                # 记录圆形位置和帧数
                circle_info.append((frame_count, (x, y)))

            '''
            # 检查圆形区域内的像素颜色是否在范围内
            num_colors_inside_range = np.sum((color_lower <= circle_region) & (circle_region <= color_upper))
            if num_colors_inside_range >= 15:
                # 如果符合条件，绘制边界框
                cv2.rectangle(frame, (x - radius, y - radius), (x + radius, y + radius), (0, 0, 255), 2)
                cv2.circle(frame, (x, y), radius, (0, 255, 0), 4)
                # 记录圆形位置和帧数
                circle_info.append((frame_count, (x, y)))
            '''


    # 限制 circle_info 列表长度为最后 10 条
    circle_info = circle_info[-10:]

    # 检查是否按下 空白 键
    key = cv2.waitKey(1) & 0xFF
    if key == 32:
        pause = not pause  # 切换暂停状态
    elif key == 27:  # 检查是否按下 ESC 键
        break
        
    # 在影像右侧显示圆形位置和帧数信息
    for idx, (frame_num, circle_pos) in enumerate(circle_info):
        text = f"frame: {frame_num}, Pos: {circle_pos}"
        y_position = 20 + idx * 20  # 调整每行信息的纵向位置
        cv2.putText(frame, text, (frame.shape[1] - 300, y_position),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # 在影像中添加幀數文字
    frame_count += 1
    cv2.putText(frame, f"frame: {frame_count}", (10, frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # 显示影像
    cv2.imshow("Video", frame)

    # 检查是否按下 P 键
    key = cv2.waitKey(1) & 0xFF
    if key == 32:
        pause = not pause  # 切换暂停状态
    elif key == 27:  # 检查是否按下 ESC 键
        break

cv2.destroyAllWindows()

