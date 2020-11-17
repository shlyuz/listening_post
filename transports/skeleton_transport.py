class Transport:
    def __init__(self):
        self.info = {"name": "skeleton",
                     "author": "Und3rf10w",
                     "desc": "Skeleton for building out transports",
                     "version": "0.01-dev"
                     }
        # Should always be initialized here
        self.config = {}
        # You REALLY SHOULD keep this in, so you can use the same logging engine
        self.logging = None

    def prep_transport(self, transport_config):
        # Here you take the transport configuration and make a configuration that you're going to use by populating
        #   self.config
        self.config = transport_config
        # You REALLY SHOULD keep this in, so you can use the same logging engine
        self.logging = transport_config['logging']
        self.logging.log(f"Transport prepared", level="debug", source=self.info.name)

    def send_data(self, data):
        # Here you're going to take cooked data and send it over whatever your transport mechanism is. Return 0 in
        #   case of success.
        # Your transport should not transmit NOOPs unless its used for a connectivity check
        print(data)
        return 0

    def recv_data(self):
        # Here you're going to return the cooked data you retrieved from your transport.
        # Your transport should NOT receive NOOPs unless its used for a connectivity check.
        return "ayyylmao"

    # You can implement literally any other functions you want here, as long as you do not rely on them being called outside
    #   of this module. The only three "exported" functions of a transport are transport.prep_transport,
    #   transport.send_data, and transport.recv_data
