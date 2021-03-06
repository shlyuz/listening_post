import pickle
import binascii
import ast
import secrets
import nacl.utils

import lib.crypto
import lib.crypto.rc6
import lib.crypto.hex_encoding
import lib.crypto.xor
import lib.crypto.asymmetric
import lib.implants


def find_implant_pubkey(listener, implant_id):
    implant_index = lib.implants._get_implant_index(listener, implant_id)
    # TODO: Rotate keys here
    return listener.implants[implant_index]['ipk'], listener.implants[implant_index]['priv_key']


def uncook_transmit_frame(listener, frame, target_component_id="teamserver"):
    """

    :param listener:
    :param frame:
    :param target_component_id: OPTIONAL The id of the component who's encryption key to use
    :return:
    """
    if target_component_id == "teamserver":
        # TODO: Rotate keys here
        target_pubkey = listener.current_ts_pubkey
        my_privkey = listener.current_private_key
    else:
        target_pubkey, my_privkey = find_implant_pubkey(listener, target_component_id)
        target_pubkey = lib.crypto.asymmetric.public_key_from_bytes(str(target_pubkey))
        my_privkey = lib.crypto.asymmetric.private_key_from_bytes(str(my_privkey))

    # Asymmetric Encryption Routine
    frame_box = lib.crypto.asymmetric.prepare_box(my_privkey, target_pubkey)
    transmit_frame = lib.crypto.asymmetric.decrypt(frame_box, frame)

    # Decoding Routine
    rc6_key = binascii.unhexlify(lib.crypto.hex_encoding.decode_hex(transmit_frame[0:44])).decode("utf-8")
    listener.logging.log(f"rc6 key: {rc6_key}", level="debug", source="lib.transmit")
    unxord_frame = lib.crypto.xor.single_byte_xor(transmit_frame,
                                                  listener.xor_key)
    del transmit_frame
    unenc_frame = lib.crypto.hex_encoding.decode_hex(unxord_frame)
    del unxord_frame
    unsorted_recv_frame = pickle.loads(binascii.unhexlify(unenc_frame[44:]))
    del unenc_frame

    data_list = []
    sorted_frames = sorted(unsorted_recv_frame, key=lambda i: i['frame_id'])
    del unsorted_recv_frame
    for data_index in range(len(sorted_frames)):
        data_list.append(sorted_frames[data_index]['data'])

    # Symmetric decryption routine
    decrypted_data = lib.crypto.rc6.decrypt(rc6_key, data_list)
    listener.logging.log(f"Decrypted data: {decrypted_data}", level="debug", source="lib.transmit")

    return decrypted_data


def cook_transmit_frame(listener, data, target_component_id="teamserver"):
    """

    :param listener:
    :param data: encoded/encrypted data ready to transmit
    :param target_component_id: OPTIONAL The id of the component who's encryption key to use
    :return:
    """
    # Symmetric Encryption Routine
    if target_component_id == "teamserver":
        target_pubkey = listener.current_ts_pubkey
        my_privkey = listener.current_private_key
    else:
        target_pubkey, my_privkey = find_implant_pubkey(listener, target_component_id)
        target_pubkey = lib.crypto.asymmetric.public_key_from_bytes(str(target_pubkey))
        my_privkey = lib.crypto.asymmetric.private_key_from_bytes(str(my_privkey))
        # TODO: Extract the private key for the listener here
    rc6_key = secrets.token_urlsafe(16)
    listener.logging.log(f"rc6 key: {rc6_key}", level="debug", source="lib.transmit")
    transmit_data = lib.crypto.rc6.encrypt(rc6_key, str(data).encode('utf-8'))

    encrypted_frames = []
    for chunk_index in range(len(transmit_data)):
        frame_chunk = {"frame_id": chunk_index, "data": transmit_data[chunk_index],
                       "chunk_len": len(transmit_data)}
        encrypted_frames.append(frame_chunk)

    # Encoding routine
    hex_frames = binascii.hexlify(pickle.dumps(encrypted_frames))
    hex_frames = lib.crypto.hex_encoding.encode_hex(hex_frames)
    enveloped_frames = lib.crypto.xor.single_byte_xor(hex_frames,
                                                      listener.xor_key)

    enveloped_frames = lib.crypto.hex_encoding.encode_hex(binascii.hexlify(rc6_key.encode("utf-8"))) + enveloped_frames
    listener.logging.log(f"Unenveloped data: {enveloped_frames}", level="debug", source="lib.transmit")

    # Asymmetric Encryption
    frame_box = lib.crypto.asymmetric.prepare_box(my_privkey, target_pubkey)
    transmit_frames = lib.crypto.asymmetric.encrypt(frame_box, enveloped_frames)

    listener.logging.log(f"Enveloped data: {transmit_frames}", level="debug", source="lib.transmit")
    return transmit_frames


def cook_sealed_frame(listener, data):
    """
    Uses a nacl.public.SealedBox() to authenticate with the target component

    :param listener:
    :param data:
    :return:
    """
    rc6_key = secrets.token_urlsafe(16)
    listener.logging.log(f"rc6 key: {rc6_key}", level="debug", source="lib.transmit")
    transmit_data = lib.crypto.rc6.encrypt(rc6_key, str(data).encode('utf-8'))

    encrypted_frames = []
    for chunk_index in range(len(transmit_data)):
        frame_chunk = {"frame_id": chunk_index, "data": transmit_data[chunk_index],
                       "chunk_len": len(transmit_data)}
        encrypted_frames.append(frame_chunk)

    # Encoding routine
    hex_frames = binascii.hexlify(pickle.dumps(encrypted_frames))
    hex_frames = lib.crypto.hex_encoding.encode_hex(hex_frames)
    enveloped_frames = lib.crypto.xor.single_byte_xor(hex_frames,
                                                      listener.xor_key)

    enveloped_frames = lib.crypto.hex_encoding.encode_hex(binascii.hexlify(rc6_key.encode("utf-8"))) + enveloped_frames
    listener.logging.log(f"Unenveloped init data: {enveloped_frames}", level="debug", source="lib.transmit")

    # Asymmetric SealedBox Encryption
    ts_pubkey = listener.current_ts_pubkey
    frame_box = lib.crypto.asymmetric.prepare_sealed_box(ts_pubkey)
    transmit_frames = lib.crypto.asymmetric.encrypt(frame_box, enveloped_frames)

    # Prepend the transmit frame with an init signature
    init_signature = ast.literal_eval(listener.config.config['lp']['init_signature'])
    transmit_frames = init_signature + transmit_frames

    listener.logging.log(f"Enveloped init data: {transmit_frames}", level="debug", source="lib.transmit")
    return transmit_frames


def uncook_sealed_frame(listener, frame):
    """
    Uses a nacl.public.SealedBox() to receive initialization ack

    :param listener:
    :param frame:
    :return:
    """

    frame_box = lib.crypto.asymmetric.prepare_sealed_box(listener.initial_private_key)
    transmit_frame = lib.crypto.asymmetric.decrypt(frame_box, frame)

    # Decoding Routine

    rc6_key = binascii.unhexlify(lib.crypto.hex_encoding.decode_hex(transmit_frame[0:44])).decode("utf-8")
    listener.logging.log(f"rc6 key: {rc6_key}", level="debug", source="lib.transmit")
    unxord_frame = lib.crypto.xor.single_byte_xor(transmit_frame,
                                                  listener.xor_key)

    del transmit_frame
    unenc_frame = lib.crypto.hex_encoding.decode_hex(unxord_frame)
    del unxord_frame
    unsorted_recv_frame = pickle.loads(binascii.unhexlify(unenc_frame[44:]))
    del unenc_frame

    data_list = []
    sorted_frames = sorted(unsorted_recv_frame, key=lambda i: i['frame_id'])
    del unsorted_recv_frame
    for data_index in range(len(sorted_frames)):
        data_list.append(sorted_frames[data_index]['data'])

    # Symmetric decryption routine
    decrypted_data = lib.crypto.rc6.decrypt(rc6_key, data_list)
    listener.logging.log(f"Decrypted data: {decrypted_data}", level="debug", source="lib.transmit")

    return decrypted_data
