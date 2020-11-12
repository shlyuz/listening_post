import base64
import asyncio
import ast  # debug

from lib import networking
from lib import core


class Listener(object):
    def __init__(self, args):
        self.info = {"name": "listening_post",
                     "author": "Und3rf10w"
                     }
        super(Listener, self).__init__()
        self.status = "INITIALIZING"

    def setup_management_socket(self):
        """
        Sets up the management socket for our listener to use
        :return:
        """
        try:
            listener.logging.log(f"Connected to management socket on {listener.addr}:{listener.port}",
                                 source=f"{listener.listening_post.info['name']}")
            listener.management_socket = networking.connect_to_listener_socket(listener.addr,
                                                                               listener.port)
        # TODO: Too broad of an execption
        except Exception as e:
            listener.logging.log(f"Critical error when starting Listening Post management Socket: {e}",
                                 level="critical", source=f"{listener.listening_post.info['name']}")
            exit()

    def initialize(self, manifest):
        try:
            initialization_frame = core.send_initialization(listener)
            networking.send_management_frame(listener,
                                             str(initialization_frame).encode('utf-8)'))  # Debug, this will be cooked
            manifest_frame = networking.recv_management_frame(listener)
            networking.send_management_frame(listener, str(manifest_frame).encode('utf-8'))
            ack_frame = networking.recv_management_frame(listener)
            if listener.listening_post.status == "READY":
                listener.logging.log(f"LP Ready", source="lib.core")
            else:
                raise RuntimeError
        # TODO: catch other exceptions
        except Exception as e:
            listener.logging.log(f"Critical [{type(e).__name__}] when initializing listener api server: {e}",
                                 level="critical", source=f"{listener.listening_post.info['name']}.initialize")
            exit()

    def prepare_manifests(self):
        # TODO:
        manifest = {"implants": [{"implant_id": "DEADB33F",
                                  "implant_os": "win",
                                  "implant_user": "user"
                                  }],
                    "component_id": listener.component_id
                    }
        return manifest

    def start_lp(self, *args):
        """
        Start our LP, request manifests from Implants, store the manifests, update internal variables, prepare manifest
        for teamserver retrieval, loop to await teamserver interaction

        :param args:
        :return:
        """
        global listener

        listener = args[0]
        try:
            # TODO: Setup Listener transport(s)

            # TODO: Request Manifests from Implants

            # TODO: Update internal values with manifests from Implants

            # TODO: Prepare Listening Post Manifest
            listener.manifest = self.prepare_manifests()

            # TODO: Create management socket
            self.setup_management_socket()

            # TODO: Send management socket for init from teamserver
            self.initialize(listener.manifest)

            # TODO: Await commands from teamserver and perform main loop

        except Exception as e:
            listener.logging.log(f"Critical [{type(e).__name__}] when starting listener api server: {e}",
                                 level="critical", source=f"{listener.listening_post.info['name']}")
            exit()
