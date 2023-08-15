import json
import socket
import sys

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QEvent, QObject, QPoint
from queue import Queue
from threading import Thread

class HIDClient(Thread):
    def __init__(self, PORT=12321):
        super().__init__()
        self.HOST = "127.0.0.1"
        self.PORT = PORT
        self.daemon = True
        self.stopped = False
    
    def run(self):
        global SendQueue
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.HOST, self.PORT))
            while True:
                if not SendQueue.empty():
                    s.sendall(SendQueue.get(block=True))


class HoverTracker(QObject):
    positionChanged = pyqtSignal(QPoint)

    def __init__(self, widget):
        super().__init__(widget)
        self._widget = widget
        self.widget.setMouseTracking(True)
        self.widget.installEventFilter(self)

    @property
    def widget(self):
        return self._widget

    def eventFilter(self, obj, event):
        if obj is self.widget and event.type() == QEvent.MouseMove:
            self.positionChanged.emit(event.pos())
        return super().eventFilter(obj, event)

class AppUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # self.lbl=QLabel(self)
        # self.lbl.setText("Hover over me")
        self.trackpad = QPushButton('Trackpad', self)
        self.trackpad.setGeometry(10, 10, 250, 200)
        self.trackpad.setEnabled(False)


        hover_tracker = HoverTracker(self.trackpad)
        hover_tracker.positionChanged.connect(self.on_position_changed)

        self.resize(300,300)
        self.setWindowTitle('QLineEdit')

    @pyqtSlot(QPoint)
    def on_position_changed(self, p):
        global SendQueue
        data = {
            'type': 'MOUSE',
            'value': f'{p.x()},{p.y()}'
        }
        encoded_data = json.dumps(data).encode('utf-8')
        SendQueue.put(encoded_data)
        print(p)

    def eventFilter(self, object, event):
        if event.type() == QEvent.Enter:
            print("Mouse is over the label")
            self.stop = True
            print('program stop is', self.stop)
            return True
        elif event.type() == QEvent.Leave:
            print("Mouse is not over the label")
            self.stop = False
            print('program stop is', self.stop)
        return False

if __name__ == '__main__':
    global SendQueue
    SendQueue = Queue()
    hidClient = HIDClient()
    hidClient.start()
    app = QApplication(sys.argv)
    w = AppUI()
    w.show()
    sys.exit(app.exec_())