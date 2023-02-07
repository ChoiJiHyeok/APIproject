import socketserver
from datetime import datetime

server_ip = 'localhost'
server_port = 9000


# 소켓 요청 처리
class TH(socketserver.BaseRequestHandler):
    def handle(self):
        c_sock = self.request
        if c_sock not in server.c_socks:
            server.c_socks.append(c_sock)
        server.p_msg(c_sock, '연결됨')
        server.receive(c_sock)


# 서버 객체 생성
class TTS(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class MainServer:
    def __init__(self):
        self.c_socks = []

    def receive(self, c):
        while True:
            try:
                rmsg = c.recv(1024).decode()
                if rmsg:
                    self.p_msg(c, '받은 메시지:', rmsg)
                    self.reaction(c, rmsg)
            except ConnectionResetError:
                self.p_msg(c, '연결 비정상 종료')
                self.c_socks.remove(c)
                c.close()
                break
            else:
                continue

############################################################################

    def reaction(self, c, msg):
        pass


############################################################################

    def p_msg(self, sock, head, *msg):
        if msg:
            print(f'{datetime.now()} / {sock.getpeername()} / {head} {msg}')
        else:
            print(f'{datetime.now()} / {sock.getpeername()} / {head}')

    def send_msg(self, c, msg):
        c.sendall(msg.encode())
        self.p_msg(c, '보낸 메시지:', msg)


if __name__ == '__main__':
    server = MainServer()
    with TTS((server_ip, server_port), TH) as TS:
        TS.serve_forever()
