# select 모듈을 이용한 TCP 클라이언트 프로그램

from socket import *
from select import *

socks = []
sock = socket()
sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
socks.append(sock)
sock.connect(('localhost', 2500))

while True:
    r_sock, w_sock, e_sock = select(socks, [], [], 0)
    # 입력을 받은 경우
    if r_sock:
        print('받음')
        for s in r_sock:
            # 입력을 받든 경우
            if s == sock:
                print('내소켓: ', s)
                msg = sock.recv(1024).decode()
                print('받은 메시지: ', msg)
    smsg = input('보낼 메시지: ')
    sock.send(smsg.encode())
