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
        self.atw.setCurrentIndex(0)
        self.user_management = False
        self.qna_show = False

        #장은희테스트
        # self.atw.setCurrentIndex(2)
        # 실시간상담채팅
        self.ale_chat.returnPressed.connect(self.at_chat) # 메시지 전송
        self.alw_chat_user.itemClicked.connect(self.select_user) # 학생별로 수신
        # self.alw_chat_user.currentItemChanged.connect(self.select_change_user) # 큐메시지박스/학생연결끊김


        # 시그널 - 메서드
        # 로그인, 회원가입
        self.hbt_add.clicked.connect(self.signup)
        self.hbt_login.clicked.connect(self.login)
        # 문제 만들기
        self.abt_add.clicked.connect(self.add_space)
        self.abt_del.clicked.connect(self.del_space)
        self.abt_finish.clicked.connect(self.register_question)
        self.abt_cancel.clicked.connect(self.del_atw_q)
        self.atw_q.currentCellChanged.connect(self.total_score)
        self.acb_num.currentIndexChanged.connect(self.send_quiz_num)
        # 학생관리
        self.atw.currentChanged.connect(self.atw_move)
        self.alw_user.itemDoubleClicked.connect(self.study_progress)

        # 서버 연결
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((svrip, port))
        self.p_msg('연결된 서버: ', svrip)
        th = threading.Thread(target=self.receive, args=(self.sock,), daemon=True)
        th.start()

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
        # 로그인
        if head == 'login':
            # 로그인 성공
            if msg[0] == 'success':
                # 나중에 쓸수도 있기에 만든 변수
                self.code = msg[1]
                self.name = msg[2]
                # 관리자 페이지 이동
                self.stackedWidget.setCurrentIndex(2)
                # 문제 등록 번호 콤보박스에 등록
                for i in msg[3]:
                    self.acb_num.addItem(str(i[0]))
                self.messagebox('로그인 성공')
            # 로그인 실패
            else:
                self.messagebox('로그인 실패')
        # 회원가입
        elif head == 'signup':
            # 가입 성공 및 회원 코드 띄우기
            if msg[0] == 'success':
                code = msg[1]
                self.messagebox(f'가입 성공, 발급 코드: {code} 입니다.')
            # 가입 실패 코드 띄우기
            else:
                self.messagebox('가입 실패')
        # ``` 문제 만들기
        # 테이블 위젯에 문제 띄우기
        elif head == 'load_quiz':
            # 테이블 위젯 셋팅
            self.atw_q.setRowCount(0)
            self.atw_q.setRowCount(len(msg))
            # 테이블 위젯 셀에 내용 저장
            for row, quiz_list in enumerate(msg):
                for col, value in enumerate(quiz_list):
                    if col != 0:
                        self.atw_q.setItem(row, col-1, QTableWidgetItem(value))
        # 추가된 문제 등록번호 콤보박스에 저장
        elif head == 'add_acb_num':
            self.acb_num.addItem(str(msg))
        # ```
        # ``` 학생 관리
        # 처음 학생 관리창 들어가면 전체 학생 리스트 불러오기
        elif head == 'management':
            self.alw_user.clear()
            for value in msg:
                self.alw_user.addItem(f'[{value[0]}]{value[1]}')
        # 학생 회원가입시 코드및 이름 받아오기
        elif head == 'add_alw_user':
            self.alw_user.addItem(f'[{msg[0]}]{msg[1]}')

        elif head == 'study':
            self.atw_record.clear()
            if msg != 'False':
                for m in msg[0]:
                    self.add_top_tree(str(m[0]), str(m[1]), str(m[2]), msg[1])
        # ```
        # ###장은희
        # alw_chat_user에 학생 넣기
        elif head == 'chat_user':
            self.alw_chat_user.clear()
            for i in range(len(msg)):
                self.alw_chat_user.addItem(f"{msg[i][0]}/{msg[i][2]}")

        # 실시간 상담 (학생->선생님)
        elif head == 'st_chat':
            if self.select_code == msg[0] and self.select_name == msg[1]:
                self.alw_chat.addItem(f"{msg[2]} {msg[0]}/{msg[1]} 학생 : {msg[3]}")
                self.alw_chat.scrollToBottom()

        # 실시간 상담 (자기자신)
        elif head == 'at_chat':
            self.alw_chat.addItem(f"{msg[2]} {msg[1]} 선생님 : {msg[3]}")

        elif head == 'select_user':
            self.alw_chat.clear()
            print('이전메시지', msg)
            for i in range(len(msg)):
                self.alw_chat.addItem(f"{msg[i][2]} {msg[i][0]}/{msg[i][1]} 학생 : {msg[i][3]}")
                self.alw_chat.scrollToBottom()

        # ``` QnA
        # 처음 QnA창에 들어가면 질문내역 위젯에 등록
        elif head == 'set_stw_qa':
            self.atw_qa.setRowCount(len(msg))
            for row, qna in enumerate(msg):
                for col, val in enumerate(qna):
                    self.atw_qa.setItem(row, col, QTableWidgetItem(str(val)))
        # 추가된 질문 받아와 위젯에 등록
        elif head == 'add_stw_qa':
            row = self.atw_qa.rowCount()
            self.atw_qa.setRowCount(row+1)
            for idx, val in enumerate(msg):
                self.atw_qa.setItem(row, idx, QTableWidgetItem(str(val)))
        # ```

    # tree 위젯에 item 추가하기
    def add_top_tree(self, num, name, score, value):
        item = QTreeWidgetItem(self.atw_record)
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
# 송신
###########################################################################

    # 로그인 (선생 프로그램으로 서버에 [선생 코드, 권한, 이름] 전송)
    def login(self):
        code = self.hle_code.text()
        name = self.hle_name.text()
        if code and name:
            self.send_msg('login', [code, '관리자', name])
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

    # 문제 등록 (서버에 [문제 목록] 전송)
    def register_question(self):
        # 콤보 박스 내용이 숫자가 아닌경우 신규 문제 등록
        try:
            box = int(self.acb_num.currentText())
        except ValueError:
            box = self.acb_num.count()
        # 초기 셋팅
        t_list = []
        row = self.atw_q.rowCount()
        col = self.atw_q.columnCount()
        # 테이블 위젯의 셀 내용 list에 저장하기
        try:
            for i in range(row):
                q_list = [box]
                for j in range(col):
                    if j < 2:
                        q_list.append(self.atw_q.item(i, j).text())
                    else:
                        q_list.append(int(self.atw_q.item(i, j).text()))
                t_list.append(q_list)
            # 등록할 문제 목록의 배점 합계가 100점인지 여부 확인
            score = int(self.al_score.text())
            if score == 100:
                self.send_msg('register_question', t_list)
                self.atw_q.clearContents()
                self.atw_q.setRowCount(0)
                self.al_score.setNum(0)
            else:
                self.messagebox('만점은 100 입니다.')
        # 작성된 문제 목록에 문제가 있는경우
        except ValueError:
            self.messagebox('배점 또는 point란에 문자가 있습니다.')
        except AttributeError:
            self.messagebox('빈칸이 있습니다.')

    # 문제 등록 넘버를 서버로 송신
    def send_quiz_num(self):
        num = self.acb_num.currentText()
        self.send_msg('load_quiz', num)

    # tab위젯 tab이동시 index 받기
    def atw_move(self):
        tab = self.atw.currentIndex()
        if tab == 1 and not self.user_management:
            self.user_management = True
            self.send_msg('management', '')
        # 장은희_상담탭 구현중
        elif tab == 2: # alw_chat_user에 학생 넣기. 시그널 전송
            self.send_msg('chat_user', '')
        elif tab == 3 and not self.qna_show:
            self.qna_show = True
            self.send_msg('qna_adin', '')

    # 학생관리창에서 학생이름을 더블 클릭하면 서버에 신호 전송
    def study_progress(self):
        name = self.alw_user.currentItem().text().split(']')[1]
        self.send_msg('study', name)


    #####장은희
    # 상담 (관리자 프로그램으로 서버에 [관리자코드, 관리자이름, 채팅시간, 채팅내용] 전송)
    def at_chat(self):
        chat_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        chat_msg = self.ale_chat.text()
        # self.alw_chat.addItem(f"{self.name}({time}) : {chat_msg}")
        if chat_msg and chat_time:
            self.send_msg('at_chat', [self.code, self.name, chat_time, chat_msg])
        self.alw_chat.scrollToBottom()
        self.ale_chat.clear()

    def select_user(self): # 아이템클릭/서버한테 '학생별로 수신받고 싶어' 시그널 보내기
        self.selectName = self.alw_chat_user.currentItem().text()
        self.send_msg('select_user', self.selectName)

        select_user = self.selectName.split('/')
        self.select_code = select_user[0]
        self.select_name = select_user[1]
        print(self.select_name)





###########################################################################
# 송신 기능이 없는 시그널 - 메서드
###########################################################################

    # 문제목록에 문제 추가 하기
    def add_space(self):
        num = self.atw_q.rowCount()
        self.atw_q.setRowCount(num+1)

    # 문제목록에 문제 삭제 하기
    def del_space(self):
        max_num = self.atw_q.rowCount()
        num = self.atw_q.currentRow()
        # 테이블 위젯의 선택한 셀이 없는 경우
        if num < 0:
            num = max_num-1
        # 테이블 위젯의 특정 셀의 행 지우기
        self.atw_q.removeRow(num)

    # 선택셀 변경시 배점 총합을 라벨에 출력
    def total_score(self):
        row = self.atw_q.rowCount()
        score = 0
        # 작성중 계속 시그널이 들어오는 함수로 애러 발생을 pass 처리
        try:
            for i in range(row):
                score += int(self.atw_q.item(i, 2).text())
            self.al_score.setNum(score)
        except AttributeError:
            pass
        except ValueError:
            pass

    # 문제목록의 내용 전부 삭제
    def del_atw_q(self):
        self.atw_q.clearContents()
        self.atw_q.setRowCount(0)

    # 학생연결 종료
    # def select_change_user(self):
    #     self.messagebox('현재 상담중인 학생과 연결이 종료됩니다.')
    #     self.alw_chat.clear()







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
        # 단순히 보기 편하게 할려고 만든 조건
        if msg:
            print(f'{datetime.now()} / {head} {msg}')
        else:
            print(f'{datetime.now()} / {head}')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()