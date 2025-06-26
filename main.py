import cv2
import sys
import time
import threading
import face_utils
import inotify.adapters
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QKeyEvent, QMouseEvent
from PyQt5.QtWidgets import QApplication, QWidget


checkInterval = 5
stopEvent = threading.Event()
isUser = False
cap = cv2.VideoCapture(0)
check_once = None


class FullscreenWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowState(Qt.WindowFullScreen)


# def check_face_once():
#     print("Opened! check!")
#     global cap
#     cap.grab()
#     ret, frame = cap.read()
#     if(ret):
#         cv2.imwrite("./test.jpg", frame)
#         if(not face_utils.check_face("./test.jpg")):
#             print("attacker!")
#             #app.open_window()
#         else:
#             print("User!")
#     time.sleep(100)


def check_face_once():
    global isUser
    if(not isUser):
        app.start_lock()
    time.sleep(100)


def listen():
    global check_once
    file_to_watch = '/home/Fox/code/tmp/'
    i = inotify.adapters.Inotify()
    i.add_watch('{}'.format(file_to_watch))

    print("Listening for events in {}".format(file_to_watch))
    for event in i.event_gen(yield_nones=True):
        start_time = time.time()
        if(event):
            (_, event_types, path, filename) = event
            if 'IN_ACCESS' in event_types or 'IN_OPEN' in event_types:
                print("目录访问了: {}, {}".format(path, start_time))
                if(check_once is None or not check_once.is_alive()):
                    check_once = threading.Thread(target=check_face_once)
                    check_once.start()
        else:
            if stopEvent.wait(
                timeout=max(0, .01 - time.time() + start_time)
            ):
                break


def check_face_loop():
    global cap
    global isUser
    global checkInterval
    while(True):
        start_time = time.time()
        
        cap.grab()
        ret, frame = cap.read()
        if(ret):
            cv2.imwrite("./test.jpg", frame)
        isUser = face_utils.check_face("./test.jpg")

        if stopEvent.wait(
            timeout=max(0, checkInterval - time.time() + start_time)
        ):
            break

    print("check quited")


def mask():
    global checkInterval
    checkInterval = 3
    app = QApplication(sys.argv)
    window = FullscreenWindow()
    window.show()
    sys.exit(app.exec_())
    checkInterval = 5


class WorkerThread(QThread):
    # def run(self):
    #     print("启动！")
    #     self.signal_open_window.emit()
    #     self.sleep(5)
    #     print("关闭！")
    #     self.signal_close_window.emit()
    #     self.sleep(5)
    #     print("退出！")
    #     self.signal_exit_program.emit()

    def run(self):
        print("子线程启动！！")
        while(True):
            print(isUser)
            time.sleep(1)


class Main:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        self.worker_thread = None
        self.listener = threading.Thread(target=listen)
        self.checker = threading.Thread(target=check_face_loop)
    
    
    def start_lock(self):
        self.open_window()
        global checkInterval
        checkInterval = 2
        if(self.worker_thread is None or not self.worker_thread.isRunning()):
            self.worker_thread = WorkerThread()
            self.worker_thread.start()

    
    def open_window(self):
        if not self.window or not self.window.isVisible():
            self.window = FullscreenWindow()
            self.window.show()

    def close_window(self):
        if self.window:
            self.window.hide()
            self.window.deleteLater()
            self.window = None

    def exit_program(self):
        global stopEvent
        stopEvent.set()
        self.checker.join()
        self.listener.join()
        if self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
        self.app.quit()
        global cap
        cap.release()

    def run(self):
        self.checker.start()
        self.listener.start()
        print("开始监听！")
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    app = Main()
    app.run()
