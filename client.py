from queue import Queue
from threading import Thread, Condition, Timer
from struct import pack, unpack
from array import array
import socket
import select
from sys import argv

nbuffered = 0
next_to_send = 0
expected_ack = 0
buffer = []
EOF = False
sock = socket.socket(type=socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 4321))
max_seq = 0
condition = Condition()
host = ''
port = 1234
filename = ''
N = 64
MSS = 500

class Frame():

    def __init__(self, seq, data):
        self._time_out = False
        checksum = self.calc_checksum(data)
        self._frame = self.pack_data(seq, checksum, data)
        self._seq = seq
        self._data = data

    def get_seq(self):
        return self._seq

    def get_frame(self):
        return self._frame

    def get_data(self):
        return self._data

    def calc_checksum(self, data):
        if len(data) % 2:
            data += b'\x00'
        s = sum(array('H', data))
        s = (s & 0xffff) + (s >> 16)
        s += (s >> 16)
        return socket.ntohs(~s & 0xffff)

    def pack_data(self, seq, checksum, data):
        header = pack("IH", seq, checksum)
        return header + b'\x55\x55' + data


def get_frames(filename, MSS):
    buffer = []
    seq = 0
    with open(filename, 'rb') as fin:
        while True:
            data = fin.read(MSS)
            frame = Frame(seq, data)
            buffer.append([False, frame])
            seq += 1
            if data:
                continue
            else:
                break
    return buffer

def get_acked_seq(ack):
    data = unpack("IHH", ack)
    return data[0]

def rdt_send():
    global nbuffered, next_to_send, expected_ack, buffer, EOF, sock, max_seq, condition, host, port, filename, N, MSS
    while True:
            nbuffered = 0
            window = list()
            for i in buffer:
                if not i[0]:
                    window.append(i[1].get_frame())
                    nbuffered += 1
                    if nbuffered == N:
                        break
            if len(window):
                for i in window:
                    sock.sendto(i, (host, port))
            else:
                EOF = True
                break
            with condition:
                condition.wait()
                for i in range(len(buffer)):
                    if not buffer[i][0]:
                        print("Time out, sequence number = {}".format(i))
                        break
            

def recv_ack():
    global sock, condition, nbuffered, expected_ack, host, port, buffer, EOF, next_to_send, max_seq
    while not EOF:
        rl, wl, el = select.select([sock,], [], [], 0.2)
        if sock in rl:
            frame, addr = sock.recvfrom(8)
            ack = get_acked_seq(frame)
            buffer[ack][0] = True
        else:
            
            with condition:
                condition.notify()
                    
                
                

def main():
    global host, port, filename, N, MSS, buffer, max_seq
    host, port, filename, N, MSS = argv[1:]
    port = int(port)
    N = int(N)
    MSS = int(MSS)
    buffer = get_frames(filename, MSS)
    max_seq = len(buffer)
    t1 = Thread(target=rdt_send)
    t2 = Thread(target=recv_ack)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    
def test_rdt_send(a, b, c, d, e):
    global host, port, filename, N, MSS, nbuffered, next_to_send, expected_ack, buffer, max_seq
    nbuffered = 0
    next_to_send = 0
    expected_ack = 0
    buffer = []
    max_seq = 0
    host, port, filename, N, MSS = a, int(b), c, int(d), int(e)
    buffer = get_frames(filename, MSS)
    max_seq = len(buffer)
    t1 = Thread(target=rdt_send)
    t2 = Thread(target=recv_ack)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

if __name__ == "__main__":
    main()
