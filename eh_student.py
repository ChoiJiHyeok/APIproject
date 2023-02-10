import pymysql as p
import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
import socket
import threading
from datetime import datetime
import requests
import xmltodict as xmltodict
import math
from tkinter import messagebox, Tk
import json


form_class = uic.loadUiType("main.ui")[0]
svrip = 'localhost'
port = 9000

db_host = '10.10.21.105'
db_port = 3306
db_user = 'network'
db_pw = 'aaaa'
db = 'api'


def db_execute(sql):
    conn = p.connect(host=db_host, port=db_port, user=db_user, password=db_pw, db=db, charset='utf8')
    c = conn.cursor()
    c.execute(sql)
    conn.commit()
    conn.close()
    return c.fetchall()


class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.stackedWidget.setCurrentIndex(0)
        self.read_api()
        self.action = True

        #장은희테스트
        self.stw.setCurrentIndex(3)

        # 시그널 - 메서드

        self.hbt_add.clicked.connect(self.signup)
        self.hbt_login.clicked.connect(self.login)
        ##장은희##
        self.sle_chat.returnPressed.connect(self.st_chat) # 실시간 상담채팅

        # 서버 연결
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((svrip, port))
        self.p_msg('연결된 서버: ', svrip)
        th = threading.Thread(target=self.receive, args=(self.sock,), daemon=True)
        th.start()

    # API 자료가 업데이트 돼면 DB자료 변경
    def read_api(self):
        key = 'cbbbb410eb3d4bfa88e79a9172862f'
        url = f'http://www.incheon.go.kr/dp/openapi/data?apicode=10&page=1&key={key}'
        data_total = int(xmltodict.parse(requests.get(url).content)['data']['totalCount'])
        total_page = math.ceil(data_total / 10)
        sql = f'select count(*) from learning_data;'
        api = db_execute(sql)[0][0]
        if api < data_total:
            sql = 'delete from learning_data;'
            db_execute(sql)
            for page in range(1, total_page + 1):
                url = f'http://www.incheon.go.kr/dp/openapi/data?apicode=10&page={page}&key={key}'
                content = requests.get(url).content
                dict = xmltodict.parse(content)
                data = dict['data']
                date_item = data['list']['item']
                for i in date_item:
                    data_listnum = i['listNum']
                    data_year = i['histYear']
                    data_month = i['histDate'][0] + i['histDate'][1]
                    data_day = i['histDate'][2] + i['histDate'][3]
                    date_summary = i['summary']
                    spl = f'insert into learning_data values ({data_listnum},"{data_year}년 {data_month}월 {data_day}일","{date_summary}")'
                    db_execute(spl)

    # 수신 메서드
    def receive(self, c):
        while True:
            rmsg = json.loads(c.recv(1024).decode())
            if rmsg:
                self.p_msg('받은 메시지:', rmsg)
                self.reaction(rmsg[0], rmsg[1])

    # 반응 메서드
    def reaction(self, head, msg):
        print(head, msg)
        if head == 'login':
            if msg[0] == 'success':
                self.stackedWidget.setCurrentIndex(1)
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
        #####장은희
        # 실시간 상담 (자기자신)
        elif head == 'st_chat':
            self.slw_chat.addItem(f"{msg[1]}({msg[2]}) : {msg[3]}")
        # 실시간 상담 (선생님->학생)
        elif head == 'at_chat':
            if self.hle_code.text() == msg[0]:
                self.slw_chat.addItem(f"{msg[1]}({msg[2]}) : {msg[3]}")
                self.slw_chat.scrollToBottom()


###########################################################################
# 시그널 - 메서드
###########################################################################
    # 로그인 (학생 프로그램으로 서버에 [학생 코드, 권한, 이름] 전송)
    def login(self):
        code = self.hle_code.text()
        name = self.hle_name.text()
        if code and name:
            self.send_msg('login', [code, '학생', name])
        else:
            self.messagebox('로그인 실패')
        self.hle_code.clear()
        self.hle_name.clear()

    # 회원 가입 (선생, 학생 프로그램 상관없이 서버에 [권한, 이름] 전송)
    def signup(self):
        name = self.hle_add_name.text().split()[0]
        admin = self.hrb_admin.isChecked()
        user = self.hrb_user.isChecked()
        if name:
            if admin:
                self.send_msg('signup', ['관리자', name])
            elif user:
                self.send_msg('signup', ['학생', name])
            self.hle_add_name.clear()

    #####장은희
    # 상담 (학생 프로그램으로 서버에 [학생코드, 학생이름, 채팅시간, 채팅내용] 전송)
    def st_chat(self):
        chat_time = str(datetime.now()) #strftime("%Y-%m-%d %H:%M:%S")
        time = datetime.now().strftime("%H:%M")
        chat_msg = self.sle_chat.text()
        # self.slw_chat.addItem(f"{self.name}({time}) : {chat_msg}")
        if chat_msg and chat_time:
            self.send_msg('st_chat', [self.code, self.name, chat_time, chat_msg, time])
        self.slw_chat.scrollToBottom()
        self.sle_chat.clear()



###########################################################################
# 도구 메서드
###########################################################################

    # tkinter 를 이용한 messagbox 송출
    def messagebox(self, value):
        tk_window = Tk()
        tk_window.geometry("0x0+3000+6000")
        messagebox.showinfo('안내창', f'{value}')
        tk_window.destroy()

    # 주제, 내용으로 서버에 데이터 전송
    def send_msg(self, head, value):
        msg = json.dumps([head, value])
        self.sock.sendall(msg.encode())
        self.p_msg('보낸 메시지:', msg)

    # 메시지 종류, 내용을 매개 변수로 콘솔에 확인 내용 출력
    def p_msg(self, head, *msg):
        if msg:
            print(f'{datetime.now()} / {head} {msg}')
        else:
            print(f'{datetime.now()} / {head}')




if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()