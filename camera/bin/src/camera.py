# encoding: utf-8

import os
import shutil
import cv2
import time
import json
import lebai_sdk
import utils.camera as camera

current_dir = os.path.dirname(os.path.abspath(__file__))

lebai_sdk.init()
lebai = lebai_sdk.connect("127.0.0.1", True)

def get_cmd():
    cmd = (lebai.get_item("plugin_camera_cmd_reinit"))['value']
    if cmd and cmd != "":
        return "reinit"
    cmd = (lebai.get_item("plugin_camera_cmd_shoot"))['value']
    if cmd and cmd != "":
        return "shoot"

    return ""

def get_flip():
    val = (lebai.get_item("plugin_camera_flip"))['value']
    if not val:
        val = "-2"
    return int(val)

def search_camera():
    width = (lebai.get_item("plugin_camera_width"))['value']
    if not width:
        width = "1280"
    width = int(width)
    height = (lebai.get_item("plugin_camera_height"))['value']
    if not height:
        height = "720"
    height = int(height)
    fps = (lebai.get_item("plugin_camera_fps"))['value']
    if not fps:
        fps = "10"
    fps = int(fps)

    camera_list = []
    for i in range(-1, 20):
        cap = camera.Camera(i, width, height, fps)
        if cap.isOpened() and (cap.getImage()[0] is not None):
            camera_list.append(i)
        cap.release()
    lebai.set_item("plugin_camera_indexs", json.dumps(camera_list))
    return camera_list

def init_camera():
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
    fps = (lebai.get_item("plugin_camera_fps"))['value']
    if not fps:
        fps = "10"
    fps = int(fps)

    cap = camera.Camera(index, width, height, fps)
    return cap

def main():
    cap = init_camera()
    if not cap.isOpened():
        cameras = search_camera()
        if len(cameras) == 1:
            lebai.set_item("plugin_camera_index", str(cameras[0]))
        exit(1)

    images_dir = os.path.join(current_dir, "../../images")
    if not os.path.exists(images_dir):
        os.mkdir(images_dir)
    while True:
        time.sleep(0.1)
        cmd = get_cmd()
        if not cmd or cmd == "":
            continue
        if cmd == "shoot":
            frame, depth = cap.getImage()
            if frame is None:
                break
            frame = cv2.GaussianBlur(frame, (5, 5), 0)
            flip = get_flip()
            if flip in [0, 1, -1]:
                frame = cv2.flip(frame, flip)
                frame = cv2.flip(depth, flip)
            cv2.imwrite(os.path.join(images_dir, "img.tmp.jpg"), frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            shutil.move(os.path.join(images_dir, "img.tmp.jpg"), os.path.join(images_dir, "img.jpg"))
            if depth:
                cv2.imwrite(os.path.join(images_dir, "depth.tmp.png"), depth)
                shutil.move(os.path.join(images_dir, "depth.tmp.png"), os.path.join(images_dir, "depth.png"))
            # cv2.imwrite(os.path.join(images_dir, "img.tmp.webp"), frame, [cv2.IMWRITE_WEBP_QUALITY, 50])
            # shutil.move(os.path.join(images_dir, "img.tmp.webp"), os.path.join(images_dir, "img.webp"))
        if cmd == "reinit":
            cap.release()
            cameras = search_camera()
            cap = init_camera()
        lebai.set_item("plugin_camera_cmd_{}".format(cmd), "")
    exit(2)
    # 释放摄像头
    cap.release()

if __name__ == '__main__':
    main()
