from lib.crypto import asymmetric
from lib import instructions


def _get_implant_index(listener, implant_id):
    try:
        implant_index = next(index for (index, d) in enumerate(listener.implants) if d["implant_id"] == implant_id)
        return implant_index
    except StopIteration:
        listener.logging.log(f"{implant_id} not found!, attempted import for {implant_id}",
                             level="error", source="lib.implants")
        pass


def import_transport(listener, transport_name, transport_config):
    import_string = f"import transports.{transport_name} as transport"
    transport_config['logging'] = listener.logging
    exec(import_string, globals())
    try:
        implant_transport = transport.Transport(listener)
        listener.logging.log(f"Imported {transport_name}", level="debug", source="lib.implants")
        listener.transports.append(implant_transport)
        listener.transports[-1].prep_transport(transport_config)
    except ImportError:
        listener.logging.log(f"{transport_name} not found! Report this!",
                         level="error", source="lib.implants")
    except Exception as e:
        listener.logging.log(f"Critical [{type(e).__name__}] when initalizing transport: {e}",
                             level="critical", source=f"lib.implants")


def attach_transport_to_implant(listener, implant_id, transport_name, transport_config):
    # TODO: This won't really happen too often, since the transport likely needs to be prepared prior to the implant
    # TODO: fixme:
    import_string = f"import transports.{transport_name} as transport"
    transport_config['logging'] = listener.logging
    exec(import_string, globals())
    try:
        # Find the index of the implant
        implant_index = _get_implant_index(listener, implant_id)
        if implant_index:
            # I know this is fucking weird, but you find a better way to do this then
            implant_transport = transport.Transport()
            listener.implants[implant_index]['transport'] = implant_transport
            listener.logging.log(f"Imported {transport_name}, module for implant {implant_id}",
                                 level="debug", source="lib.implants")
            listener.implants[implant_index]['transport'].prep_transport(transport_config)
    except ImportError:
        listener.logging.log(f"{transport_name} not found!, attempted import for {implant_id}",
                             level="error", source="lib.implants")


def prep_transport_for_implant_manifest(listener, transport_name, transport_config):
    import_string = f"import transports.{transport_name} as transport"
    transport_config['logging'] = listener.logging
    try:
        # Do a retrieval of the transport's method to signal for a manifest
        exec(f"import transports.{transport_name} as transport")
        implant_transport = transport.Transport()
        implant_transport.prep_transport(transport_config)
        listener.transports.append(implant_transport)
    except ImportError:
        listener.logging.log(f"{transport_name} not found!, attempted import for manifest retrieval",
                             level="error", source="lib.implants")


def relay_cmd_to_implant(listener, implant_id, cmd):
    # TODO: Cook the command
    try:
        implant_index = _get_implant_index(listener, implant_id)
        if implant_index:
            listener.implants[implant_index]['transport_handle'].send_data(cmd)
    except Exception as e:
        listener.logging.log(f"Critical [{type(e).__name__}] when relaying command to implant {implant_id}: {e}",
                             level="critical", source=f"lib.implants")


def retrieve_output_from_implant(listener, implant_id):
    # TODO: uncook data
    try:
        implant_index = _get_implant_index(listener, implant_id)
        if implant_index:
            listener.implants[implant_index]['transport_handle'].recv_data()
    except Exception as e:
        listener.logging.log(f"Critical [{type(e).__name__}] when retrieving data from implant {implant_id}: {e}",
                             level="critical", source=f"lib.implants")


def initialize_implant(frame, listener):
    # TODO: Check if implant already exists in manifest
    implant_manifest = frame['args'][0]['manifest']
    implant_manifest['ipk'] = frame['args'][1]['ipk']
    # TODO: Rotate this key
    implant_manifest['lpk'] = listener.current_public_key._public_key
    implant_manifest['priv_key'] = listener.current_private_key._private_key
    implant_manifest['lp_id'] = listener.component_id
    implant_manifest['transport_id'] = frame['transport_id']
    listener.implants.append(implant_manifest)
    data = {'component_id': listener.component_id, "cmd": "ipi",
            "args": [{'lpk': implant_manifest['lpk']}], "txid": frame['txid']}
    instruction_frame = instructions.create_instruction_frame(data)
    reply_frame = instruction_frame
    return reply_frame


def initalize_existing_implant(frame, listener):
    # TODO: Implement me
    return None