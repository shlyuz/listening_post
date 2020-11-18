import struct
import asyncio
import ast
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
        self.logging = None

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
                transport_frame = {"frame": frame, "type": "init"}
            else:
                # TODO: Attach the component's id here
                transport_frame = {"frame": frame, "type": "std"}
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
        loop = asyncio.new_event_loop()
        t = Thread
        self.config = transport_config
        self.logging = transport_config['logging']
        self.bind_addr = self.config['bind_addr']
        self.bind_port = int(self.config['bind_port'])
        t = Thread(target=self.start_background_loop, args=(loop,), daemon=False)
        loop.create_task(asyncio.start_server(lambda reader, writer: self.handle_client(reader=reader, writer=writer, component=self.component),
                                              host=self.config['bind_addr'],
                                              port=self.config['bind_port'],))
        t.start()

    def send_data(self, data):
        pass

    def recv_data(self):
        pass

    def set_implant_id(self, implant_id):
        self.implant_id = implant_id
