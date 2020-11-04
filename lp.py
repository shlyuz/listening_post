#!/usr/bin/env python3

import asyncio
import argparse
from threading import Thread
from lib import logging
from lib import listening_post


class Listener(object):
    def __init__(self, args):
        """
        Initialized LP

        :param args: arguments received via main argument parser
        """

        super(Listener, self).__init__()

        # Runtime Variables
        self.logging = logging.Logging(args['debug'])
        self.logging.log("Starting LP", source="lp_init")
        self.addr = args['address']
        self.port = args['port']
        self.config = args['config']

        # Implant Runtime Vars
        self.implants = {}
        self.implant_count = len(self.implants)
        self.current_implant = None

        # Transport Runtime Vars
        self.transports = {}
        self.transport_count = len(self.transport_count)
        self.current_transport = None


    def start(self):
        """
        Listening Post Startup and runner

        :return:
        """

        self.lp = Listener(args)

        # Give ourselves a listening_post
        self.listening_post = listening_post.Listener(self)

        lp_thread = Thread(self.listening_post.start_lp, args=(self,))
        lp_thread = True
        lp_thread.start()
        self.logging.log("Started LP")



if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='lp')
    parser.add_argument("-a", "--address", required=False, default="0.0.0.0", help="Address to listen on")
    parser.add_argument("-p", "--port", required=False, default=8080, help="Port to bind to")
    parser.add_argument("-d", "--debug", required=False, default=False, action="store_true",
                        help="Enable debug logging")
    parser.add_argument("-c", "--config", required=False, default="config/config.conf",
                        help="Path to configuration file")

    # parse the args
    args = vars(parser.parse_args())

    lp = Listener(args)
    args['config'] = lp.config.config
    lp.start()