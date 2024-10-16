# encoding: utf-8

import lebai_sdk
import time

lebai_sdk.init()
lebai = lebai_sdk.connect("127.0.0.1", False)


def main():
    last = lebai.get_di("ROBOT", 0)
    while True:
        time.sleep(0.1)
        new = lebai.get_di("ROBOT", 0)
        if last == 0 and new == 1:
            lebai.resume_task()
        if last == 1 and new == 0:
            lebai.pause_task()
        last = new


if __name__ == "__main__":
    main()
