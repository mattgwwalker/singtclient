import json
import sys

from twisted.web import server, resource
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.logger import Logger

from singtclient.client_tcp import TCPClient
from singtclient.client_udp import UDPClient

# Start a logger with a namespace for a particular subsystem of our application.
log = Logger("client_web_command")


class CommandResource(resource.Resource):
    isLeaf = True

    def __init__(self, reactor):
        super().__init__()
        self._reactor = reactor
        self._connected = False

        self.commands = {}

        self._register_commands()

    def render_POST(self, request):
        content = request.content.read()
        content = json.loads(content)

        command = content["command"]

        command_handler = self.commands[command]

        return command_handler(content, request)


    def _register_commands(self):
        self.register_command("connect", self._command_connect)
        self.register_command("is_connected", self._command_is_connected)
        self.register_command("debug_check_playback", self._command_debug_check_playback)
        self.register_command("debug_stop_playback", self._command_debug_stop_playback)
        self.register_command("debug_record", self._command_debug_record)
        
    
    def register_command(self, command, function):
        self.commands[command] = function

        
    def _command_is_connected(self, content, request):
        connected_dict = {
            True: "connected",
            False: "not connected"
        }

        result = {
            "result": "success",
            "connected": self._connected
        }

        request.setResponseCode(200)
        #request.responseHeaders.addRawHeader(b"content-type", b"application/json")
        return json.dumps(result).encode("utf-8")

        
    def _command_connect(self, content, request):
        username = content["username"]
        address = content["address"]
        log.info(f"Connecting to server '{address}' as '{username}'")

        # TCP
        point = TCP4ClientEndpoint(self._reactor, address, 1234)
        client = TCPClient(username)
        d = connectProtocol(point, client)

        def on_success(tcp_client):
            print("Connected to server")
            self._connected = True
            request.setResponseCode(200)
            result = {"result": "success"}
            result_json = json.dumps(result).encode("utf-8")
            request.write(result_json)
            request.finish()
        
        def on_error(failure):
            print("ERROR An error occurred:", failure)
            request.setResponseCode(500)
            request.write(b"An error occurred:" + str(failure).encode("utf-8"))
            request.finish()

        d.addCallback(on_success)
        d.addErrback(on_error)

        # UDP
        # 0 means any port, we don't care in this case
        udp_client = UDPClient(address, 12345)
        self._reactor.listenUDP(0, udp_client)

        return server.NOT_DONE_YET

    
    def _command_debug_check_playback(self, content, request):
        from singtclient.pre_flight import check_play_audio

        try:
            check_play_audio.check_play_audio()
            result = (
                "Audio started without error.  If you cannot "+
                "hear anything, ensure that your headphones "+
                "are turned on, unmuted, and that the volume "+
                "is sufficiently high."
            )
        except Exception as e:
            result = "Failed to play audio: "+str(e)

        result_json = {
            "result": result
        }

        result_json = json.dumps(result_json).encode("utf-8")

        return result_json


    def _command_debug_stop_playback(self, content, request):
        import sounddevice as sd
        try:
            sd.stop()
            result = "Playback stopped without error.";
        except Exception as e:
            result = "Failed to stop playback: "+str(e)

        result_json = {
            "result": result
        }

        result_json = json.dumps(result_json).encode("utf-8")

        return result_json
        

    def _command_debug_record(self, content, request):
        from singtclient.pre_flight import check_record_audio

        try:
            check_record_audio.check_record_audio()
            result = (
                "Recording completed.  Playback started "+
                "without error.  If you cannot hear "+
                "anything make sure you first pass the "+
                "audio playback test above.  If you still "+
                "can't hear anything, ensure your microphone "+
                "is correctly plugged in and turned on."
            )
        except Exception as e:
            result = "Failed to record and playback: "+str(e)

        result_json = {
            "result": result
        }

        result_json = json.dumps(result_json).encode("utf-8")

        return result_json
