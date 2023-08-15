import json
import pyautogui
import socket
import sys
import time

from abc import ABC, abstractmethod
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout
from threading import Thread

gettime = lambda: time.time()

class Event(ABC):
    def __init__(self):
        self.time = gettime()
    
    @abstractmethod
    def handle():
        pass

class KeyboardEvent(Event):
    def __init__(self, key):
        super().__init__()
        self.key = key
    
    def handle(self):
        global keyLabel
        if pyautogui.isValidKey(self.key):
            # # if pag.isShiftCharacter(self.key):
            # #     pag.keyDown('shift')
            # pag.press(self.key)
            keyLabel.setText(f'{self.key}')
            print(self.time, 'Key Event:', self.key)

class MouseEvent(Event):
    def __init__(self, X, Y):
        super().__init__()
        self.X = X
        self.Y = Y

    def handle(self):
        # pag.moveTo(self.X, self.Y)
        global mouseValue
        mouseValue.setText(f'{self.X}, {self.Y}')
        print(self.time, 'Mouse Event:', self.X, self.Y)

class VirtualDevice(Thread):
    def __init__(self, name):
        super().__init__()
        self.event_queue: list[Event] = []
        self.daemon = True
        self.name = name

    def run(self):
        print(f'[VirtualDevice] Stared {self.name} device')
        while True:
            if len(self.event_queue) > 0:
                event: Event = self.event_queue.pop(0)
                event.handle()

    def interrupt(self, event: Event):
        self.event_queue.append(event)

class VirtualKeyboardMouse:
    def __init__(self):
        self.Keyboard = VirtualDevice('Keyboard')
        self.Mouse = VirtualDevice('Mouse')

    def start(self):
        self.Keyboard.start()
        self.Mouse.start()

    def process(self, rawdata):
        try:
            # crude data sanitization TODO: fix this
            data_str = rawdata.decode('utf-8')
            data_str = data_str[data_str.index('{'):data_str.rindex('}')+1]
            decoded_data_ls = json.loads(f'[{data_str}]')
            for decoded_data in decoded_data_ls:
                if decoded_data['type'] == 'KEY':
                    self.Keyboard.interrupt(KeyboardEvent(decoded_data['value']))
                elif decoded_data['type'] == 'MOUSE':
                    [X, Y] = decoded_data['value'].split(',')
                    self.Mouse.interrupt(MouseEvent(X, Y))
        except:
            print('Couldn\'t process data', rawdata)


class HIDServer(Thread):
    def __init__(self, PORT=12321):
        super().__init__()
        self.HOST = '127.0.0.1'
        self.PORT = PORT
        self.daemon = True
        self.virtdev = VirtualKeyboardMouse()
        self.stopped = False

    def run(self):
        self.virtdev.start()
        while not self.stopped:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((self.HOST, self.PORT))
                # print('Is anyone there?')
                print(f'[HIDServer] Started at {self.HOST}:{self.PORT}')
                s.listen()
                conn, addr = s.accept()
                with conn:
                    print(f'Client connected: {addr}')
                    while not self.stopped:
                        data = conn.recv(1024)
                        if data:
                            self.virtdev.process(data)

class AppUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        global keyLabel
        global mouseValue
        
        keyPressLabel = QLabel('Last Key Pressed')
        mousePosLabel = QLabel('Last Mouse Position')
        keyLabel = QLabel('None')
        mouseValue = QLabel('None')

        lbox = QVBoxLayout()
        lbox.addWidget(keyPressLabel)
        lbox.addWidget(mousePosLabel)

        vbox = QVBoxLayout()
        vbox.addWidget(keyLabel)
        vbox.addWidget(mouseValue)

        hbox = QHBoxLayout()
        hbox.addLayout(lbox)
        hbox.addLayout(vbox)

        self.resize(300,300)
        self.setLayout(hbox)
        self.setWindowTitle('VirtualKeyboardMouse')

if __name__ == '__main__':
    hidserver = HIDServer()
    hidserver.start()
    app = QApplication(sys.argv)
    w = AppUI()
    w.show()
    sys.exit(app.exec_())