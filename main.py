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
cap = cv2.VideoCapture(0)


class FullscreenWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowState(Qt.WindowFullScreen)


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


def check_face():
    global cap
    global checkInterval
    while(True):
        start_time = time.time()
        
        cap.grab()
        ret, frame = cap.read()
        if(ret):
            cv2.imwrite("./test.jpg", frame)
        face_utils.check_face("./test.jpg")

        if stopEvent.wait(
            timeout=max(0, checkInterval - time.time() + start_time)
        ):
            break

    cap.release()
    print("quit")


def mask():
    global checkInterval
    checkInterval = 3
    app = QApplication(sys.argv)
    window = FullscreenWindow()
    window.show()
    sys.exit(app.exec_())
    checkInterval = 5


class WorkerThread(QThread):
    signal_open_window = pyqtSignal()
    signal_close_window = pyqtSignal()
    signal_exit_program = pyqtSignal()

    def run(self):
        print("启动！")
        self.signal_open_window.emit()
        self.sleep(5)
        print("关闭！")
        self.signal_close_window.emit()
        self.sleep(5)
        print("退出！")
        self.signal_exit_program.emit()


class Main:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        self.worker_thread = WorkerThread()
        self.worker_thread.signal_open_window.connect(self.open_window)
        self.worker_thread.signal_close_window.connect(self.close_window)
        self.worker_thread.signal_exit_program.connect(self.exit_program)
    
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
        if self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
        self.app.quit()

    def run(self):
        time.sleep(5)
        print("就决定是你了，子线程！")
        self.worker_thread.start()
        sys.exit(self.app.exec_())


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
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    app = Main()
    app.run()
