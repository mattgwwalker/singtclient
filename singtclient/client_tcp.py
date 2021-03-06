import json
import struct

from twisted.internet.protocol import Protocol
from twisted.web.client import HTTPDownloader
from twisted.web.client import URI

from singtcommon import TCPPacketizer

from .client_file import FileTransportClient
from .recording_mode import RecordingMode

# Start a logger with a namespace for a particular subsystem of our application.
from twisted.logger import Logger
log = Logger("client_tcp")


class TCPClient(Protocol):
    def __init__(self, name, context):
        super()
        self._name = name
        self._context = context
        
        self._tcp_packetizer = None

        self._commands = {}
        self._register_commands()

        print("Client started")

        
    def register_command(self, command, function):
        self._commands[command] = function

        
    def _register_commands(self):
        self.register_command("download", self._command_download)
        self.register_command("record", self._command_record)

        
    def connectionMade(self):
        log.info("Connection made")
        self._tcp_packetizer = TCPPacketizer(self.transport)
        database = self._context["database"]
        d = database.get_client_id()

        def announce(client_id):
            log.info(f"Announcing with username '{self._name}'")
            data = {
                "command":"announce",
                "client_id": client_id,
                "username": self._name
            }
            msg = json.dumps(data)

            return self._tcp_packetizer.write(msg)

        def on_error(error):
            log.error(f"Failed to announce with username '{self._name}': "+str(error))
            return error

        d.addCallback(announce)
        d.addErrback(on_error)

        return d

        
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
            # Swallow this error; it doesn't need to propagate
            log.warn(f"No function was registered against the command '{command}'")
            return

        try:
            function(decoded_packet)
        except Exception as e:
            raise #Exception(f"Failed during executing of the function for command '{command}': "+str(e))

        
    def _command_download(self, data):
        reactor = self._context["reactor"]
        session_files = self._context["session_files"]
        audio_id = data["audio_id"]
        partial_url = data["partial_url"]

        ip_address = str(self.transport.getPeer().host)
        url = "http://" + ip_address + partial_url

        file_path = session_files.session_dir / f"{audio_id}.opus"
        
        log.info(f"Downloading file from {url} to {file_path}")

        url_bytes = url.encode("utf-8")
        url_parsed = URI.fromBytes(url_bytes)
        factory = HTTPDownloader(url_bytes, str(file_path))
        reactor.connectTCP(url_parsed.host, url_parsed.port, factory)
        d = factory.deferred
        def on_success(data):
            # File downloaded succesfully, tell the server
            result = {
                "command": "update_downloaded",
                "audio_id": audio_id,
                "result": "success"
            }
            result_json = json.dumps(result)
            self._tcp_packetizer.write(result_json)
            
        def on_error(error):
            # File failed to downloaded succesfully, tell the server
            log.error(f"Failed to download file at '{url}': {error}")
            result = {
                "command": "update_downloaded",
                "audio_id": audio_id,
                "result": "failure",
                "error": str(error)
            }
            result_json = json.dumps(result)
            self._tcp_packetizer.write(result_json)

        d.addCallback(on_success)
        d.addErrback(on_error)

        return d

    def _command_record(self, data):
        backing_audio_ids = data["backing_audio_ids"]
        recording_audio_id = data["recording_audio_id"]

        print("'Record' command received with")
        print("backing_audio_ids:", backing_audio_ids)
        print("recording_audio_id:", recording_audio_id)

        # Shut down the UDPClient if it's running
        
        # TODO: Create a FileTransportClient

        # Open a file for output
        out_file = open("out.opus", "wb")
        
        # Create a recording mode
        recording_mode = RecordingMode(
            out_file,
            backing_audio_ids,
            recording_audio_id,
            self._context
        )

        d = recording_mode.record()

        def close_file(audio_id):
            print("Closing file")
            # Close file
            out_file.close()
        d.addBoth(close_file)

        return d
            
