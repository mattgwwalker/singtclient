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
        print("Sending initial command message")
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
            
        

file_path = Path("/Users/matthew/Desktop/VirtualChoir/Sounds/psallite.opus")
audio_id = 1
        
def gotProtocol(p):
    p.send_file(file_path, audio_id)

port = 2000
point = TCP4ClientEndpoint(reactor, "127.0.0.1", port)
d = connectProtocol(point, FileTransportClient())
d.addCallback(gotProtocol)

def on_error(error):
    print("Error:", error)
d.addErrback(on_error)

reactor.run()
