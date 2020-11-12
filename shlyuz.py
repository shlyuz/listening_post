#!/usr/bin/env python3

import asyncio
import ast
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

        # Crypto values
        self.initial_private_key = args['config']['crypto']['private_key']
        self.initial_public_key = self.initial_private_key.public_key
        self.initial_rc6_key = args['config']['crypto']['sym_key']
        self.xor_key = ast.literal_eval(args['config']['crypto']['xor_key'])
        self.ts_pubkey = args['config']['crypto']['ts_pk']

        # Implant Runtime Vars
        self.implants = {}
        self.implant_count = len(self.implants)

        # Transport Runtime Vars
        self.transports = {}
        self.transport_count = len(self.transports)

    def start(self):
        """
        Listening Post Startup and runner

        :return:
        """

        # Give ourselves a listening_post
        self.listening_post = listening_post.Listener(self)

        lp_thread = Thread(target=self.listening_post.start_lp, args=(self,))
        lp_thread.start()
        self.logging.log("Started LP")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='lp')
    parser.add_argument("-a", "--address", required=False, default="127.0.0.1", help="Address to connect to")
    parser.add_argument("-p", "--port", required=False, default=8081, help="Port to connect to")
    parser.add_argument("-d", "--debug", required=False, default=False, action="store_true",
                        help="Enable debug logging")
    parser.add_argument("-c", "--config", required=False, default="config/config.conf",
                        help="Path to configuration file")

    # parse the args
    args = vars(parser.parse_args())

    lp = Listener(args)
    lp.start()
