import cv2
import sys
import time
import threading
import face_utils
import inotify.adapters
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QEvent
from PyQt5.QtGui import QKeyEvent, QMouseEvent
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout


checkInterval = 5
stopEvent = threading.Event()
isUser = False
cap = cv2.VideoCapture(0)
check_once = None
lockOn = False


class FullscreenWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowFullScreen)
        self.setWindowTitle("Security Lock")

        self.title_label = QLabel("\\\\\\W.T.F Security Lock Enabled\\\\\\")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: red; font-size: 64px; " 
                                       "font-weight: bold;")
        
        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(self.title_label)

        self.setLayout(layout)

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

        print("Listening for events in {}".format(file_to_watch))
        for event in i.event_gen(yield_nones=True):
            start_time = time.time()
            if(event):
                (_, event_types, path, filename) = event
                if 'IN_ACCESS' in event_types or 'IN_OPEN' in event_types:
                    print("目录访问了: {}, {}".format(path, start_time))
                    self.check_face_once()
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


class WorkerThread(QThread):
    signal_stop = pyqtSignal()
    signal_re = pyqtSignal()

    def run(self):
        print("子线程启动！！")
        while(True):
            if(lockOn):
                self.signal_re.emit()
                print(isUser)
                if(isUser):
                    print("emit!")
                    self.signal_stop.emit()
                    print("emit done!")
            time.sleep(.05)


class Main:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        self.worker_thread = WorkerThread()
        self.listener = ListenThread()
        self.checker = threading.Thread(target=check_face_loop)
    
    def start_lock(self):
        global lockOn
        lockOn = True
        self.open_window()
        global checkInterval
        checkInterval = 2

    def quit_lock(self):
        print("quit lock!")
        global lockOn
        global checkInterval
        lockOn = False
        checkInterval = 5
        self.close_window()

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
            print("hiding")
            self.window.hide()
            self.window.deleteLater()
            self.window = None
            print("succeed")

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
        self.checker.start()
        self.listener.start()
        self.worker_thread.start()
        self.listener.signal_start.connect(self.start_lock)
        self.worker_thread.signal_stop.connect(self.quit_lock)
        self.worker_thread.signal_re.connect(self.reopen_window)
        print("开始监听！")
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    app = Main()
    app.run()
