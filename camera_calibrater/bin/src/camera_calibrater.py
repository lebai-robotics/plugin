# encoding: utf-8

### 视觉标定

import os
import shutil
import numpy as np
from contextlib import suppress
import cv2
import json
import time
import lebai_sdk
import utils.rotation as rotation

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
def get_row_col_width():
    row = (lebai.get_item("plugin_camera_calibrater_row"))['value']
    if not row:
        row = "8"
    row = int(row)
    col = (lebai.get_item("plugin_camera_calibrater_col"))['value']
    if not col:
        col = "5"
    col = int(col)
    width = (lebai.get_item("plugin_camera_calibrater_width"))['value']
    if not width:
        width = "0.03"
    width = float(width)
    return row, col, width
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
    pose = (lebai.get_item("plugin_camera_calibrater_pose_{}".format(i)))['value']
    if not pose:
        return None
    return json.loads(pose)

def clear_imgs():
    for i in range(1, 10):
        with suppress(FileNotFoundError):
            os.remove(os.path.join(images_dir, "camera_calibrater.{}.webp".format(i)))

def shoot_img():
    lebai.set_item("plugin_camera_cmd_shoot", "shoot")
    while True:
        time.sleep(0.1)
        cmd = (lebai.get_item("plugin_camera_cmd_shoot"))['value']
        if not cmd or cmd == "":
            break

def main():
    while True:
        time.sleep(1)
        cmd = get_cmd()
        if not cmd or cmd == "":
            continue
        if cmd == "preview":
            shoot_img()
            img = cv2.imread(os.path.join(images_dir, "img.webp"))
            if img.size == 0:
                lebai.set_item("plugin_camera_calibrater_cmd_preview", "")
                continue
            row, col, width = get_row_col_width()
            ret, corners = cv2.findChessboardCorners(img, (row, col), None)
            if ret:
                if len(corners) == row * col:
                    cv2.drawChessboardCorners(img, (row,col), corners, ret)
            cv2.imwrite(os.path.join(images_dir, "camera_calibrater.tmp.webp"), img, [cv2.IMWRITE_WEBP_QUALITY, 10])
            shutil.move(os.path.join(images_dir, "camera_calibrater.tmp.webp"), os.path.join(images_dir, "camera_calibrater.webp"))
        if cmd == "record":
            shoot_img()
            lebai_real = lebai_sdk.connect(get_ip(), False)
            i = get_i()+1
            lebai.set_item("plugin_camera_calibrater_i", str(i))
            shutil.copy(os.path.join(images_dir, "img.webp"), os.path.join(images_dir, "camera_calibrater.{}.webp".format(i)))
            pose = (lebai_real.get_kin_data())["actual_flange_pose"]
            lebai.set_item("plugin_camera_calibrater_pose_{}".format(i), json.dumps(pose))
        if cmd == "clear":
            # 清除数据
            clear_imgs()
            lebai.set_item("plugin_camera_calibrater_i", str(0))
        if cmd == "calibrate":
            # 标定
            cp_int = np.zeros((row * col, 3), np.float32)
            cp_int[:, :2] = np.mgrid[0:row, 0:col].T.reshape(-1, 2)
            cp_world = cp_int * width
            obj_points = []  # 存储物理坐标
            image_points = []  # 存储角点像素坐标
            R_end2base = [] # 法兰相对于基座的姿态
            T_end2base = [] # 法兰相对于基座的位置
            R_chess2cam = [] # 棋盘相对于摄像头的姿态
            T_chess2cam = [] # 棋盘相对于摄像头的位置
            for i in range(1, get_i()+1):
                img = cv2.imread(os.path.join(images_dir, "camera_calibrater.{}.webp".format(i)), cv2.IMREAD_GRAYSCALE)
                if img.size == 0:
                    continue
                ret, corners = cv2.findChessboardCorners(img, (row, col), None)
                if not ret or len(corners) != row * col:
                    continue
                # cv2.find4QuadCornerSubpix(img, corners, (row, col))
                p = get_pose(i)
                if not p:
                    continue
                R_end2base.append(rotation.eulerZyzToRotationMatrix([p["rz"], p["ry"], p["rx"]]))
                T_end2base.append(np.array([p["x"], p["y"], p["z"]]))
                obj_points.append(cp_world)
                image_points.append(corners)
            # 进行相机标定
            image_points_len = len(image_points)
            if image_points_len < 3:
                print("image not enough")
                lebai.set_item("plugin_camera_calibrater_cmd_calibrate", "")
                continue
            ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(obj_points, image_points, img.shape[::-1], None, None)
            if not ret:
                print("failed to calibrateCamera")
                lebai.set_item("plugin_camera_calibrater_cmd_calibrate", "")
                continue
            lebai.set_item("plugin_camera_calibrater_camera_matrix", json.dumps(camera_matrix.tolist())) # 相机内参
            lebai.set_item("plugin_camera_calibrater_dist_coeffs", json.dumps(dist_coeffs.tolist())) # 相机畸变
            # 手眼标定
            for i in range(0,len(image_points)):
                ret, rvec, tvec = cv2.solvePnP(cp_world, image_points[i], camera_matrix, distCoeffs=dist_coeffs)
                RT = np.column_stack(((cv2.Rodrigues(rvec))[0], tvec))
                R_chess2cam.append(RT[:3, :3])
                T_chess2cam.append(RT[:3, 3].reshape((3, 1)))
            tp = get_type()
            if tp == "inHand":
                R, T = cv2.calibrateHandEye(R_end2base, T_end2base, R_chess2cam, T_chess2cam, cv2.CALIB_HAND_EYE_TSAI)
                r = rotation.rotationMatrixToEulerZyx(R)
                data = {"x":T[0][0],"y":T[1][0],"z":T[2][0],"rz":r[0],"ry":r[1],"rx":r[2]}
                lebai.set_item("plugin_camera_calibrater_data", json.dumps(data))

            clear_imgs()
            lebai.set_item("plugin_camera_calibrater_i", str(0))
        lebai.set_item("plugin_camera_calibrater_cmd_{}".format(cmd), "")

if __name__ == '__main__':
    main()
