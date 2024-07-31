# encoding: utf-8
import apriltag
import json
import time
import lebai_sdk

lebai = lebai_sdk.connect("127.0.0.1", True)

def main():
    apriltag_signal = (lebai.get_item("plugin_apriltag_signal"))['value']
    if not apriltag_signal:
        apriltag_signal = "13"
    apriltag_signal = int(apriltag_signal)

    while True:
        time.sleep(0.1)
        apriltag_id = lebai.get_signal(apriltag_signal)
        if apriltag_id >= 0:
            lebai.save_pose("apriltag"+str(apriltag_id), None)
            apriltag_data = apriltag.main()
            apriltag_pose = apriltag_data.get(str(apriltag_id), None)
            lebai.save_pose("apriltag"+str(apriltag_id), apriltag_pose)

            lebai.set_signal(apriltag_signal, -1)

if __name__ == '__main__':
    main()
