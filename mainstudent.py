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
import time

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
        self.stw.setCurrentIndex(0)
        self.read_api()
        self.action = True

        #장은희테스트
        # self.stw.setCurrentIndex(3)
        self.selected = False

        # 시그널 - 메서드
        self.hbt_add.clicked.connect(self.signup)
        self.hbt_login.clicked.connect(self.login)
        self.hle_name.returnPressed.connect(self.login)
        self.stw.tabBarClicked.connect(self.show_contents)
        self.comboBox.currentTextChanged.connect(self.select_year)
        self.study_save_btn.clicked.connect(self.save_contents)
        self.load_study_btn.clicked.connect(self.load_save)
        self.answer_table.cellChanged.connect(self.input_answer)
        self.quiz_type_box.currentTextChanged.connect(self.show_quiz)
        self.sbr_test.clicked.connect(self.clear_answer_table)


        ##장은희##
        self.sle_chat.returnPressed.connect(self.st_chat) # 실시간 상담채팅
        # QnA
        self.sbt_qa.clicked.connect(self.interpellate)
        self.stw.currentChanged.connect(self.stw_move)

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


    def show_quiz(self):# 퀴즈 내용을 요청하는 메서드
        self.send_msg('quiz_type',[self.quiz_type_box.currentText()])




    def input_answer(self, row, column): # 정답 입력하면 시간 제서 서버로 보내는 메서드
        print('hihi')
        cell_answer=self.answer_table.item(row,column).text()
        quiz_text=self.stw_test.item(row,column+1).text()
        print(quiz_text,'퀴즈텍스트')
        get_num=self.row_list[row]
        print(get_num[-1],'문제 번호')
        print(cell_answer)
        self.end=time.time()
        measure_time=(self.start-self.end)*(-1)
        sol_time=f"{measure_time:0.2f}"
        print(sol_time)
        self.start=time.time()
        self.send_msg('정답', [self.name, self.quiz_type_box.currentText(), get_num, cell_answer,sol_time,quiz_text]) # 이름, 퀴즈코드, 문제번호, 제출 답안, 풀이 시간 전달

    def show_contents(self, index): # Qtablewidget에 보여줄 학습내용 연도 선택하는 메서드
        self.comboBox.clear()
        if index==1:
            for i in range(1000,2001,100):
                if i == 2000:
                    self.comboBox.addItem(str(i) + '년' + '~' + str(i + 23)+'년')
                else:
                    self.comboBox.addItem(str(i)+'년'+'~'+str(i+100)+'년')

        elif index==2:
            self.send_msg("call_quiz", ['quiz_num' , 'score', 'quiz','quiz_code'])
            self.start = time.time()


        else:
            print(index)
    def select_year(self): # 학습할 내용을 선택하는 메서드
        self.send_msg("call_contents", ['연도', self.comboBox.currentText()])

    # 학습내용 저장하기
    def save_contents(self): # 학습할 내용 저장하는 메서드
        self.save1=self.stw_contents.item(0, 1).text()
        print(self.msg)
        self.save2=self.stw_contents.item(self.msg-1, 1).text()
        print(self.save1, self.save2)
        self.send_msg('save_contents', [self.name, self.save1, self.save2])

    def load_save(self): # 저장된 학습내용을 불러오는 메서드
        self.send_msg('loading_studying', [self.name, self.save1, self.save2])

    # 수신 메서드
    def receive(self, c):
        while True:
            new_msg = True
            tmsg = ''
            buffer = 10
            while True:
                msg = c.recv(buffer)
                tmsg += msg.decode()

                # 전송된 데이터의 길이 정보를 추출하여 buffer에 저장
                if new_msg:
                    buffer = int(msg)
                    new_msg = False
                else:
                    # json.loads할 데이터에 길이 정보를 제거
                    tmsg = tmsg[10:]
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
                self.send_msg('stu_home', [self.code, self.name])
            else:
                self.messagebox('로그인 실패')
        elif head == 'signup':
            if msg[0] == 'success':
                code = msg[1]
                self.messagebox(f'가입 성공, 발급 코드: {code} 입니다.')
            else:
                self.messagebox('가입 실패')

        elif head == 'load_history':# db learning_data  Qtablewidget에 표시

            self.msg = len(msg)
            self.stw_contents.setRowCount(0)
            self.stw_contents.setRowCount(len(msg))
            self.stw_contents.setColumnCount(3)
            header = self.stw_contents.horizontalHeader()
            for i in range(len(msg)):
                for j in range(3):
                    self.stw_contents.setItem(i, j, QTableWidgetItem(str(msg[i][j])))
            self.stw_contents.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents) #셀값에 따라 자동으로 컬럼 넓이 조절

        elif head == 'loading_studying': # 저장된 학습내용 불러옴

            self.stw_contents.setRowCount(len(msg))
            self.stw_contents.setColumnCount(3)
            for i in range(len(msg)):
                for j in range(3):
                    self.stw_contents.setItem(i, j, QTableWidgetItem(str(msg[i][j])))
        elif head == "loading_quiz": # 문제유형 선택 : self.quiz_type_box에 유형 추가

            print(msg, '퀴즈유형 확인')
            self.quiz_type_box.clear()
            for i in msg:
                self.quiz_type_box.addItem(i[0])

        #학생이 문제 풀기
        #quiz load
        elif head == 'data_quiz':
            self.stw_test.setRowCount(0)
            self.stw_test.setRowCount(len(msg))
            self.stw_test.setColumnCount(2)

            for i in range(len(msg)):
                for j in range(2):
                    self.stw_test.setItem(i, j, QTableWidgetItem(str(msg[i][j])))
            self.stw_test.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

            #정답란 제출란
            self.row_list = []
            for l in range(len(msg)):
                self.row_list.append('문제' + str(l+1))
            print(self.row_list)
            self.answer_table.setRowCount(len(msg))
            self.answer_table.setColumnCount(1)
            self.answer_table.setVerticalHeaderLabels(self.row_list)  # row 항목명 세팅

        # ####장은희
        # 실시간 상담 (자기자신)
        elif head == 'st_chat':
            self.slw_chat.addItem(f"{msg[2]} {msg[0]}/{msg[1]} 학생 : {msg[3]}")

        # 실시간 상담 (선생님->학생)
        elif head == 'at_chat':
            print('받은매시지:',msg)
            #['a1', '최', '2023-02-11 15:01', 'ㅋㅋㅋㅋㅋ', 's1', '최지혁']
            if self.code == msg[4] and self.name == msg[5]:
                self.selected = True #현재 이 학생은 선생님과 매칭된 상태
                if self.selected == True:
                    self.slw_chat.addItem(f"{msg[2]} {msg[1]} 선생님 : {msg[3]}")
                    self.slw_chat.scrollToBottom()
            else:
                pass

        # ```QnA
        # 추가 등록된 질문 받아 위젯에 넣기
        elif head == 'add_stw_qa':
            row = self.stw_qa.rowCount()
            self.stw_qa.setRowCount(row+1)
            for idx, val in enumerate(msg):
                self.stw_qa.setItem(row, idx, QTableWidgetItem(str(val)))
        # 처음 QnA 창에 들어가면 질문 내역 위젯에 넣기
        elif head == 'set_stw_qa':
            row = len(msg)
            self.stw_qa.setRowCount(row)
            for row, qna in enumerate(msg):
                for col, val in enumerate(qna):
                    self.stw_qa.setItem(row, col, QTableWidgetItem(str(val)))
        # ```
        # ``` 학생 로그인 첫 화면
        elif head == 'set_stu_home':
            self.sl_h_rating.setText(msg[0])
            self.sl_h_name.setText(msg[2])
            self.slcd_h_point.display(msg[3])
            if msg[4] != '':
                self.sle_h_progress.setText(msg[4].split(':')[1])
            self.send_msg('study', self.name)
        elif head == 'study':
            self.stw_h_score.clear()
            if msg != 'False':
                for m in msg[0]:
                    self.add_top_tree(str(m[0]), str(m[1]), str(m[2]), msg[1])
        # ```

        # tree 위젯에 item 추가하기
    def add_top_tree(self, num, name, score, value):
        item = QTreeWidgetItem(self.stw_h_score)
        item.setText(0, num)
        item.setText(1, name)
        item.setText(2, score)
        for i in value:
            if str(i[0]) == num:
                sub_item = QTreeWidgetItem(item)
                sub_item.setText(0, str(i[1]))
                sub_item.setText(1, str(i[2]))
                sub_item.setText(2, str(i[3]))
                sub_item.setText(3, str(i[4]))
                sub_item.setText(4, str(i[5]))



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
        chat_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        chat_msg = self.sle_chat.text()
        # self.slw_chat.addItem(f"{self.name}({time}) : {chat_msg}")
        if chat_msg and chat_time:
            self.send_msg('st_chat', [self.code, self.name, chat_time, chat_msg])
        self.slw_chat.scrollToBottom()
        self.sle_chat.clear()

    # ``` QnA
    # 추가 질문 등록시 서버에 DB저장하고 위제에 새로운 질문 등록하도록 신호전달
    def interpellate(self):
        question = self.sle_qa.text()
        if question:
            self.send_msg('question', [self.code, self.name, question])
            self.sle_qa.clear()
    # ```

    # tab 위젯 이동시 서버에 신호 전달
    def stw_move(self):
        tab = self.stw.currentIndex()
        if tab == 1:
            self.send_msg('stu_home', [self.code, self.name])
        # QnA창에 이동시 위젯에 질문내역 불러오게 서버에 신호전달
        elif tab == 4:
            self.send_msg('qna', [self.code, self.name])

    def clear_answer_table(self):
        self.answer_table.setRowCount(0)


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
        msg = f"{len(msg):<10}"+msg
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