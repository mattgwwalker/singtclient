from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.logger import Logger

from .client_tcp import TCPClient

# Start a logger with a namespace for a particular subsystem of our application.
log = Logger("command")

class Command:
    def __init__(self, context):
        self._context = context
    
    def connect(self, username, address, port=1234):
        log.info(f"Connecting to server '{address}' as '{username}'")

        # TCP
        reactor = self._context["reactor"]
        point = TCP4ClientEndpoint(reactor, address, port)
        client = TCPClient(username, self._context)
        d = connectProtocol(point, client)

        def on_error(error):
            log.warn("An error occurred while attempting to connect to server: "+str(error))
            return error
        d.addErrback(on_error)

        # TODO: This needs to be controlled and not part of this connection
        # UDP
        # 0 means any port, we don't care in this case
        udp_client_factory = self._context["udp_client_factory"]
        udp_client = udp_client_factory(address, 12345, self._context)
        reactor.listenUDP(0, udp_client)

        return d
