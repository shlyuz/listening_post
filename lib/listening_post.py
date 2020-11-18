import base64
import asyncio
import ast  # debug
from time import sleep
from threading import Thread

from lib import networking
from lib import core
from lib import implants


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
            listener.logging.log(f"Critical [{type(e).__name__}] when starting Listening Post management Socket: {e}",
                                 level="critical", source=f"{listener.listening_post.info['name']}")
            exit()

    def initialize(self):
        try:
            initialization_frame = core.send_initialization(listener)
            networking.send_management_frame(listener, initialization_frame)
            manifest_frame = networking.recv_management_frame(listener)
            networking.send_management_frame(listener, manifest_frame)
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
        manifest = {"implants": listener.implants, "component_id": listener.component_id}
        return manifest

    def main(self):
        # TODO: Loop this, thread this
        #  * Do a get command
        #   * if fails, sleep
        #   * else, send command to implant and relay reply on next timer
        listener.logging.log(f"Starting main execution",
                             source=f"{listener.listening_post.info['name']}.main",
                             level="debug")
        while True:
            listener.logging.log(f"Requesting commands from teamsever",
                                 source=f"{listener.listening_post.info['name']}.main",
                                 level="debug")
            if len(listener.implants) > 0:
                # Only request commands if we have implants to request them for
                command_request_frame = core.request_command(listener)
                networking.send_management_frame(listener, command_request_frame)
                command_reply_frame = networking.recv_management_frame(listener)
            #     # TODO: Routing to implants should happen in core.
            listener.logging.log(f"Pausing cmd_receipt thread for {listener.config.config['lp']['main_job_timer']} seconds",
                                 source=f"{listener.listening_post.info['name']}.main",
                                 level="debug")
            sleep(int(listener.config.config['lp']['main_job_timer']))
            pass

    def setup_transports(self):
        try:
            for section in listener.config.config.sections():
                if section.startswith("transport_"):
                    transport_name = section.replace("transport_", "")
                    transport_config = dict(listener.config.config[section].items())
                    implants.import_transport(listener, transport_name, transport_config)
        except Exception as e:
            listener.logging.log(f"Critical [{type(e).__name__}] when initalizing transport: {e}",
                                 level="critical", source=f"{listener.listening_post.info['name']}")

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
            transport_thread = Thread(target=self.setup_transports(), daemon=False)
            transport_thread.start()
            # self.setup_transports()

            # TODO: Request Manifests from Implants

            # TODO: Update internal values with manifests from Implants

            # TODO: Prepare Listening Post Manifest
            listener.manifest = self.prepare_manifests()

            self.setup_management_socket()

            self.initialize()

            self.main()

        except Exception as e:
            listener.logging.log(f"Critical [{type(e).__name__}] when starting listener api server: {e}",
                                 level="critical", source=f"{listener.listening_post.info['name']}")
            exit()
