# encoding: utf-8

### AprilTag检测位姿

import os
import cv2
import time
import lebai_sdk
import utils.rotation as rotation
import dt_apriltags as apriltag

current_dir = os.path.dirname(os.path.abspath(__file__))
images_dir = os.path.join(current_dir, "../../../camera/images")

lebai_sdk.init()
lebai = await lebai_sdk.connect("127.0.0.1", True)

def main():
    fx = (await lebai.get_item("plugin_camera_fx"))['value']
    if not fx:
        fx = "900"
    fx = float(fx)
    fy = (await lebai.get_item("plugin_camera_fy"))['value']
    if not fy:
        fy = "900"
    fy = float(fy)
    cx = (await lebai.get_item("plugin_camera_cx"))['value']
    if not cx:
        cx = "640"
    cx = float(cx)
    cy = (await lebai.get_item("plugin_camera_cy"))['value']
    if not cy:
        cy = "360"
    cy = float(cy)
    tag_family = (await lebai.get_item("plugin_apriltag_tag_family"))['value']
    if not tag_family:
        tag_family = "tag36h11"
    tag_size = (await lebai.get_item("plugin_apriltag_tag_size"))['value']
    if not tag_size:
        tag_size = "0.04"
    tag_size = float(tag_size)

    at_detector = apriltag.Detector(families=tag_family)
    gray = cv2.imread(os.path.join(images_dir, "tmp.jpg"), cv2.IMREAD_GRAYSCALE)
    if not gray:
        exit(2)
    tags = at_detector.detect(gray, estimate_tag_pose=True, camera_params=(fx, fy, cx, cy), tag_size=tag_size)

    ret = {}
    for tag in tags:
        pos = tag.pose_t
        rot = rotation.rotationMatrixToEulerZyx(tag.pose_R)
        offset = {"x":pos[0][0],"y":pos[1][0],"z":pos[2][0], "rx":rot[2],"ry":rot[1],"rz":rot[0]}
        ret[tag.tag_id] = offset

    print(ret)

main()
