import sys
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

def detect_largest_circle(frame):
    im_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_bound = np.array([4, 120, 120], dtype=np.uint8)
    upper_bound = np.array([11, 255, 255], dtype=np.uint8)
    im_hsv_masked = cv2.inRange(im_hsv, lower_bound, upper_bound)
    
    element = np.ones((5, 5), dtype=np.uint8)
    im_hsv_masked = cv2.erode(im_hsv_masked, element)
    im_hsv_masked = cv2.dilate(im_hsv_masked, element)

    points = np.argwhere(im_hsv_masked > 0).astype(np.float32)
    if len(points) == 0:
        return None

    circle = cv2.minEnclosingCircle(points)
    center, radius = circle

    # 在此加上對半徑的範圍判斷
    if 10 <= radius <= 15:
        circle_info = (int(center[0]), int(center[1]), int(radius))
        return circle_info
    else:
        return None



def resize_and_equalize_resolution(image1, image2):
    # 調整兩張圖片的大小和解析度
    width = min(image1.shape[1], image2.shape[1])
    height = min(image1.shape[0], image2.shape[0])
    
    image1_resized = cv2.resize(image1, (width, height))
    image2_resized = cv2.resize(image2, (width, height))
    
    return image1_resized, image2_resized

def calculate_similarity(image1, image2):
    # 設置窗口大小，這裡使用3x3的窗口大小
    win_size = 3
    
    # 計算SSIM
    ssim_value = ssim(image1, image2, multichannel=True, win_size=win_size)
    
    # 將SSIM值轉換到0到100範圍
    similarity_percentage = ssim_value * 100
    
    return similarity_percentage

def calculate_similarity_bypath(image1path, image2path):
    # 讀取兩張圖像
    image1 = cv2.imread(image1path)
    image2 = cv2.imread(image2path)

    # 調整圖像大小和解析度
    image1_resized, image2_resized = resize_and_equalize_resolution(image1, image2)

    # 計算相似度
    similarity_percentage = calculate_similarity(image1_resized, image2_resized)

    return similarity_percentage

'''
test.py

# 導入 calculate_similarity_bypath 函式
from opencv3 import calculate_similarity_bypath

# 計算相似度
similarity_percentage = calculate_similarity_bypath('test5.png', 'test7.png')

print(f"相似度: {similarity_percentage:.2f}%")
'''
