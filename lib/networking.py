import socket
import struct


def create_mangement_socket(addr, port):
    """
    Creates our management socket to interact with the teamserver
    :param addr:
    :param port:
    :return:
    """
    management_channel = {}
    management_channel['sock'] = socket.create_connection((addr, int(port)))
    management_channel['state'] = 1
    return (management_channel['sock'])


