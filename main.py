import os
import cv2
import time
import threading
import face_utils
import inotify.adapters
from PIL import Image


CHECK_INTERVAL = 5
stopEvent = threading.Event()


def listen():
    file_to_watch = '/home/Fox/code/WTF_Security_Lock/'
    i = inotify.adapters.Inotify()
    i.add_watch('{}'.format(file_to_watch))

    print("Listening for events in {}".format(file_to_watch))
    for event in i.event_gen(yield_nones=False):
        (_, event_types, path, filename) = event
        if 'IN_ACCESS' in event_types:
            print(f"🔔 目录访问了: {path}")
        elif 'IN_OPEN' in event_types:
            print(f"📂 目录被打开: {path}")


def take_pic():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 30)
    while(True):
        start_time = time.time()
        cap.grab()


def check_face():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    while(True):
        start_time = time.time()
        
        cap.grab()
        ret, frame = cap.read()
        if(ret):
            cv2.imwrite("./test.jpg", frame)
        face_utils.check_face("./test.jpg")

        if stopEvent.wait(
            timeout=max(0, CHECK_INTERVAL - time.time() + start_time)
        ):
            break

    cap.release()
    print("quit")


def main():
    listener = threading.Thread(target=listen)
    checker = threading.Thread(target=check_face)

    checker.start()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("主线程捕获到 KeyboardInterrupt，发送停止信号...")
        stopEvent.set()

    checker.join()


if __name__ == '__main__':
    main()
