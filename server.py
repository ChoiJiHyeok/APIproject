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

###########################################################################
# 스레드 객체
###########################################################################

    # 수신 메서드 ,클라 연결 종료시 종료 메시지 남기고 연결 소켓 제거
    def receive(self, c):
        while True:
            try:
                rmsg = json.loads(c.recv(1024).decode())
                if rmsg:
                    self.p_msg(c, '받은 메시지:', rmsg)
                    self.reaction(c, rmsg[0], rmsg[1])
            except ConnectionResetError:
                self.p_msg(c, '연결 종료')
                self.c_socks.remove(c)
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
            if login:
                sql = f"select distinct quiz_num from quiz;"
                quiz_num = db_execute(sql)
                self.send_msg(c, 'login', ['success', msg[0], msg[2], quiz_num])
            else:
                self.send_msg(c, 'login', ['failure'])
        # 회원가입
        elif head == 'signup':
            if msg[0] == '관리자':
                sql = "select count(*) from login_data where member_num like 'a%';"
                num = int(db_execute(sql)[0][0])+1
                sql = f"insert into login_data values('a{num}', '{msg[0]}', '{msg[1]}')"
                db_execute(sql)
                self.send_msg(c, 'signup', ['success', f'a{num}'])
            else:
                sql = "select count(*) from login_data where member_num like 's%';"
                num = int(db_execute(sql)[0][0])+1
                sql = f"insert into login_data values('s{num}', '{msg[0]}','{msg[1]}')"
                db_execute(sql)
                self.send_msg(c, 'signup', ['success', f's{num}'])
        # ``` 문제 만들기
        elif head == 'register_question':
            sql = "select count(distinct quiz_num) from quiz;"
            quiz_num = db_execute(sql)[0][0]
            if msg[0][0] > quiz_num:
                for v in msg:
                    sql = f"insert into quiz values('{v[0]}', '{v[1]}', '{v[2]}', '{v[3]}', '{v[4]}');"
                    db_execute(sql)
            else:
                sql = f"delete from quiz where quiz_num = {msg[0][0]};"
                db_execute(sql)
                for v in msg:
                    sql = f"insert into quiz values('{v[0]}', '{v[1]}', '{v[2]}', '{v[3]}', '{v[4]}');"
                    db_execute(sql)
        elif head == 'load_quiz':
            sql = f"select * from quiz where quiz_num= '{msg}'"
            quiz_list = db_execute(sql)
            self.send_msg(c, 'load_quiz', quiz_list)
        # ```

###########################################################################
# 도구 메서드
###########################################################################

    # 클라소켓, 주제, 내용으로 클라에 데이터 전송
    def send_msg(self, c, head, value):
        msg = json.dumps([head, value])
        c.sendall(msg.encode())
        self.p_msg(c, '보낸 메시지:', value)

    # 클라소켓, 메시지 종류, 내용을 매개 변수로 콘솔에 확인 내용 출력
    def p_msg(self, sock, head, *msg):
        if msg:
            print(f'{datetime.now()} / {sock.getpeername()} / {head} {msg}')
        else:
            print(f'{datetime.now()} / {sock.getpeername()} / {head}')


if __name__ == '__main__':
    server = Server()
    with TTS((server_ip, server_port), TH) as TS:
        TS.serve_forever()
