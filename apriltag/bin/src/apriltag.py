# encoding: utf-8

### AprilTag检测位姿

import os
import shutil
from contextlib import suppress
import cv2
import numpy as np
import json
import time
import lebai_sdk
import utils.rotation as rotation
import dt_apriltags as apriltag

current_dir = os.path.dirname(os.path.abspath(__file__))
images_dir = os.path.join(current_dir, "../../../camera/images")

lebai_sdk.init()
lebai = lebai_sdk.connect("127.0.0.1", True)
at_detector_family = None
at_detector = None

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
    tag_family = (lebai.get_item("plugin_apriltag_tag_family"))['value']
    if not tag_family:
        tag_family = "tag36h11"
    tag_size = (lebai.get_item("plugin_apriltag_tag_size"))['value']
    if not tag_size:
        tag_size = "0.04"
    tag_size = float(tag_size)

    if tag_family != at_detector_family or not at_detector:
        at_detector_family = tag_family
        at_detector = apriltag.Detector(families=tag_family)
    img = cv2.imread(os.path.join(images_dir, "img.jpg"), cv2.IMREAD_GRAYSCALE)
    img = cv2.undistort(img, np.array(camera_matrix), np.array(dist_coeffs))
    #_, img = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)
    if img.size == 0:
        exit(2)
    tags = at_detector.detect(img, estimate_tag_pose=True, camera_params=(fx, fy, cx, cy), tag_size=tag_size)

    ret = {}
    for tag in tags:
        pos = tag.pose_t
        rot = rotation.rotationMatrixToEulerZyx(tag.pose_R)
        offset = {"x":pos[0][0],"y":pos[1][0],"z":pos[2][0], "rx":rot[2],"ry":rot[1],"rz":rot[0]}
        if (offset["x"]**2+offset["y"]**2+offset["z"]**2)**0.5 > 0.8:
            continue
        ret[str(tag.tag_id)] = offset
        for corner in tag.corners:
            cv2.line(img, tuple(corner.astype(int)), tuple(tag.center.astype(int)), 0, 3)
            cv2.line(img, tuple(corner.astype(int)), tuple(tag.center.astype(int)), 255, 1)
        cv2.circle(img, tuple(tag.center.astype(int)), 3, 255, 2)
    cv2.imwrite(os.path.join(images_dir, "apriltag.tmp.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 50])
    with suppress(FileNotFoundError):
        shutil.move(os.path.join(images_dir, "apriltag.5.jpg"), os.path.join(images_dir, "apriltag.6.jpg"))
    with suppress(FileNotFoundError):
        shutil.move(os.path.join(images_dir, "apriltag.4.jpg"), os.path.join(images_dir, "apriltag.5.jpg"))
    with suppress(FileNotFoundError):
        shutil.move(os.path.join(images_dir, "apriltag.3.jpg"), os.path.join(images_dir, "apriltag.4.jpg"))
    with suppress(FileNotFoundError):
        shutil.move(os.path.join(images_dir, "apriltag.2.jpg"), os.path.join(images_dir, "apriltag.3.jpg"))
    with suppress(FileNotFoundError):
        shutil.move(os.path.join(images_dir, "apriltag.1.jpg"), os.path.join(images_dir, "apriltag.2.jpg"))
    with suppress(FileNotFoundError):
        shutil.move(os.path.join(images_dir, "apriltag.jpg"), os.path.join(images_dir, "apriltag.1.jpg"))
    with suppress(FileNotFoundError):
        shutil.move(os.path.join(images_dir, "apriltag.tmp.jpg"), os.path.join(images_dir, "apriltag.jpg"))
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
        tag_rot_offset = {"x":0,"y": 0,"z": 0, "rz":offset["rz"], "ry":offset["ry"], "rx":offset["rx"]}
        tag_pose = lebai.pose_trans(cam, tag_pos_offset)
        tag_pose = lebai.pose_trans(tag_pose, tag_rot_offset)
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
