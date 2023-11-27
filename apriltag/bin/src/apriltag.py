# encoding: utf-8

### AprilTag检测位姿

import cv2
import time
import lebai_sdk
import asyncio
import utils.rotation as rotation
import utils.camera as camera
import dt_apriltags as apriltag

lebai_sdk.init()

async def main():
    lebai = await lebai_sdk.connect("127.0.0.1", True)
    camera_index = (await lebai.get_item("plugin_apriltag_camera_index"))['value']
    if not camera_index:
	    camera_index = "0"
    camera_index = int(camera_index)
    fx = (await lebai.get_item("plugin_apriltag_fx"))['value']
    if not fx:
	    fx = "320"
    fx = float(fx)
    fy = (await lebai.get_item("plugin_apriltag_fy"))['value']
    if not fy:
	    fy = "320"
    fy = float(fy)
    cx = (await lebai.get_item("plugin_apriltag_cx"))['value']
    if not cx:
	    cx = "320"
    cx = float(cx)
    cy = (await lebai.get_item("plugin_apriltag_cy"))['value']
    if not cy:
	    cy = "240"
    cy = float(cy)
    tag_family = (await lebai.get_item("plugin_apriltag_tag_family"))['value']
    if not tag_family:
	    tag_family = "tag36h11"
    tag_size = (await lebai.get_item("plugin_apriltag_tag_size"))['value']
    if not tag_size:
	    tag_size = "0.04"
    tag_size = float(tag_size)

    at_detector = apriltag.Detector(families=tag_family)
    cap = camera.open(camera_index)
    if not cap:
        exit(-1)

    # 开始用摄像头读数据，返回hx为true则表示读成功，frame为读的图像
    hx, frame = cap.read()
    hx, frame = cap.read()
    hx, frame = cap.read()
    # 如果hx为Flase表示开启摄像头失败，那么就输出"read vido error"并退出程序
    if hx is False:
        exit(-1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    tags = at_detector.detect(gray, estimate_tag_pose=True, camera_params=(
        fx, fy, cx, cy), tag_size=tag_size)
    
    ret = {}
    for tag in tags:
        pos = tag.pose_t
        rot = rotation.rotationMatrixToEulerZyx(tag.pose_R)
        offset = {"x":pos[0][0],"y":pos[1][0],"z":pos[2][0], "rx":rot[2],"ry":rot[1],"rz":rot[0]}
        ret[tag.tag_id] = offset

    print(ret)
    # 释放摄像头
    cap.release()

asyncio.run(main())
