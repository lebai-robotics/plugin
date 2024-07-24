# encoding: utf-8

### 视觉标定

import os
import shutil
import numpy as np
from contextlib import suppress
import cv2
import json
import time
import math
import lebai_sdk
import utils.rotation as rotation

lebai_sdk.init()
lebai = lebai_sdk.connect("127.0.0.1", True)

def get_tag():
    tag = (lebai.get_item("plugin_camera_calibrater_tag"))['value']
    if not tag:
        tag = "0"
    return tag
def get_size():
    size = (lebai.get_item("plugin_camera_calibrater_size"))['value']
    if not size:
        size = "120"
    size = int(size)
    return size
def get_i():
    i = (lebai.get_item("plugin_camera_calibrater_i"))['value']
    if not i:
        i = "0"
    i = int(i)
    return i
def get_cmd():
    cmd = (lebai.get_item("plugin_camera_calibrater_cmd_clear"))['value']
    if cmd and cmd != "":
        return "clear"
    cmd = (lebai.get_item("plugin_camera_calibrater_cmd_calibrate"))['value']
    if cmd and cmd != "":
        return "calibrate"
    cmd = (lebai.get_item("plugin_camera_calibrater_cmd_record"))['value']
    if cmd and cmd != "":
        return "record"
    cmd = (lebai.get_item("plugin_camera_calibrater_cmd_preview"))['value']
    if cmd and cmd != "":
        return "preview"

    return ""
def get_pose(i):
    robot_pose = (lebai.get_item("plugin_camera_calibrater_pose_{}".format(i)))['value']
    if not robot_pose:
        return None
    tag_pose = (lebai.get_item("plugin_camera_calibrater_pose_tag_{}".format(i)))['value']
    if not tag_pose:
        return None
    return {"robot": json.loads(robot_pose), "tag": json.loads(tag_pose)}

def find_tags():
    lebai.write_single_register("openmv", 300, 1)
    while lebai.read_holding_registers("openmv", 300, 1)[1]!=0:
        time.sleep(0.1)
    num = lebai.read_holding_registers("openmv", 301, 1)[1]
    tags = {}
    for i in range(num):
        tag_data = lebai.read_holding_registers(311+10*i, 7)
        x = tag_data[2]
        if x > 32767:
            x = x - 65536
        y = tag_data[3]
        if y > 32767:
            y = y - 65536
        z = tag_data[4]
        if z > 32767:
            z = z - 65536
        tags[str(tag_data[1])] = {"x":x,"y":y,"z":z,"rz":tag_data[5]/65536*2*math.pi,"ry":tag_data[6]/65536*2*math.pi,"rx":tag_data[7]/65536*2*math.pi}
    return tags

def main():
    while True:
        time.sleep(0.1)
        cmd = get_cmd()
        if not cmd or cmd == "":
            continue
        if cmd == "record":
            tag_id = get_tag()
            tags = find_tags()
            if not tags.has_key(tag_id):
                continue

            i = get_i()+1
            lebai.set_item("plugin_camera_calibrater_i", str(i))
            lebai.set_item("plugin_camera_calibrater_pose_tag_{}".format(i), json.dumps(tags[tag_id]))
            pose = (lebai.get_kin_data())["actual_flange_pose"]
            lebai.set_item("plugin_camera_calibrater_pose_{}".format(i), json.dumps(pose))

        if cmd == "clear":
            # 清除数据
            lebai.set_item("plugin_camera_calibrater_i", str(0))
        if cmd == "calibrate":
            R_end2base = [] # 法兰相对于基座的姿态
            T_end2base = [] # 法兰相对于基座的位置
            R_chess2cam = [] # 标签相对于摄像头的姿态
            T_chess2cam = [] # 标签相对于摄像头的位置
            # 手眼标定
            for i in range(1, get_i()+1):
                pose = get_pose(i)
                p = pose["robot"]
                R_end2base.append(rotation.eulerZyzToRotationMatrix([p["rz"], p["ry"], p["rx"]]))
                T_end2base.append(np.array([p["x"], p["y"], p["z"]]))
                p = pose["tag"]
                R_chess2cam.append(rotation.eulerZyzToRotationMatrix([p["rz"], p["ry"], p["rx"]]))
                T_chess2cam.append(np.array([p["x"], p["y"], p["z"]]))
            R, T = cv2.calibrateHandEye(R_end2base, T_end2base, R_chess2cam, T_chess2cam, cv2.CALIB_HAND_EYE_TSAI)
            r = rotation.rotationMatrixToEulerZyx(R)
            data = {"x":T[0][0],"y":T[1][0],"z":T[2][0],"rz":r[0],"ry":r[1],"rx":r[2]}
            lebai.set_item("plugin_camera_calibrater_data", json.dumps(data))

            lebai.set_item("plugin_camera_calibrater_i", str(0))
        lebai.set_item("plugin_camera_calibrater_cmd_{}".format(cmd), "")

if __name__ == '__main__':
    main()
