import socket
import struct
import ast
from time import sleep

from lib import frame_orchestrator
from lib import transmit


def reset_socket(listener):
    listener.management_socket = connect_to_listener_socket(listener.addr, listener.port)


def connect_to_listener_socket(addr, port):
    """
    Establish a connection to our management socket
    :param addr:
    :param port:
    :return:
    """
    management_channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    management_channel.connect((addr, int(port)))
    return management_channel


def send_management_frame(listener, data):
    reset_socket(listener)
    slen = struct.pack('<I', len(data))
    listener.logging.log(f"Encoded data: {data}", level="debug", source="lib.networking.send")
    try:
        listener.management_socket.send(slen + data)
    except BrokenPipeError:
        sleep(60)
        listener.management_socket.send(slen + data)


def recv_management_frame(listener):
    try:
        try:
            frame_size = listener.management_socket.recv(4)
        except ConnectionResetError:
            listener.management_socket.close()
            listener.management_socket = connect_to_listener_socket(listener.addr, listener.port)
            frame_size = listener.management_socket.recv(4)
        except Exception as e:
            listener.logging.log(f"Critical [{type(e).__name__}] when starting teamserver api server: {e}",
                                 level="critical", source="lib.networking.recv")

        slen = struct.unpack('<I', frame_size)[0]
        listener.logging.log(f"frame_len: {slen}", level="debug", source="lib.networking.recv")
        frame = listener.management_socket.recv(slen)
        listener.logging.log(f"raw_frame: {frame}", level="debug", source="lib.networking.recv")
        reset_socket(listener)
        if frame[:len(ast.literal_eval(listener.config.config['lp']['init_signature']))] == ast.literal_eval(listener.config.config['lp']['init_signature']):
            frame = frame[len(ast.literal_eval(listener.config.config['lp']['init_signature'])):]
            uncooked_frame = ast.literal_eval(transmit.uncook_sealed_frame(listener, frame).decode('utf-8'))
        else:
            uncooked_frame = ast.literal_eval(transmit.uncook_transmit_frame(listener, frame).decode('utf-8'))
        ack_frame = frame_orchestrator.determine_destination(uncooked_frame, listener)
        return ack_frame
    except ConnectionResetError:
        listener.management_socket.close()
        listener.management_socket = connect_to_listener_socket(listener.addr, listener.port)
        frame_size = listener.management_socket.recv(4)
    except ValueError as e:
        raise ConnectionResetError
    except Exception as e:
        listener.logging.log(f"Critical [{type(e).__name__}] when starting teamserver api server: {e}",
                             level="critical", source="lib.networking.recv")
