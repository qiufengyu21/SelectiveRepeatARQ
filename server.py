from struct import pack, unpack, calcsize
from array import array
import socket
import random
import sys


def pack_ack(seq):
    header = pack("I", seq)
    return header + b'\x00\x00\xAA\xAA'


def unpack_frame(frame):
    data = unpack("IHH", frame[:calcsize('IHH')])
    return data[0], data[1], frame[calcsize('IHH'):]


def calc_checksum(data):
    if len(data) % 2:
        data += b'\x00'
    s = sum(array('H',data))
    s = (s & 0xffff) + (s >> 16)
    s += (s >> 16)
    return socket.ntohs(~s & 0xffff)


def main(port, filename, p):
    try:
        p = float(p)
        sock = socket.socket(type=socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', int(port)))
        i = 0
        expected_seq = 0
        with open("{}{}".format(filename,i), 'wb') as fout:
            buffer = []
            EOF = False
            while not EOF:
                frame, addr = sock.recvfrom(4096)
                seq, checksum, data = unpack_frame(frame)
                r = random.random()
                if r < p:
                    print("Packet loss, sequence number = {}".format(seq))
                    continue
                if checksum != calc_checksum(data) or seq < expected_seq:
                    continue
                else:
                    #print("Packet accepted, sequence number = {}".format(seq))
                    ack = pack_ack(seq)
                    sock.sendto(ack, addr)
                    #print("expceted = {}, seq = {}".format(expected_seq, seq))
                    if seq == expected_seq:
                        if data == b'':
                            EOF = True
                            break
                        #print("write to file")
                        fout.write(data)
                        expected_seq += 1
                        while len(buffer):
                            if buffer[0][0] == expected_seq:
                                data = buffer.pop(0)[1]
                                fout.write(data)
                                if data == b'':
                                    EOF = True
                                    break
                                expected_seq += 1
                            else:
                                break                                                                 
                    else:
                        buffer.insert(0, (seq, data))
                        buffer.sort(key=lambda x:x[0])
                        #print(buffer[0][0])                       
    except KeyboardInterrupt as e:
        print(e)
        return

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
