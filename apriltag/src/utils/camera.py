# encoding: utf-8

import cv2

width = 640
height = 480

default_index = 0

def open(index = default_index):
    cap = cv2.VideoCapture(index)  # 打开相机
    # 检查相机是否成功打开
    if not cap.isOpened():
        return None

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return cap
