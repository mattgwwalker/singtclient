from pathlib import Path
import json

from twisted.internet import reactor
from twisted.internet.protocol import Protocol
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

from singtcommon import TCPPacketizer


class FileTransportClient(Protocol):
    def connectionMade(self):
        self._packetizer = TCPPacketizer(self.transport)


    def connectionLost(self, reason):
        print("Connection lost:", reason)
        
        
    def send_file(self, file_path, audio_id):
        # Open file for reading
        f = open(file_path, "rb")
        
        # Send initial message
        message = {
            "command": "receive_file",
            "audio_id": audio_id
        }
        message_json = json.dumps(message) 
        self._packetizer.write(message_json)

        # Send data
        index = 0
        chunk_size = 1000
        while True:
            # Read next chunk from file
            data = f.read(chunk_size)
            if len(data) == 0:
                # We've come to the end
                data = b"END"
                self._packetizer.write_bytes(data)
                break
            else:
                # Write the next chunk
                data = b"DATA" + data
                self._packetizer.write_bytes(data)

        # Close the connection
        self.transport.loseConnection()

    def open(self, audio_id):
        # Send initial message
        message = {
            "command": "receive_file",
            "audio_id": audio_id
        }
        message_json = json.dumps(message) 
        self._packetizer.write(message_json)

    def close(self):
        data = b"END"
        self._packetizer.write_bytes(data)

        # Close the connection
        self.transport.loseConnection()

    def write(self, data):
        data = b"DATA" + data
        self._packetizer.write_bytes(data)
    
