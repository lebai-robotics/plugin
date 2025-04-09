# encoding: utf-8

import os
import shutil
from contextlib import suppress
import cv2
import numpy as np
import json
import time
import lebai_sdk
import utils.rotation as rotation
from ultralytics import YOLO

current_dir = os.path.dirname(os.path.abspath(__file__))
images_dir = os.path.join(current_dir, "../../../camera/images")

lebai_sdk.init()
lebai = lebai_sdk.connect("127.0.0.1", True)

def get_ip():
    val = (lebai.get_item("plugin_camera_calibrater_ip"))['value']
    if not val:
        val = "127.0.0.1"
    return val
def get_type():
    tp = (lebai.get_item("plugin_camera_calibrater_type"))['value']
    if not tp:
        tp = "inHand"
    return tp
def shoot_img():
    lebai.set_item("plugin_camera_cmd_shoot", "shoot")
    while True:
        time.sleep(0.1)
        cmd = (lebai.get_item("plugin_camera_cmd_shoot"))['value']
        if not cmd or cmd == "":
            break
def find_tags():
    shoot_img()
    dist_coeffs = (lebai.get_item("plugin_camera_calibrater_dist_coeffs"))['value']
    dist_coeffs = json.loads(dist_coeffs)
    camera_matrix = (lebai.get_item("plugin_camera_calibrater_camera_matrix"))['value']
    camera_matrix = json.loads(camera_matrix)
    fx = camera_matrix[0][0]
    fy = camera_matrix[1][1]
    cx = camera_matrix[0][2]
    cy = camera_matrix[1][2]
    model = (lebai.get_item("plugin_yolo_model"))['value']
    if not model:
        model = "yolo11n.pt"

    model = YOLO(model)
    img = cv2.imread(os.path.join(images_dir, "img.jpg"), cv2.IMREAD_GRAYSCALE)
    img = cv2.undistort(img, np.array(camera_matrix), np.array(dist_coeffs))
    #_, img = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)
    depth = cv2.imread(os.path.join(images_dir, "depth.png"))
    depth = cv2.undistort(depth, np.array(camera_matrix), np.array(dist_coeffs))
    if img.size == 0 or depth.size == 0:
        exit(2)
    results = model(img)

    ret = []
    for box in results[0].boxes:
        confidence = float(box.conf[0])
        if confidence < 0.6:
            continue
        class_id = int(box.cls[0])
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        depth = depth_img[center_y, center_x] / 10000.0  # 假设深度单位为 0.1毫米，转换为米

        # 像素坐标转换为相机坐标系
        x = (center_x - cx) * depth / fx
        y = (center_y - cy) * depth / fy
        z = depth

        ret.push({"x": x, "y": y, "z": z, "class_id": class_id, "confidence": confidence})
    results[0].save(os.path.join(images_dir, "yolo.tmp.jpg"))
    with suppress(FileNotFoundError):
        shutil.move(os.path.join(images_dir, "yolo.5.jpg"), os.path.join(images_dir, "yolo.6.jpg"))
    with suppress(FileNotFoundError):
        shutil.move(os.path.join(images_dir, "yolo.4.jpg"), os.path.join(images_dir, "yolo.5.jpg"))
    with suppress(FileNotFoundError):
        shutil.move(os.path.join(images_dir, "yolo.3.jpg"), os.path.join(images_dir, "yolo.4.jpg"))
    with suppress(FileNotFoundError):
        shutil.move(os.path.join(images_dir, "yolo.2.jpg"), os.path.join(images_dir, "yolo.3.jpg"))
    with suppress(FileNotFoundError):
        shutil.move(os.path.join(images_dir, "yolo.1.jpg"), os.path.join(images_dir, "yolo.2.jpg"))
    with suppress(FileNotFoundError):
        shutil.move(os.path.join(images_dir, "yolo.jpg"), os.path.join(images_dir, "yolo.1.jpg"))
    with suppress(FileNotFoundError):
        shutil.move(os.path.join(images_dir, "yolo.tmp.jpg"), os.path.join(images_dir, "yolo.jpg"))
    return ret

def find_tags_pose(flange_pose):
    tp = get_type()
    if tp == "toHand":
        flange_pose = {"x": 0, "y": 0, "z": 0, "rx": 0, "ry": 0, "rz": 0}
    tags = find_tags()
    ret = {}
    cam2flange = json.loads((lebai.get_item("plugin_camera_calibrater_data"))['value'])
    cam = lebai.pose_trans(flange_pose, cam2flange)
    for tag_id, tag in tags.items():
        offset = tag
        tag_pos_offset = {"x":offset["x"], "y":offset["y"], "z":offset["z"], "rz":0, "ry":0, "rx":0}
        tag_pose = lebai.pose_trans(cam, tag_pos_offset)
        ret[str(tag_id)] = tag_pose
    return ret

def main():
    lebai_real = lebai_sdk.connect(get_ip(), False)
    flange_pose = (lebai_real.get_kin_data())["actual_flange_pose"]
    ret = find_tags_pose(flange_pose)
    return ret

if __name__ == '__main__':
    ret = main()
    print(json.dumps(ret))
