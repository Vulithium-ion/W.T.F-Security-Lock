import os
import cv2
import sys
import time
import threading
import face_utils
import inotify.adapters
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QEvent
from PyQt5.QtGui import QKeyEvent, QMouseEvent, QPixmap, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout


checkInterval = 5
stopEvent = threading.Event()
isUser = False
cap = cv2.VideoCapture(0)
check_once = None
lockOn = False
countDown = 0
defaultCountDown = 31
picPerSec = 30


class FullscreenWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowFullScreen)
        self.setWindowTitle("Security Lock")

        self.title_label = QLabel("\\\\\\W.T.F Security Lock Enabled\\\\\\")
        self.title_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.title_label.setStyleSheet("color: red; font-size: 64px; " 
                                       "font-weight: bold;")
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.pixmap = QPixmap("test.jpg") 

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.status_label.setFont(QFont("Arial", 18))
        
        layout = QVBoxLayout()
        layout.addStretch(1)
        layout.addWidget(self.title_label)
        layout.addStretch(2)
        layout.addWidget(self.image_label)
        layout.addStretch(2)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        self.refresh()

    def refresh(self):
        pixmap = QPixmap("test.jpg") #可能有竞态条件？
        self.image_label.setPixmap(pixmap.scaledToWidth(600, 
                                   Qt.SmoothTransformation))
        global countDown
        if(countDown > 0):
            self.status_label.setText(
                "⚠️Shutting Down in {} Seconds⚠️".format(countDown)
            )
        else:
            self.status_label.setText("🔻Shutting down now...🔻")

    def isActive(self):
        return super().isActiveWindow()


class ListenThread(QThread):
    signal_start = pyqtSignal()

    def check_face_once(self):
        global lockOn
        global isUser
        if(not isUser and not lockOn):
            self.signal_start.emit()

    def run(self):
        global check_once
        file_to_watch = '/home/Fox/code/tmp/'
        i = inotify.adapters.Inotify()
        i.add_watch('{}'.format(file_to_watch))

        # print("Listening for events in {}".format(file_to_watch))
        for event in i.event_gen(yield_nones=True):
            start_time = time.time()
            if(event):
                (_, event_types, path, filename) = event
                if 'IN_ACCESS' in event_types:
                    # print("Accessed: {}, {}".format(path, start_time))
                    self.check_face_once()
            else:
                if stopEvent.wait(
                    timeout=max(0, .01 - time.time() + start_time)
                ):
                    break


def count_down():
    global countDown
    global lockOn
    while(lockOn):
        #print("countdown-- ({}) {}".format(countDown, threading.get_ident()))
        countDown -= 1
        time.sleep(1)
        if(countDown == -1):
            # os.system("shutdown")
            print("shutdown -h 0")
            pass


def read_cam():
    global cap
    while(True):
        start_time = time.time()
        cap.grab()
        ret, frame = cap.read()
        if(ret):
            cv2.imwrite("./test.jpg", frame)
        time.sleep(max(0, 1/picPerSec - time.time() + start_time))


def check_face_loop():
    global isUser
    global checkInterval
    while(True):
        start_time = time.time()
        
        isUser = face_utils.check_face("./test.jpg")

        if stopEvent.wait(
            timeout=max(0, checkInterval - time.time() + start_time)
        ):
            break


class WorkerThread(QThread):
    signal_stop = pyqtSignal()
    signal_tick = pyqtSignal()

    def run(self):
        while(True):
            if(lockOn):
                self.signal_tick.emit()
                if(isUser):
                    self.signal_stop.emit()
            time.sleep(.033333)


class Main:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        self.worker_thread = WorkerThread()
        self.listener = ListenThread()
        self.checker = threading.Thread(target=check_face_loop)
        self.counter = None
        self.photographor = threading.Thread(target=read_cam)
    
    def start_lock(self):
        global lockOn
        if(not lockOn):
            lockOn = True
            global checkInterval
            checkInterval = 2
            global countDown
            countDown = defaultCountDown
            # ！！这里有逻辑错误：可能执行这里时counter线程没结束，之后改（会改吗）？
            self.counter = threading.Thread(target=count_down)
            self.counter.start()
            self.open_window()

    def quit_lock(self):
        global lockOn
        global checkInterval
        lockOn = False
        checkInterval = 5
        self.close_window()

    def tick(self):
        self.reopen_window()
        self.window.refresh()

    def reopen_window(self):
        if(not self.window.isActive()):
            self.close_window()
            self.open_window()
    
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
        if self.listener.isRunning():
            self.listener.quit()
            self.listener.wait()
        if self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
        global cap
        cap.release()
        self.app.quit()

    def run(self):
        self.window = FullscreenWindow()
        self.photographor.start()
        self.checker.start()
        self.listener.start()
        self.worker_thread.start()
        self.listener.signal_start.connect(self.start_lock)
        self.worker_thread.signal_stop.connect(self.quit_lock)
        self.worker_thread.signal_tick.connect(self.tick)
        sys.__stdout__.write("W.T.F Security Lock Booted!\n")
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    app = Main()
    app.run()
