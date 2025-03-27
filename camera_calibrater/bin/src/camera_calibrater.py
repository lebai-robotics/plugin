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
import dt_apriltags as apriltag

apriltag.Detector.__del__ = lambda x: None # 解决段错误问题

current_dir = os.path.dirname(os.path.abspath(__file__))
images_dir = os.path.join(current_dir, "../../../camera/images")

lebai_sdk.init()
lebai = lebai_sdk.connect("127.0.0.1", True)

def get_ip():
    val = (lebai.get_item("plugin_camera_calibrater_ip"))['value']
    if not val:
        val = "127.0.0.1"
    return val
def get_calibrate():
    val = (lebai.get_item("plugin_camera_calibrater_calibrate"))['value']
    if not val:
        val = "camera"
    return val
def get_tool():
    tp = (lebai.get_item("plugin_camera_calibrater_tool"))['value']
    if not tp:
        tp = "grid"
    return tp
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
def get_tag_family():
    family = (lebai.get_item("plugin_camera_calibrater_tag_family"))['value']
    if not family:
        family = "tag36h11"
    return family
def get_tag_size():
    size = (lebai.get_item("plugin_camera_calibrater_tag_size"))['value']
    if not size:
        size = "0.04"
    size = float(size)
    return size
def get_tag_id():
    id = (lebai.get_item("plugin_camera_calibrater_tag_id"))['value']
    if not id:
        id = "0"
    id = int(id)
    return id
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
    if cmd and cmd == "hand":
        return "calibrate_hand"
    if cmd and cmd != "":
        return "calibrate_camera"
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
        time.sleep(0.1)
        cmd = get_cmd()
        if not cmd or cmd == "":
            continue
        row, col, width = get_row_col_width()
        if cmd == "preview":
            shoot_img()
            img = cv2.imread(os.path.join(images_dir, "img.jpg"))
            if img.size == 0:
                lebai.set_item("plugin_camera_calibrater_cmd_preview", "")
                continue
            tool = get_tool()
            if tool == 'grid':
                ret, corners = cv2.findChessboardCorners(img, (row, col), None)
                if ret:
                    if len(corners) == row * col:
                        cv2.drawChessboardCorners(img, (row,col), corners, ret)
            if tool == 'apriltag':
                tag_family = get_tag_family()
                at_detector = apriltag.Detector(families=tag_family)
                gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                tags = at_detector.detect(gray_img)
                for tag in tags:
                    for corner in tag.corners:
                        cv2.line(img, tuple(corner.astype(int)), tuple(tag.center.astype(int)), 0, 3)
                        cv2.line(img, tuple(corner.astype(int)), tuple(tag.center.astype(int)), 255, 1)
                    cv2.circle(img, tuple(tag.center.astype(int)), 3, 255, 2)
            cv2.imwrite(os.path.join(images_dir, "camera_calibrater.tmp.webp"), img, [cv2.IMWRITE_WEBP_QUALITY, 10])
            shutil.move(os.path.join(images_dir, "camera_calibrater.tmp.webp"), os.path.join(images_dir, "camera_calibrater.webp"))
        if cmd == "record":
            shoot_img()
            img = cv2.imread(os.path.join(images_dir, "img.jpg"))
            if img.size == 0:
                lebai.set_item("plugin_camera_calibrater_cmd_record", "")
                continue
            tool = get_tool()
            if tool == 'grid':
                ret, corners = cv2.findChessboardCorners(img, (row, col), None)
                if not ret or len(corners) != row * col:
                    lebai.set_item("plugin_camera_calibrater_cmd_record", "")
                    continue
            if tool == 'apriltag':
                tag_family = get_tag_family()
                tag_id = get_tag_id()
                at_detector = apriltag.Detector(families=tag_family)
                gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                tags = at_detector.detect(gray_img)
                finded = False
                for tag in tags:
                    if int(tag.tag_id) == tag_id:
                        finded = True
                        break
                if not finded:
                    lebai.set_item("plugin_camera_calibrater_cmd_record", "")
                    continue
            i = get_i() + 1
            if get_calibrate() == 'hand':
                lebai_real = lebai_sdk.connect(get_ip(), False)
                pose = (lebai_real.get_kin_data())["actual_flange_pose"]
                lebai.set_item("plugin_camera_calibrater_pose_{}".format(i), json.dumps(pose))
            lebai.set_item("plugin_camera_calibrater_i", str(i))
            shutil.copy(os.path.join(images_dir, "img.jpg"), os.path.join(images_dir, "camera_calibrater.{}.webp".format(i)))
        if cmd == "clear":
            # 清除数据
            clear_imgs()
            lebai.set_item("plugin_camera_calibrater_i", str(0))
        if cmd == "calibrate_camera":
            if get_i() < 9:
                print("image not enough")
                lebai.set_item("plugin_camera_calibrater_cmd_calibrate", "")
                continue
            # 标定
            R_chess2cam = [] # 棋盘相对于摄像头的姿态
            T_chess2cam = [] # 棋盘相对于摄像头的位置

            cp_int = np.zeros((row * col, 3), np.float32)
            cp_int[:, :2] = np.mgrid[0:row, 0:col].T.reshape(-1, 2)
            cp_world = cp_int * width
            obj_points = []  # 存储物理坐标
            image_points = []  # 存储角点像素坐标
            for i in range(1, get_i()+1):
                img = cv2.imread(os.path.join(images_dir, "camera_calibrater.{}.webp".format(i)), cv2.IMREAD_GRAYSCALE)
                if img.size == 0:
                    continue
                ret, corners = cv2.findChessboardCorners(img, (row, col), None)
                if not ret or len(corners) != row * col:
                    continue
                # cv2.find4QuadCornerSubpix(img, corners, (row, col))
                obj_points.append(cp_world)
                image_points.append(corners)
            # 进行相机标定
            ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(obj_points, image_points, img.shape[::-1], None, None)
            if not ret:
                print("failed to calibrateCamera")
                lebai.set_item("plugin_camera_calibrater_cmd_calibrate", "")
                continue
            # 计算投影误差
            mean_error = 0
            error_points = []  # 坐标误差
            for i in range(len(obj_points)):
                imgpoints2, _ = cv2.projectPoints(obj_points[i], rvecs[i], tvecs[i], camera_matrix, dist_coeffs)
                error = cv2.norm(image_points[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
                error_points.append(error)
                mean_error += error
            mean_error = mean_error / len(obj_points)

            bad_points = []  #异常坐标
            for i in range(len(obj_points)):
                if error_points[i] > max(mean_error, 0.1) * 1.5:
                    print("remove bad images:", error_points[i])
                    bad_points.append(i)
            for i in bad_points[::-1]:
                end2base.pop(i)
                obj_points.pop(i)
                image_points.pop(i)

            ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(obj_points, image_points, img.shape[::-1], None, None)
            if not ret:
                print("failed to calibrateCamera")
                lebai.set_item("plugin_camera_calibrater_cmd_calibrate", "")
                continue
            lebai.set_item("plugin_camera_calibrater_camera_matrix", json.dumps(camera_matrix.tolist())) # 相机内参
            lebai.set_item("plugin_camera_calibrater_dist_coeffs", json.dumps(dist_coeffs.tolist())) # 相机畸变
            clear_imgs()
            lebai.set_item("plugin_camera_calibrater_i", str(0))
        if cmd == "calibrate_hand":
            if get_i() < 9:
                print("image not enough")
                lebai.set_item("plugin_camera_calibrater_cmd_calibrate", "")
                continue
            dist_coeffs = (lebai.get_item("plugin_camera_calibrater_dist_coeffs"))['value']
            dist_coeffs = json.loads(dist_coeffs)
            camera_matrix = (lebai.get_item("plugin_camera_calibrater_camera_matrix"))['value']
            camera_matrix = json.loads(camera_matrix)
            # 标定
            end2base = [] # 法兰相对于基座的位姿
            R_chess2cam = [] # 棋盘相对于摄像头的姿态
            T_chess2cam = [] # 棋盘相对于摄像头的位置
            tool = get_tool()
            if tool == 'grid':
                cp_int = np.zeros((row * col, 3), np.float32)
                cp_int[:, :2] = np.mgrid[0:row, 0:col].T.reshape(-1, 2)
                cp_world = cp_int * width
                obj_points = []  # 存储物理坐标
                image_points = []  # 存储角点像素坐标
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
                    end2base.append(p)
                    obj_points.append(cp_world)
                    image_points.append(corners)
                # 手眼标定
                for i in range(0,len(image_points)):
                    ret, rvec, tvec = cv2.solvePnP(cp_world, image_points[i], camera_matrix, distCoeffs=dist_coeffs)
                    RT = np.column_stack(((cv2.Rodrigues(rvec))[0], tvec))
                    R_chess2cam.append(RT[:3, :3])
                    T_chess2cam.append(RT[:3, 3].reshape((3, 1)))
            if tool == 'apriltag':
                dist_coeffs = (lebai.get_item("plugin_camera_calibrater_dist_coeffs"))['value']
                dist_coeffs = json.loads(dist_coeffs)
                camera_matrix = (lebai.get_item("plugin_camera_calibrater_camera_matrix"))['value']
                camera_matrix = json.loads(camera_matrix)
                fx = camera_matrix[0][0]
                fy = camera_matrix[1][1]
                cx = camera_matrix[0][2]
                cy = camera_matrix[1][2]
                tag_family = get_tag_family()
                tag_id = get_tag_id()
                tag_size = get_tag_size()
                at_detector = apriltag.Detector(families=tag_family)
                for i in range(1, get_i()+1):
                    p = get_pose(i)
                    if not p:
                        continue
                    img = cv2.imread(os.path.join(images_dir, "camera_calibrater.{}.webp".format(i)), cv2.IMREAD_GRAYSCALE)
                    img = cv2.undistort(img, np.array(camera_matrix), np.array(dist_coeffs))
                    if img.size == 0:
                        continue
                    tags = at_detector.detect(img, estimate_tag_pose=True, camera_params=(fx, fy, cx, cy), tag_size=tag_size)
                    for tag in tags:
                        if int(tag.tag_id) == tag_id:
                            pos = tag.pose_t
                            rot = rotation.rotationMatrixToEulerZyx(tag.pose_R)
                            offset = {"x":pos[0][0],"y":pos[1][0],"z":pos[2][0], "rx":rot[2],"ry":rot[1],"rz":rot[0]}
                            if (offset["x"]**2+offset["y"]**2+offset["z"]**2)**0.5 > 0.8:
                                continue
                            end2base.append(p)
                            R_chess2cam.append(tag.pose_R)
                            T_chess2cam.append(tag.pose_t)
                            break
            tp = get_type()
            if tp == "inHand":
                # end2base * cam2end * chess2cam = chess2base
                R_end2base = []
                T_end2base = []
                for i in range(len(end2base)):
                    p = end2base[i]
                    R_end2base.append(rotation.eulerZyzToRotationMatrix([p["rz"], p["ry"], p["rx"]]))
                    T_end2base.append(np.array([p["x"], p["y"], p["z"]]))
                R, T = cv2.calibrateHandEye(R_end2base, T_end2base, R_chess2cam, T_chess2cam, cv2.CALIB_HAND_EYE_TSAI)
                r = rotation.rotationMatrixToEulerZyx(R)
                data = {"x":T[0][0],"y":T[1][0],"z":T[2][0],"rz":r[0],"ry":r[1],"rx":r[2]}
                lebai.set_item("plugin_camera_calibrater_data", json.dumps(data))
            if tp == "toHand":
                # end2base⁻¹ * cam2base * chess2cam = chess2end
                R_end2base = []
                T_end2base = []
                for i in range(len(end2base)):
                    p = end2base[i]
                    p = lebai.pose_inverse(p)
                    R_end2base.append(rotation.eulerZyzToRotationMatrix([p["rz"], p["ry"], p["rx"]]))
                    T_end2base.append(np.array([p["x"], p["y"], p["z"]]))
                R, T = cv2.calibrateHandEye(R_end2base, T_end2base, R_chess2cam, T_chess2cam, cv2.CALIB_HAND_EYE_TSAI)
                r = rotation.rotationMatrixToEulerZyx(R)
                data = {"x":T[0][0],"y":T[1][0],"z":T[2][0],"rz":r[0],"ry":r[1],"rx":r[2]}
                lebai.set_item("plugin_camera_calibrater_data", json.dumps(data))

            clear_imgs()
            lebai.set_item("plugin_camera_calibrater_i", str(0))
        lebai.set_item("plugin_camera_calibrater_cmd_{}".format(cmd), "")

if __name__ == '__main__':
    main()
