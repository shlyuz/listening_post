import struct
import asyncio
import ast
import socket
import random
import string
from threading import Thread

class Transport:
    def __init__(self, component):
        self.info = {"name": "bind_tcp_socket",
                     "author": "Und3rf10w",
                     "desc": "Bind a tcp socket and use that as a transport, inverse of rev_tcp_socket",
                     "version": "0.01-dev"
                     }
        # Should always be initialized here
        self.config = {}
        self.bind_addr = "127.0.0.1"
        self.bind_port = 8084
        self.component = component
        self.socket = None
        self.logging = None
        self.implant_id = None
        self.transport_id = None
        self.async_loop = None
        self.data_queue = []

    async def handle_client(self, reader, writer, component):
        self.logging.log(f"Transport Socket Conn: {reader._transport.get_extra_info('peername')}", level="debug",
                         source=f"transport.{self.info['name']}")
        try:
            request_size = await reader.read(4)
            if request_size == b'':
                raise ConnectionResetError
            slen = struct.unpack('<I', request_size)[0]
            frame = await reader.read(slen)
            if frame[:len(ast.literal_eval(component.config.config['lp']['init_signature']))] == ast.literal_eval(component.config.config['lp']['init_signature']):
                frame = frame[len(ast.literal_eval(component.config.config['lp']['init_signature'])):]
                transport_frame = {"frame": frame, "type": "init", "transport_id": self.transport_id}
            else:
                # TODO: Attach the component's id here
                transport_frame = {"frame": frame, "type": "std", "transport_id": self.transport_id}
            component.transport_frame_queue.append(transport_frame)
            reply_frame = await component.process_transport_frame()
            response = reply_frame
            self.logging.log(f"SEND: {response}", level="debug", source=f"transport.{self.info['name']}")
            rlen = struct.pack('<I', len(str(response).encode('utf-8')))
            # Send the response
            writer.write(rlen + response)
            await writer.drain()
        except ConnectionResetError:
            writer.close()
        except struct.error:
            self.logging.log(f"Invalid data", level="debug", source=f"transport.{self.info['name']}")
        except UnboundLocalError:
            self.logging.log(f"Invalid frame received", level="error", source=f"transport.{self.info['name']}")
            self.logging.log(f"Invalid frame {frame}", level="debug", source=f"transport.{self.info['name']}")
        except Exception as e:
            self.logging.log(f"Encountered [{type(e).__name__}] {e}", level="error",
                             source=f"transport.{self.info['name']}")
        writer.close()

    def start_background_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def prep_transport(self, transport_config):
        self.async_loop = asyncio.new_event_loop()
        t = Thread
        self.config = transport_config
        self.logging = transport_config['logging']
        self.bind_addr = self.config['bind_addr']
        self.bind_port = int(self.config['bind_port'])
        self.transport_id = self.config['transport_id']
        t = Thread(target=self.start_background_loop, args=(self.async_loop,), daemon=False)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.bind((self.config['bind_addr'], int(self.config['bind_port'])))
        except OSError:
            self.logging.log(f"Transport binding failed", level="critical", source=self.info['name'])
            from time import sleep
            sleep(10)
            self.socket.bind((self.config['bind_addr'], int(self.config['bind_port'])))
        self.socket.listen()
        self.async_loop.create_task(asyncio.start_server(
            lambda reader, writer: self.handle_client(reader=reader, writer=writer, component=self.component), sock=self.socket))
        t.start()
        self.logging.log(f"Transport prepared", level="debug", source=self.info['name'])

    async def send_coro(self, data):
        loop = self.async_loop

        # Create a pair of connected sockets
        rsock, wsock = socket.socketpair()

        # Register the open socket to wait for data.
        reader, writer = await asyncio.open_connection(sock=rsock)

        # Send our data
        data_len = struct.pack('<I', len(str(data).encode('utf-8')))
        loop.call_soon(wsock.send, data_len + str(data).encode('utf-8'))

        writer.close()

    def send_data(self, data):
        self.data_queue.append(data)
        # asyncio.run_coroutine_threadsafe(self.send_coro(data), self.async_loop)
        # # try:
        # #     self.logging.log(f"SEND: {data}", level="debug", source=f"transport.{self.info['name']}")
        # #     rlen = struct.pack('<I', len(str(data).encode('utf-8')))
        # #     # Send the response
        # #     self.writer.write(rlen + data)
        # #     await self.writer.drain()
        # # except ConnectionResetError:
        # #     self.writer.close()
        # # except struct.error:
        # #     self.logging.log(f"Invalid data", level="debug", source=f"transport.{self.info['name']}")
        # # except UnboundLocalError:
        # #     self.logging.log(f"Invalid frame received", level="error", source=f"transport.{self.info['name']}")
        # #     self.logging.log(f"Invalid frame {frame}", level="debug", source=f"transport.{self.info['name']}")
        # # except Exception as e:
        # #     self.logging.log(f"Encountered [{type(e).__name__}] {e}", level="error",
        # #                      source=f"transport.{self.info['name']}")
        # # self.writer.close()

    def recv_data(self):
        pass

    def set_implant_id(self, implant_id):
        self.implant_id = implant_id
