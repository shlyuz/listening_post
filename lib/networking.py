import socket
import struct


def create_mangement_socket(addr, port):
    """
    Creates our management socket to interact with the teamserver
    :param addr: The address to bind the management socket to
    :param port: The address to bind the management port to
    :return:
    """
    management_channel = {'sock': socket.create_connection((addr, int(port))), 'state': 1}
    return (management_channel['sock'])


def send_management_frame(sock, chunk):
    slen = struct.pack('<I', len(chunk))
    sock.sendall(slen + chunk)


def recv_management_frame(sock):
    try:
        chunk = sock.recv(4)
    except:
        return("")

    if len(chunk) > 4:
        return()

    slen = struct.unpack('<I', chunk)[0]
    chunk = sock.recv(slen)
    while len(chunk) < slen:
        chunk = chunk + sock.recv(slen - len(chunk))


def kill_management_socket(sock):
    sock.close()