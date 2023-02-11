import pymysql as p
import socketserver
from datetime import datetime
import json

server_ip = 'localhost'
server_port = 9000

db_host = '10.10.21.105'
db_port = 3306
db_user = 'network'
db_pw = 'aaaa'
db = 'api'


# DB에 값을 변경하거나 불러오는 함수
def db_execute(sql):
    conn = p.connect(host=db_host, port=db_port, user=db_user, password=db_pw, db=db, charset='utf8')
    c = conn.cursor()
    c.execute(sql)
    conn.commit()
    conn.close()
    return c.fetchall()


# 소켓 연결 요청 처리
class TH(socketserver.BaseRequestHandler):
    def handle(self):
        c_sock = self.request
        if c_sock not in server.c_socks:
            server.c_socks.append(c_sock)
        server.p_msg(c_sock, '연결됨')
        server.receive(c_sock)


# 소켓 객체 생성
class TTS(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


# 메인서버
class Server:
    def __init__(self):
        self.c_socks = []
        self.admin_socks = []
        self.student_socks = []

###########################################################################
# 스레드 객체
###########################################################################

    # 수신 메서드 ,클라 연결 종료시 종료 메시지 남기고 연결 소켓 제거
    def receive(self, c):
        while True:
            try:
                rmsg = json.loads(c.recv(4096).decode())
                if rmsg:
                    self.p_msg(c, '받은 메시지:', rmsg)
                    self.reaction(c, rmsg[0], rmsg[1])
            except ConnectionResetError:
                self.p_msg(c, '연결 종료')
                self.c_socks.remove(c)
                print('연결된 클라: ', len(self.c_socks))
                if c in self.student_socks:
                    self.student_socks.remove(c)
                    print('연결된 학생: ', len(self.student_socks))
                if c in self.admin_socks:
                    self.admin_socks.remove(c)
                    print('연결된 선생: ', len(self.student_socks))
                c.close()
                break
            else:
                continue

    # 반응 메서드
    def reaction(self, c, head, msg):
        print(head, msg)
        # 로그인
        if head == 'login':
            sql = f"select * from login_data where member_num = '{msg[0]}' and authority = '{msg[1]}' and member_name='{msg[2]}';"
            login = db_execute(sql)
            # 클라에서 받은 정보가 DB에 등록 되어 있는경우
            if login:
                # DB에 저장된 문제 등록 목록 및 정보 클라에 전달
                # [로그인성공여부, 회원코드, 회원이름, 문제등록번호목록]
                sql = f"select distinct quiz_num from quiz;"
                quiz_num = db_execute(sql)
                self.send_msg(c, 'login', ['success', msg[0], msg[2], quiz_num])
                # 정보를 선생과 학생으로 구분하여 전송하기위해 list에 소켓 저장
                if msg[1] == '관리자':
                    self.admin_socks.append(c)
                    print('현재연결된선생소켓', self.admin_socks)
                elif msg[1] == '학생':
                    self.student_socks.append(c)
                    print('현재연결된학생소켓',self.student_socks)
            # 학생 또는 선생 프로그램에서 다른 권한의 계정으로 로그인 시도한 경우
            # 로그인 정보가 틀린경우
            else:
                self.send_msg(c, 'login', ['failure'])
        # 회원가입
        elif head == 'signup':
            # 관리자 권한 가입 정보 DB에 저장 및 정보 전송 [성공여부, 회원 코드]
            if msg[0] == '관리자':
                # 회원 코드를 생성하기위해 번호조회
                sql = "select count(*) from login_data where member_num like 'a%';"
                num = int(db_execute(sql)[0][0])+1
                # DB에 회원 정보 등록[회원코드, 권한, 이름]
                sql = f"insert into login_data values('a{num}', '{msg[0]}', '{msg[1]}')"
                db_execute(sql)
                self.send_msg(c, 'signup', ['success', f'a{num}'])
            # 학생 권한 가입 정보 DB에 저장 및 정보 전송 [성공여부, 회원 코드]
            else:
                # 회원 코드를 생성하기위해 번호조회
                sql = "select count(*) from login_data where member_num like 's%';"
                num = int(db_execute(sql)[0][0])+1
                # DB에 회원 정보 등록[회원코드, 권한, 이름]
                sql = f"insert into login_data values('s{num}', '{msg[0]}','{msg[1]}')"
                db_execute(sql)
                # 회원관리 DB에 신규 등록
                sql = f"insert into study_progress values('F','s{num}','{msg[1]}', '0', '0');"
                db_execute(sql)
                self.send_msg(c, 'signup', ['success', f's{num}'])
                for client in self.admin_socks:
                    self.send_msg(client, 'add_alw_user', [f's{num}', f'{msg[1]}'])

        # ``` 문제 만들기
        # 문제 등록하기
        elif head == 'register_question':
            sql = "select count(distinct quiz_num) from quiz;"
            quiz_num = db_execute(sql)[0][0]
            # 신규 문제
            if msg[0][0] > quiz_num:
                # 문제 DB에 저장
                for v in msg:
                    sql = f"insert into quiz values('{v[0]}', '{v[1]}', '{v[2]}', '{v[3]}', '{v[4]}');"
                    db_execute(sql)
                # 관리자 권한을 가진 모든 클라에게 전송 [추가 등록된 문제 등록 번호]
                for administrator in self.admin_socks:
                    self.send_msg(administrator, 'add_acb_num', msg[0][0])
            # 기존 문제 수정
            else:
                sql = f"delete from quiz where quiz_num = {msg[0][0]};"
                db_execute(sql)
                for v in msg:
                    sql = f"insert into quiz values('{v[0]}', '{v[1]}', '{v[2]}', '{v[3]}', '{v[4]}');"
                    db_execute(sql)
        # 해당 등록 번호의 문제 목록 클라에 전송
        elif head == 'load_quiz':
            sql = f"select * from quiz where quiz_num= '{msg}'"
            quiz_list = db_execute(sql)
            self.send_msg(c, 'load_quiz', quiz_list)
        # ```
        # ``` 학생 관리
        elif head == 'management':
            sql = "select member_num ,member_name from login_data where member_num like 's%';"
            user_infor = db_execute(sql)
            self.send_msg(c, 'management', user_infor)
        elif head == 'study':
            sql = f"select quiz_num, min(student_name), sum(quiz_point) as sum from quiz_student" \
                  f" where student_name = '{msg}' group by quiz_num;"
            user_infor = db_execute(sql)
            sql = f"select * from quiz_student where student_name = '{msg}' order by quiz_num;"
            more_infor = db_execute(sql)
            if user_infor:
                self.send_msg(c, 'study', [user_infor, more_infor])
            else:
                self.send_msg(c, 'study', 'False')
        #```
        # 학생용
        # 학생이 학습내용 풀러오기

        elif head == 'call_contents':
            if msg[1] != '연도선택':
                try:
                    year=msg[1].split("~")
                    print(year)
                    sql=f'SELECT *FROM learning_data WHERE date BETWEEN "{year[0]}" AND "{year[1]}"'
                    study_contents=db_execute(sql)
                    print(study_contents)
                    self.send_msg(c,'load_history',study_contents)
                except IndexError:
                    print('study')
            else:
                print('gg')
        elif head == "save_contents": # 학습내용 저장 하기
            sql=f'UPDATE study_progress SET study_progress = "{msg[0]}:{msg[1]}~{msg[2]}" WHERE student_name = "{msg[0]}"'
            update_progress=db_execute(sql)
            print(update_progress)

        elif head == 'loading_studying': #저장된 학습내용 불러오기
            sql=f'SELECT *FROM learning_data WHERE date BETWEEN "{msg[1]}" AND "{msg[2]}"'
            find_contents=db_execute(sql)
            self.send_msg(c,'loading_studying',find_contents)

        elif head == 'call_quiz':
            sql=f'SELECT {msg[0]},{msg[1]},{msg[2]} FROM api.quiz'
            find_quiz=db_execute(sql)
            print(find_quiz,'퀴즈전송')
            self.send_msg(c,'loading_quiz',find_quiz)

        elif head == '정답':
            sql=f'SELECT count(*)FROM quiz_student WHERE quiz_num="{msg[1][-1]}" AND student_name="{msg[0]}"';
            count_data=db_execute(sql)
            print(count_data)
            if count_data[0][0] == 0:
                # sql1=f"INSERT INTO quiz_student ()"
                sql2=f'SELECT quiz FROM api.quiz WHERE quiz_num="{msg[1][-1]}"'
                see_quiz=db_execute(sql2)
                print(see_quiz,'확인하자')






        # ####장은희
        # 실시간 상담 (학생프로그램)
        elif head == 'st_chat':
            member_num = msg[0]
            member_name = msg[1]
            chat_time = msg[2]
            chat_msg = msg[3]
            sql = f"insert into chatlog values \
                  ('{member_num}','{member_name}','{chat_time}','{chat_msg}')"
            db_execute(sql)
            st_chat_list = [member_num, member_name, chat_time, chat_msg]
            self.send_msg(c, 'st_chat', st_chat_list)
            # 관리자 권한을 가진 모든 클라에게 전송
            for admin in self.admin_socks:
                self.send_msg(admin, 'st_chat', st_chat_list)

        # 실시간 상담 (관리자프로그램)
        elif head == 'at_chat':
            member_num = msg[0]
            member_name = msg[1]
            chat_time = msg[2]
            chat_msg = msg[3]
            sql = f"insert into chatlog values \
                  ('{member_num}','{member_name}','{chat_time}','{chat_msg}')"
            db_execute(sql)
            at_chat_list = [member_num, member_name, chat_time, chat_msg]
            # self.send_msg(c, 'at_chat', at_chat_list)
            # # 학생 클라에게 전송
            for student in self.student_socks:
                self.send_msg(student, 'at_chat', at_chat_list)

        elif head == 'select_user':
            select_user = msg.split('/')
            self.select_code = select_user[0]
            self.select_name = select_user[1]
            sql = f"select * from chatlog where member_num = '{self.select_code}' and member_name = '{self.select_name}'"
            at_select_user = db_execute(sql)
            print('121313123',at_select_user)
            #본인 클라에게 전송
            self.send_msg(c, 'select_user', at_select_user)

        elif head == 'chat_user':
            sql = f"SELECT * FROM api.login_data where authority = '학생'"
            alw_chat_user_list = db_execute(sql)
            for admin in self.admin_socks:
                self.send_msg(admin, 'chat_user', alw_chat_user_list)



###########################################################################
# 도구 메서드
###########################################################################

    # 클라소켓, 주제, 내용으로 클라에 데이터 전송
    def send_msg(self, c, head, value):
        msg = json.dumps([head, value])
        print('서버 전송 바이트: ', len(msg))
        # 전송 데인터의 처음 10바이트를 전송 길이정보를 넣어 전송
        msg = f"{len(msg):<10}"+msg
        c.sendall(msg.encode())
        self.p_msg(c, '보낸 메시지:', value)

    # 클라소켓, 메시지 종류, 내용을 매개 변수로 콘솔에 확인 내용 출력
    def p_msg(self, sock, head, *msg):
        # 단순히 보기 편하게 할려고 만든 조건
        if msg:
            print(f'{datetime.now()} / {sock.getpeername()} / {head} {msg}')
        else:
            print(f'{datetime.now()} / {sock.getpeername()} / {head}')


if __name__ == '__main__':
    server = Server()
    with TTS((server_ip, server_port), TH) as TS:
        TS.serve_forever()
