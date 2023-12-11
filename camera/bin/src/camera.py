# encoding: utf-8

### AprilTag检测位姿

import cv2
import time
import lebai_sdk
import utils.camera as camera

lebai_sdk.init()
lebai = lebai_sdk.connect("127.0.0.1", True)

def get_interval():
    interval = (lebai.get_item("plugin_camera_interval"))['value']
    if not interval:
        interval = "0"
    interval = float(interval)
    return interval

def main():
    index = (lebai.get_item("plugin_camera_index"))['value']
    if not index:
        index = "-1"
    index = int(index)
    width = (lebai.get_item("plugin_camera_width"))['value']
    if not width:
        width = "1280"
    width = int(width)
    height = (lebai.get_item("plugin_camera_height"))['value']
    if not height:
        height = "720"
    height = int(height)
    fx = (lebai.get_item("plugin_camera_fx"))['value']
    if not fx:
        fx = "900"
    fx = float(fx)
    fy = (lebai.get_item("plugin_camera_fy"))['value']
    if not fy:
        fy = "900"
    fy = float(fy)
    cx = (lebai.get_item("plugin_camera_cx"))['value']
    if not cx:
        cx = "640"
    cx = float(cx)
    cy = (lebai.get_item("plugin_camera_cy"))['value']
    if not cy:
        cy = "360"
    cy = float(cy)

    cap = camera.Camera(index, width, height)
    if not cap.isOpened():
        exit(1)

    while True:
        interval = get_interval()
        if interval > 0:
            time.sleep(interval)
            frame = cap.getImage()
            if frame is None:
                break
            cv2.iwrite("../../images/tmp.jpg", frame)
        else:
            time.sleep(5.0)
    exit(2)
    # 释放摄像头
    cap.release()

main()
