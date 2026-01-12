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
model_file = None
model = None

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
    global model_file
    global model
    shoot_img()

    model_new = (lebai.get_item("plugin_yolo_model"))['value']
    if not model_new:
        model_new = "yolo11n.pt"

    if model_new != model_file or not model:
        print("model:", model_new)
        model_file = model_new
        model = YOLO(model_new, task="detect")
    img = cv2.imread(os.path.join(images_dir, "img.jpg"))
    if img.size == 0:
        exit(2)

    is_depth = True
    depth_img = cv2.imread(os.path.join(images_dir, "depth.png"), cv2.IMREAD_ANYDEPTH)
    if depth_img is None or depth_img.size == 0:
        is_depth = False
    dist_coeffs = (lebai.get_item("plugin_camera_calibrater_dist_coeffs"))['value']
    camera_matrix = (lebai.get_item("plugin_camera_calibrater_camera_matrix"))['value']
    if (not dist_coeffs) or (not camera_matrix):
        is_depth = False
    else:
        dist_coeffs = json.loads(dist_coeffs)
        camera_matrix = json.loads(camera_matrix)

    results = model.predict(source=img)
    ret = []
    for box in results[0].boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        if confidence < 0.6:
            continue
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)
        if not is_depth:
            ret.append({"class_id": class_id, "confidence": confidence, "center_x": center_x, "center_y":center_y})
            continue
        depth = depth_img[center_y, center_x] / 10000.0  # 假设深度单位为 0.1毫米，转换为米

        # 像素坐标转换为相机坐标系
        fx = camera_matrix[0][0]
        fy = camera_matrix[1][1]
        cx = camera_matrix[0][2]
        cy = camera_matrix[1][2]
        x = (center_x - cx) * depth / fx
        y = (center_y - cy) * depth / fy
        z = depth

        ret.append({"x": x, "y": y, "z": z, "class_id": class_id, "confidence": confidence, "center_x": center_x, "center_y":center_y})
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
    return ret, is_depth

def find_tags_pose(flange_pose):
    tp = get_type()
    if tp == "toHand":
        flange_pose = {"x": 0, "y": 0, "z": 0, "rx": 0, "ry": 0, "rz": 0}
    tags, is_depth = find_tags()
    if not is_depth:
        return tags
    ret = []
    cam2flange = (lebai.get_item("plugin_camera_calibrater_data"))['value']
    if not cam2flange:
        return tags
    else:
        cam2flange = json.loads(cam2flange)
    cam = lebai.pose_trans(flange_pose, cam2flange)
    for tag in tags:
        tag_pos_offset = {"x":tag["x"], "y":tag["y"], "z":tag["z"], "rz":0, "ry":0, "rx":0}
        tag_pose = lebai.pose_trans(cam, tag_pos_offset)
        tag_pose["class_id"] = tag["class_id"]
        tag_pose["confidence"] = tag["confidence"]
        tag_pose["center_x"] = tag["center_x"]
        tag_pose["center_y"] = tag["center_y"]
        ret.append(tag_pose)
    return ret

def main():
    lebai_real = lebai_sdk.connect(get_ip(), False)
    flange_pose = (lebai_real.get_kin_data())["actual_flange_pose"]
    ret = find_tags_pose(flange_pose)
    return ret

if __name__ == '__main__':
    ret = main()
    print(json.dumps(ret))
