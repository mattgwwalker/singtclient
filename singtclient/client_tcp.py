import json
import struct

from twisted.internet import reactor
from twisted.internet.protocol import Protocol
from twisted.logger import Logger

from singtcommon import TCPPacketizer

# Start a logger with a namespace for a particular subsystem of our application.
log = Logger("client_tcp")


class TCPClient(Protocol):
    def __init__(self, name):
        super()
        self._name = name
        self._tcp_packetizer = None

        self._commands = {}
        self._register_commands()

        print("Client started")

        
    def register_command(self, command, function):
        self._commands[command] = function

        
    def _register_commands(self):
        self.register_command("download", self._command_download)

        
    def connectionMade(self):
        self._tcp_packetizer = TCPPacketizer(self.transport)
        data = {
            "command":"announce",
            "username": self._name
        }
        msg = json.dumps(data)
        self._tcp_packetizer.write(msg)

        
    def connectionLost(self, reason):
        print("Connection lost:", reason)

        
    def dataReceived(self, data):
        packets = self._tcp_packetizer.decode(data)

        for packet in packets:
            #print("packet decoded:", packet)
            self.process(packet)


    def process(self, packet):
        print("Processing packet: ",packet)

        try:
            decoded_packet = json.loads(packet)
        except JSONDecodeError as e:
            raise Exception(f"Failed to decode packet ({packet}) as JSON: "+str(e))

        try:
            command = decoded_packet["command"]
        except KeyError:
            raise Exception(f"Packet ({packet}) did not contain a command")

        try:
            function = self._commands[command]
        except KeyError:
            raise Exception(f"No function was registered against the command '{command}'")

        try:
            function(decoded_packet)
        except Exception as e:
            raise Exception(f"Failed during executing of the function for command '{command}': "+str(e))

        
    def _command_download(self, data):
        audio_id = data["audio_id"]
        partial_url = data["partial_url"]
        ip_address = self.transport.getPeer().host
        print("ip_address:", ip_address)
        url = "http://" + ip_address + partial_url
        print("Downloading file from "+url)
        
