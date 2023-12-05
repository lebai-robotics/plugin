# encoding: utf-8

import pyrealsense2 as rs
import numpy as np
import cv2

width = 1280
height = 720

default_index = 0

class Camera(object):
    kind = None  # 类型
    camera = None  # 摄像头实例
 
    def __init__(self, index = default_index, capW = width, capH = height):
        if index < 0:
            self.kind = "rs"
            try:
                pipeline = rs.pipeline()
                config = rs.config()
                config.enable_stream(rs.stream.color, capW, capH, rs.format.bgr8, 15)
                pipe_profile = pipeline.start(config)
                self.camera = pipeline
            except:
                pass
        else:
            self.kind = "cv"
            try:
                cap = cv2.VideoCapture(index)
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, capW)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, capH)
                    self.camera = cap
            except:
                pass
 
    def isOpened(self):
        return self.camera is not None

    def getImage(self):
        img_color = None
        if self.kind == "cv":
            try:
                ret, frame = self.camera.read()
                if ret:
                    img_color = frame
            except:
                pass
        if self.kind == "rs":
            try:
                frames = self.camera.wait_for_frames()
                color_frame = frames.get_color_frame()
                img_color = np.asanyarray(color_frame.get_data())
            except:
                pass
        return img_color

    def release(self):
        if self.kind == "cv":
            self.camera.release()
        if self.kind == "rs":
            self.camera.stop()
