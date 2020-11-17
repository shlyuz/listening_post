def _get_implant_index(listener, implant_id):
    try:
        implant_index = (index for (index, d) in enumerate(listener.implants) if d["implant_id"] == implant_id)
        return implant_index
    except StopIteration:
        listener.logging.log(f"{implant_id} not found!, attempted import for {implant_id}",
                             level="error", source="lib.implants")
        pass


def import_transport_for_implant(listener, implant_id, transport_name, transport_config):
    import_string = f"import transports.{transport_name} as transport"
    exec(import_string)
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
