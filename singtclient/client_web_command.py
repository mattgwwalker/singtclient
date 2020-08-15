import json
import sys

import pkg_resources
from twisted.web import server, resource
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.logger import Logger

from .client_tcp import TCPClient
from .client_udp import UDPClient

# Start a logger with a namespace for a particular subsystem of our application.
log = Logger("client_web_command")


class CommandResource(resource.Resource):
    isLeaf = True

    def __init__(self, context):
        super().__init__()
        self._context = context
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
        self.register_command("measure_gain_discussion", self._command_measure_gain_discussion)
        self.register_command("measure_gain_recordings", self._command_measure_gain_recordings)
        self.register_command("measure_loop_back_latency_recordings", self._command_measure_loop_back_latency_recordings)
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
        reactor = self._context["reactor"]
        point = TCP4ClientEndpoint(reactor, address, 1234)
        client = TCPClient(username, self._context)
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
        udp_client = UDPClient(address, 12345, self._context)
        reactor.listenUDP(0, udp_client)

        return server.NOT_DONE_YET

    
    def _command_measure_gain_discussion(self, content, request):
        from .pre_flight import measure_gain

        try:
            instructions_filename = pkg_resources.resource_filename(
                "singtclient",
                "sounds/speak-normally.opus"
            )

            desired_latency = 20/1000 # seconds
            seconds_to_collect = 3
            max_gain = 20

            # Measure the gain
            db, gain_db, gain = measure_gain.measure_gain(
                instructions_filename,
                desired_latency,
                seconds_to_collect,
                max_gain
            )

            # Save result in context
            self._context["discussion_gain"] = gain

            # Return result to web interface
            result = (
                f"<p>Loudest part of the recording: <strong>{db:0.1f}dB</strong> of full scale</p>\n"+
                f"<p>Calculated gain: <strong>{gain_db:0.1f}dB</strong></p>"
            )
        except Exception as e:
            result = "Failed to measure gain: "+str(e)

        result_json = {
            "result": result
        }

        result_json = json.dumps(result_json).encode("utf-8")

        return result_json

    
    def _command_measure_gain_recordings(self, content, request):
        from .pre_flight import measure_gain

        try:
            instructions_filename = pkg_resources.resource_filename(
                "singtclient",
                "sounds/sing-loudly.opus"
            )

            desired_latency = 100/1000 # seconds
            seconds_to_collect = 5
            max_gain = 20

            # Measure the gain
            db, gain_db, gain = measure_gain.measure_gain(
                instructions_filename,
                desired_latency,
                seconds_to_collect,
                max_gain
            )

            # Save result to context
            self._context["recordings_gain"] = gain

            # Send result to web interface
            result = (
                f"<p>Loudest part of the recording: <strong>{db:0.1f}dB</strong> of full scale</p>\n"+
                f"<p>Calculated gain: <strong>{gain_db:0.1f}dB</strong></p>"
            )
        except Exception as e:
            result = "Failed to measure gain: "+str(e)

        result_json = {
            "result": result
        }

        result_json = json.dumps(result_json).encode("utf-8")

        return result_json

    
    def _command_measure_loop_back_latency_recordings(self, content, request):
        from .pre_flight import measure_latency

        try:
            desired_latency = 100/1000 # seconds

            # Measure the loop-back latency
            results = measure_latency.measure_latency(
                desired_latency = desired_latency
            )
            latency_phase_one = results['phase_one_mean_median_latency']
            latency_phase_two = results['phase_two_mean_median_latency']
            mean_latency = (latency_phase_one+latency_phase_two)/2

            # Save the result in the context
            self._context["recordings_latency"] = mean_latency

            # Share the result with the web interface
            warning = ""
            if abs(latency_phase_one-latency_phase_two) > 10/1000:
                warning = (
                    "<p><strong>Warning:</strong> The two methods "+
                    "differed by more than 10 milliseconds.  Please "+
                    "report this to Matthew.</p>"
                )
            
            result = (
                f"<p>Mean latency (phase one): <strong>{latency_phase_one*1000:0.0f} ms</strong></p>\n"+
                f"<p>Mean latency (phase two): <strong>{latency_phase_two*1000:0.0f} ms</strong></p>\n"+
                warning+
                f"<p>Measurement completed, using average of <strong>{mean_latency*1000:0.0f} ms</strong>.</p>"
            )
        except Exception as e:
            result = "Failed to measure loop-back latency for recordings: "+str(e)

        result_json = {
            "result": result
        }

        result_json = json.dumps(result_json).encode("utf-8")

        return result_json

    
    def _command_debug_check_playback(self, content, request):
        from .pre_flight import check_play_audio

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
        from .pre_flight import check_record_audio

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
