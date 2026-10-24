"""노트북으로 Tello 드론 조종하기 (Python 3)

Tello의 Wi-Fi에 노트북을 연결한 뒤 실행하고, 명령을 한 줄씩 입력한다.
    command      SDK 모드 시작 (가장 먼저 입력)
    takeoff / land
    up 50, down 50, left 50, right 50, forward 50, back 50   (cm)
    cw 90, ccw 90   (도)
    flip l|r|f|b, speed 50, speed?
    end          종료 (빈 줄이나 Ctrl+C도 종료)

원본: Ryze Tello Python3 Control Demo (http://www.ryzerobotics.com/, 2018)
"""
import socket
import threading

TELLO_ADDRESS = ("192.168.10.1", 8889)  # 드론의 명령 포트
LOCAL_ADDRESS = ("", 9000)              # 응답("ok", "error" 등)을 받을 내 포트


def receive_loop(sock):
    """드론이 보내는 응답을 계속 출력한다. 소켓이 닫히면 끝난다."""
    while True:
        try:
            data, _ = sock.recvfrom(1518)
        except OSError:
            print("\nExit . . .\n")
            break
        print(data.decode("utf-8", errors="replace"))


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(LOCAL_ADDRESS)

    print("\r\n\r\nTello Python3 Demo.\r\n")
    print("Tello: command takeoff land flip forward back left right \r\n       up down cw ccw speed speed?\r\n")
    print("end -- quit demo.\r\n")

    # 응답은 따로 스레드에서 받는다 (입력을 기다리는 동안에도 출력되게)
    threading.Thread(target=receive_loop, args=(sock,), daemon=True).start()

    try:
        while True:
            msg = input("").strip()
            if not msg or msg == "end":
                print("...")
                break
            sock.sendto(msg.encode("utf-8"), TELLO_ADDRESS)
    except (KeyboardInterrupt, EOFError):
        print("\n . . .\n")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
