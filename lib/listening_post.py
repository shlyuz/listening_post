import base64
import asyncio
from lib import networking


class Listener(object):
    def __init__(self, args):
        self.info = {"name": "lp",
                     "author": "Und3rf10w"
                     }
        super(Listener, self).__init__()

    def setup_management_socket(self):
        """
        Sets up the management socket for our listener to use
        :return:
        """
        try:
            listener.listening_post.management_socket = networking.create_mangement_socket(listener.addr, listener.port)
        except Exception as e:
            listener.listening_post.log(f"Critical error when starting Listening Post management Socket",
                                        level="critical", source=f"{listener.listening_post.info['name']}")
            exit()


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
            # Create our management socket
            self.setup_management_socket(listener)




        except Exception as e:
            listener.listening_post.log(f"Critical error when starting teamserver api server", level="critical",
                                        source=f"{listener.listening_post.info['name']}")
            exit()
