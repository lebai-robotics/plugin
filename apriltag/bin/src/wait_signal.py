# encoding: utf-8
import subprocess
import json
import time
import lebai_sdk

apriltag_plugin = '/data/user/file/.plugin/apriltag/bin/src/apriltag.py'

lebai_sdk.init()
lebai = lebai_sdk.connect("127.0.0.1", True)

def main():
    apriltag_signal = (lebai.get_item("plugin_apriltag_signal"))['value']
    if not apriltag_signal:
        apriltag_signal = "13"
    apriltag_signal = int(apriltag_signal)

    while True:
        time.sleep(1)
        apriltag_id = lebai.get_signal(apriltag_signal)
        if apriltag_id >= 0:
            apriltag_data = subprocess.check_output(['lpy', apriltag_plugin])
            apriltag_data = json.loads(apriltag_data)
            apriltag_pose = apriltag_data.get(str(apriltag_id), None)
            print(apriltag_id, apriltag_data)
            lebai.save_pose("apriltag", apriltag_pose)

            lebai.set_signal(apriltag_signal, -1)

if __name__ == '__main__':
    main()
