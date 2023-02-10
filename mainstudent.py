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
#
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

        # 시그널 - 메서드

        self.hbt_add.clicked.connect(self.signup)
        self.hbt_login.clicked.connect(self.login)
        self.hle_name.returnPressed.connect(self.login)
        self.stw.tabBarClicked.connect(self.show_contents)
        self.comboBox.currentTextChanged.connect(self.select_year)
        self.study_save_btn.clicked.connect(self.save_contents)
        self.load_study_btn.clicked.connect(self.load_save)
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

    def show_contents(self, index): # Qtablewidget에 보여줄 학습내용 연도 선택
        self.comboBox.clear()
        if index==1:
            for i in range(1000,2001,100):
                if i == 2000:
                    self.comboBox.addItem(str(i) + '년' + '~' + str(i + 23)+'년')
                    # self.send_msg('call_contents', [index, self.comboBox.currentText()])
                else:
                    self.comboBox.addItem(str(i)+'년'+'~'+str(i+100)+'년')
                    # self.send_msg('call_contents', [index, self.comboBox.currentText()])
        else:
            print(index)
        # if index == 2:

    def select_year(self):
        self.send_msg("call_contents", ['연도', self.comboBox.currentText()])

    # 학습내용 저장하기
    def save_contents(self):
        self.save1=self.stw_contents.item(0, 1).text()
        print(self.msg)
        self.save2=self.stw_contents.item(self.msg-1, 1).text()
        print(self.save1, self.save2)
        self.send_msg('save_contents', [self.name, self.save1, self.save2])

    def load_save(self):
        self.send_msg('loading_studying', [self.name, self.save1, self.save2])

    # 수신 메서드
    def receive(self, c):
        while True:
            new_msg = True
            tmsg = ''
            while True:
                msg = c.recv(1024)
                tmsg += msg.decode()

                print(tmsg)
                # 전송된 데이터의 길이 정보를 추출
                if new_msg:
                    size = int(msg[:10])
                    # json.loads할 데이터에 길이 정보를 제거
                    tmsg = tmsg[10:]
                    new_msg = False

                # 전송된 데이터의 길이 정보와 json.loads할 데이터의 길이가 같으면 반복문 종료
                if len(tmsg) == size:
                    break
            rmsg = json.loads(tmsg)
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
        # db learning_data  Qtablewidget에 표시
        elif head == 'load_history':
            self.msg = len(msg)
            self.stw_contents.setRowCount(len(msg))
            self.stw_contents.setColumnCount(3)
            for i in range(len(msg)):
                for j in range(3):
                    self.stw_contents.setItem(i, j, QTableWidgetItem(str(msg[i][j])))
            # self.stw_contents.resizeColumnsToContents() # 내용에 따라서 크리 자동으로 조절
        # 저장된 학습내용 불러옴
        elif head == 'loading_studying':
            self.stw_contents.setRowCount(len(msg))
            self.stw_contents.setColumnCount(3)
            for i in range(len(msg)):
                for j in range(3):
                    self.stw_contents.setItem(i, j, QTableWidgetItem(str(msg[i][j])))
        # ####장은희
        # 실시간 상담 (자기자신)
        elif head == 'st_chat':
            self.slw_chat.addItem(f"{msg[1]}({msg[2]}) : {msg[3]}")
        # 실시간 상담 (선생님->학생)
        elif head == 'at_chat':
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