import json
import sys
from tkinter import messagebox, Tk
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

        self.hbt_add.clicked.connect(self.signup)
        self.hbt_login.clicked.connect(self.login)

        # 서버 연결
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((svrip, port))
        print('연결된 서버:' + svrip)
        th = threading.Thread(target=self.receive, args=(self.sock,))
        th.start()

    def receive(self, c):
        while True:
            rmsg = json.loads(c.recv(1024).decode())
            if rmsg:
                self.p_msg(c, '받은 메시지:', rmsg)
                self.reaction(c, rmsg[0], rmsg[1])

###########################################################################

    def login(self):
        code = self.hle_code.text()
        name = self.hle_name.text()
        if code and name:
            self.send_msg('login', [code, '관리자', name])
        else:
            self.messagebox('로그인 실패')
        self.hle_code.clear()
        self.hle_name.clear()

    def signup(self):
        name = self.hle_add_name.text()
        admin = self.hrb_admin.isChecked()
        user = self.hrb_user.isChecked()
        if admin:
            self.send_msg('signup', ['관리자', name])
        elif user:
            self.send_msg('signup', ['학생', name])
        self.hle_add_name.clear()

###########################################################################

    def reaction(self, c, head, msg):
        print(head, msg)
        if head == 'login':
            if msg[0] == 'success':
                self.stackedWidget.setCurrentIndex(2)
                self.code = msg[1]
                self.name = msg[2]
                self.messagebox('로그인 성공')
            else:
                self.messagebox('로그인 실패')
        elif head == 'signup':
            if msg[0] == 'success':
                code = msg[1]
                self.messagebox(f'가입 성공, 발급 코드: {code} 입니다.')
            else:
                self.messagebox('가입 실패')

###########################################################################

    def messagebox(self, value):
        tk_window = Tk()
        tk_window.geometry("0x0+3000+6000")
        messagebox.showinfo('안내창', f'{value}')
        tk_window.destroy()

    def send_msg(self, head, value):
        msg = json.dumps([head, value])
        self.sock.sendall(msg.encode())
        self.p_msg(self.sock, '보낸 메시지:', msg)

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