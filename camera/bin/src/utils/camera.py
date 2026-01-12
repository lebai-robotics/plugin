# encoding: utf-8

import pyrealsense2 as rs
import numpy as np
import concurrent.futures
import cv2

default_width = 640
default_height = 480
default_fps = 5
default_index = 0

class Camera(object):
    kind = None  # 类型
    camera = None  # 摄像头实例
    idle = 0.008 # 120fps
 
    def __init__(self, index = default_index, capW = default_width, capH = default_height, fps = default_fps):
        if index == -1:
            self.kind = "rs"
            try:
                capW = 640
                capH = 480
                fps = 5
                pipeline = rs.pipeline()
                config = rs.config()
                config.enable_stream(rs.stream.depth, capW, capH, rs.format.z16, fps)
                config.enable_stream(rs.stream.color, capW, capH, rs.format.bgr8, fps)
                pipe_profile = pipeline.start(config)
                self.camera = pipeline
            except:
                pass
        else:
            self.kind = "cv"
            try:
                cap = cv2.VideoCapture(index)
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    cap.set(cv2.CAP_PROP_FPS, fps)
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, capW)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, capH)
                    self.camera = cap
            except:
                pass
        self.idle = min(0.008, 1/fps)
 
    def isOpened(self):
        return self.camera is not None

    def clearCache(self):
        if self.kind == "cv":
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                while True:
                    try:
                        future = ex.submit(self.camera.grab)
                        if not future.result(timeout=0.5*self.idle):
                            break
                    except concurrent.futures.TimeoutError:
                        break

    def getInfo(self):
        if self.kind == "rs":
            try:
                pipe_profile = self.camera.get_active_profile()
                color_profile = pipe_profile.get_stream(rs.stream.color)
                color_intrinsics = color_profile.as_video_stream_profile().get_intrinsics()
                camera_matrix = np.array([
                    [color_intrinsics.fx, 0, color_intrinsics.ppx],
                    [0, color_intrinsics.fy, color_intrinsics.ppy],
                    [0, 0, 1]
                ])
                dist_coeffs = np.array([color_intrinsics.coeffs])
                return camera_matrix, dist_coeffs
            except:
                pass

    def getImage(self):
        img_color = None
        img_depth = None
        if self.kind == "cv":
            try:
                self.clearCache()
                ret, frame = self.camera.retrieve()
                if ret:
                    img_color = frame
            except:
                pass
        if self.kind == "rs":
            try:
                rs.align(rs.stream.color)
                frames = self.camera.wait_for_frames()
                rs.align(rs.stream.color).process(frames)
                depth_frame = frames.get_depth_frame()
                color_frame = frames.get_color_frame()
                img_color = np.asanyarray(color_frame.get_data())
                img_depth = np.asanyarray(depth_frame.get_data())
            except:
                pass
        return img_color, img_depth

    def release(self):
        if not self.isOpened():
            return
        if self.kind == "cv":
            self.camera.release()
        if self.kind == "rs":
            self.camera.stop()
