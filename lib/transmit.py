import ast
import binascii
import pickle

import lib.crypto


def uncook_transmit_frame(listener, frame):
    """

    :param listener:
    :param frame:
    :return:
    """
    # frame = recv_managmeent_frame(listener.listener_management_socket)
    unxord_frame = lib.crypto.xor.single_byte_xor(frame,
                                                  ast.literal_eval(listener.config.config['crypto']['xor_key']))
    unenc_frame = lib.crypto.hex_encoding.decode_hex(unxord_frame)
    del unxord_frame
    unsorted_recv_frame = pickle.loads(binascii.unhexlify(unenc_frame))
    del unenc_frame

    data_list = []
    sorted_frames = sorted(unsorted_recv_frame, key=lambda i: i['frame_id'])
    del unsorted_recv_frame
    for data_index in range(len(sorted_frames)):
        data_list.append(sorted_frames[data_index]['data'])

    decrypted_data = lib.crypto.rc6.decrypt(listener.config.config['crypto']['rc6_key'], data_list)
    listener.logging.log(f"Decrypted data: {decrypted_data}", level="debug", source="lib.transmit")

    return decrypted_data


def cook_transmit_frame(listener, data):
    """

    :param listener:
    :param data: encoded/encrypted data ready to transmit
    :return:
    """
    # frame looks like {"id": 1, "frame_data": "somearbitrarydata", "chunks": 1}

    transmit_data = lib.crypto.rc6.encrypt(listener.config.config['crypto']['rc6_key'], data.encode('utf-8'))

    encrypted_frames = []
    for chunk_index in range(len(transmit_data)):
        frame_chunk = {"frame_id": chunk_index, "data": transmit_data[chunk_index],
                       "chunk_len": len(transmit_data)}
        encrypted_frames.append(frame_chunk)

    hex_frames = binascii.hexlify(pickle.dumps(encrypted_frames))
    hex_frames = lib.crypto.hex_encoding.encode_hex(hex_frames)
    transmit_frames = lib.crypto.xor.single_byte_xor(hex_frames,
                                                     ast.literal_eval(listener.config.config['crypto']['xor_key']))
    listener.logging.log(f"Encoded data: {transmit_frames}", level="debug", source="lib.transmit")
    return transmit_frames
    # send_management_frame(listener.listener_management_socket, transmit_frames)