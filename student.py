import pymysql as p
import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
import socket
import threading
from datetime import datetime

form_class = uic.loadUiType("main.ui")[0]
svrip = 'localhost'
port = 9000


class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.stackedWidget.setCurrentIndex(0)

        self.hbt_login.clicked.connect(self.login)

        # 서버 연결
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((svrip, port))
        print('연결된 서버:' + svrip)
        th = threading.Thread(target=self.receive, args=(self.sock,))
        th.start()

    def receive(self, c):
        while True:
            rmsg = c.recv(1024).decode()
            if rmsg:
                self.p_msg(c, '받은 메시지:', rmsg)
                self.reaction(c, rmsg)

###########################################################################

    def login(self):
        self.sock.sendall('login'.encode())

###########################################################################

    def reaction(self, c, msg):
        pass


###########################################################################

    def send_msg(self, head, *value):
        self.sock.sendall(head.encode())

    def p_msg(self, sock, head, *msg):
        if msg:
            print(f'{datetime.now()} / {sock.getpeername()} / {head} {msg}')
        else:
            print(f'{datetime.now()} / {sock.getpeername()} / {head}')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()