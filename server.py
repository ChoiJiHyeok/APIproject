# select()를 이용한 다중 TCP 에코 서버
# 읽기 이벤트만 조사한다.

import socket, select

sock_list = []
buffer = 1024
port = 2500
# 서버 소켓을 생성
s_sock = socket.socket()
s_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s_sock.bind(('localhost', port))
s_sock.listen(5)

sock_list.append(s_sock)
print(f'{port}연결대기중 : ...')

while True:
    # 읽기, 쓰기, 애러 = select.select(읽기 감시 소켓, 쓰기 감시 소켓, 애러 감시 소켓, 블로킹 모드 설정)
    # 블로킹 모드 : 기본값, 넌 블로킹 모드 : select.select([], [], [], 0)
    r_sock, w_sock, e_sock = select.select(sock_list, [], [], 0)

    for s in r_sock:

        # 이곳에 있는게 맞지 않나? 한번 해보고 안돼면 지우자
        # c_sock, addr = s_sock.accept()

        # 서버 소켓 에서 입력 받은 경우
        if s == s_sock:
            c_sock, addr = s_sock.accept()
            sock_list.append(c_sock)
            print(f'{addr[0]} : {addr[1]} 연결')
        # 클라이언트 소켓 에서 입력 받은 경우
        else:
            try:
                data = s.recv(buffer)
                print('받은메시지: ', data.decode())
                if data:
                    print('보낸 소켓: ', s)
                    print('보낸 메시지: ', data)
                    c_sock.send(data)
            # 연결 종료
            except:
                print(f'{addr[0]} : {addr[1]} 연결 종료')
                s.close()
                sock_list.remove(s)
                continue
s_sock.close()
