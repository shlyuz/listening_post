import base64
import asyncio
from lib import networking


class Listener(object):
    def __init__(self, args):
        self.info = {"name": "lp",
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
            listener.logging.log(f"Starting management socket on {listener.addr}:{listener.port}",
                                        source=f"{listener.listening_post.info['name']}")
            listener.management_socket = networking.connect_to_listener_socket(listener.addr,
                                                                                              listener.port)
        # TODO: Too broad of an execption
        except Exception as e:
            listener.logging.log(f"Critical error when starting Listening Post management Socket: {e}",
                                        level="critical", source=f"{listener.listening_post.info['name']}")
            exit()

    def start_management_interaction(self):
        # TODO: Loop here until we get a vaild startup init from the Teamserver
        try:
            networking.recv_management_frame(listener.listening_post.management_socket)
        except Exception as e:
            listener.logging.log(f"Invalid attempt to connect on management interface",
                                        source=f"{listener.listening_post.info['name']}")

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

            # TODO: Create management socket
            self.setup_management_socket()

            # TODO: Receive management socket for init from teamserver

            # TODO: Send listening post manifest to teamserver

            # TODO: Await commands from teamserver and perform main loop

        except Exception as e:
            listener.logging.log(f"Critical error when starting teamserver api server: {e}", level="critical",
                                        source=f"{listener.listening_post.info['name']}")
            exit()
