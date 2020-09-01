from pathlib import Path
from enum import Enum
import math
import threading

import numpy
import pkg_resources
import pyogg
import sounddevice as sd
from singtcommon import RingBuffer
from twisted.internet import reactor
from twisted.internet import defer
from twisted.internet.task import LoopingCall

from .session_files import SessionFiles

# Start a logger with a namespace for a particular subsystem of our application.
from twisted.logger import Logger
log = Logger("recording_mode")


class RecordingMode:
    class State(Enum):
        INTRO = 10
        RECORD = 20
        
    
    def __init__(self, file_like, backing_audio_ids, recording_audio_id, context):
        self._file_like = file_like
        self._backing_audio_ids = backing_audio_ids
        self._recording_audio_id = recording_audio_id
        self._context = context
        
        self._session_files = context["session_files"]

        self._intro_audio_filename = pkg_resources.resource_filename(
            "singtclient",
            "sounds/recording.opus"
        )

        self._stream = None

        # Create a ring buffer shared by the audio callback and the
        # audio writer.  We record in mono.
        buffer_size_s = 1 # second
        self.samples_per_second = 48000
        buffer_size_samples = buffer_size_s * self.samples_per_second
        channels = 1 # mono
        buffer_shape = (buffer_size_samples, channels)
        self._ring_buffer = RingBuffer(
            buffer_shape,
            dtype=numpy.float32
        )

        self._finished = False
        
        
        
    def record(self):
        # Create deferred to return
        self._deferred = defer.Deferred()

        # Load the intro audio
        intro_audio = self._load_intro_audio()
        
        # Load the backing audio
        backing_audio = self._load_backing_audio()

        # Get the recording latency and calculate the desired duration
        try:
            recording_latency_s = self._context["recording_latency"]
        except KeyError:
            log.error(
                "Recording latency was not available in the current "+
                "context.  Assuming zero latency."
            )
            recording_latency_s = 0
        recording_latency_samples = int(
            recording_latency_s * self.samples_per_second
        )
        desired_samples = (
            len(backing_audio[0])
            + recording_latency_samples
        )

        # Create an OggOpusWriter witht the file_like given in the
        # constructor.
        self._writer = pyogg.OggOpusWriter(
            self._file_like,
            custom_pre_skip=recording_latency_samples
        )
        self._writer.set_application("audio")
        self._writer.set_sampling_frequency(self.samples_per_second)
        self._writer.set_channels(1)
        self._writer.set_frame_size(20) # milliseconds
        
        # Create a dict for variables used in callback
        class Variables:
            def __init__(self):
                self.state = RecordingMode.State.RECORD
                self.index = 0
                self.recorded_length = 0
                self.backing_length = len(backing_audio[0])
        v = Variables()

        # Start processing the audio
        self._looping_call = LoopingCall(self._write_audio)
        reactor = self._context["reactor"]
        reactor.callWhenRunning(lambda : self._looping_call.start(20/1000))
        
        # Sounddevice callback for audio processing
        def callback(indata, outdata, frames, time, status):
            if status:
                print(status)

            if v.state == RecordingMode.State.INTRO:
                # Play the intro
                if v.index+frames <= len(intro_audio):
                    outdata[:] = intro_audio[v.index:v.index+frames]
                    v.index += frames
                else:
                    outdata.fill(0)
                    remaining = len(intro_audio)-v.index
                    outdata[:remaining] = intro_audio[:remaining]

                    # Transition to RECORD
                    v.state = RecordingMode.State.RECORD
                    v.index = 0
                
            elif v.state == RecordingMode.State.RECORD:
                # Mix the backing audio
                mixed_backing_audio = None
                for pcm in backing_audio:
                    pcm_section = pcm[v.index:v.index+frames]
                    if mixed_backing_audio is None:
                        mixed_backing_audio = pcm_section
                    else:
                        mixed_backing_audio += pcm_section
                v.index += frames

                # Play the backing audio
                if len(mixed_backing_audio) == frames:
                    outdata[:] = mixed_backing_audio[:]
                else:
                    outdata[:len(mixed_backing_audio)] = (
                        mixed_backing_audio[:]
                    )
                    outdata[len(mixed_backing_audio):].fill(0)

                # Place the input into the ring buffer, from where it will
                # be processed in a non-time-critical thread.  Only save
                # the desired duration of audio
                if v.recorded_length + frames < desired_samples:
                    self._ring_buffer.put(indata)
                    v.recorded_length += frames
                else:
                    # This is the last section of audio we need
                    remaining = desired_samples - v.recorded_length
                    self._ring_buffer.put(indata[:remaining])
                    v.recorded_length += remaining
                    raise sd.CallbackStop

        def callback_finished():
            self._finished = True

        # Create Stream
        self._stream = sd.Stream(
            samplerate = 48000,
            channels = 1,
            dtype = numpy.float32,
            latency = 200/1000,
            callback = callback,
            finished_callback = callback_finished
        )

        # Start the recording.  Stop called by rasing sd.CallbackStop
        # in callback when sufficient audio has been recorded.
        self._stream.start()

        return self._deferred

    def _load_intro_audio(self):
        return self._load_audio(self._intro_audio_filename)
            
    def _load_backing_audio(self):
        paths = [self._session_files.get_path_audio_id(audio_id)
                 for audio_id in self._backing_audio_ids]
        
        backing_audio = [self._load_audio(path)
                         for path in paths]

        # Check that backing audio PCMs are all the same length
        lengths = numpy.array([len(pcm) for pcm in backing_audio])
        if not numpy.all(lengths == lengths[0]):
            raise Exception("Backing audio files were not all the same length")

        return backing_audio

    def _load_audio(self, path):
        opus_file = pyogg.OpusFile(str(path))
        pcm = opus_file.as_array()

        # Normalise
        pcm_float = pcm.astype(numpy.float32)
        pcm_float /= 2**16

        # Convert to mono
        pcm_float = numpy.mean(pcm_float, axis=1)
        pcm_float = numpy.reshape(pcm_float, (-1,1))

        return pcm_float

    def _write_audio(self):
        # Get audio from ring buffer
        length = len(self._ring_buffer)
        channels = 1 # mono
        shape = (length, channels)
        pcm_float = numpy.zeros(shape, dtype=numpy.float32)
        self._ring_buffer.get(pcm_float)

        # Convert audio to 16-bit ints
        pcm_float *= 2**16-1
        pcm_int16 = pcm_float.astype(numpy.int16)
        pcm_bytes = pcm_int16.tobytes()

        # Write audio
        self._writer.encode(pcm_bytes)

        # Check if we've finished
        if self._finished:
            print("Closing OggOpus stream and calling deferred")
            self._writer.close()
            print("Stopping looping call to write_audio")
            self._looping_call.stop()
            self._deferred.callback(self._recording_audio_id)

            
if __name__ == "__main__":
    # Create a context dictionary
    context = {}

    # Add reactor to context
    context["reactor"] = reactor

    # Create SessionFiles
    session_files = SessionFiles(Path.home())
    context["session_files"] = session_files

    # Add latency estimate to context
    context["recording_latency"] = 335/1000 # seconds

    # Open file for writing
    f = open("out.opus", "wb")
    
    # Create RecordingMode
    rec_mode = RecordingMode(
        f,
        backing_audio_ids=[99],
        recording_audio_id=100,
        context=context
    )

    d = rec_mode.record()
    
    def on_success(audio_id):
        print(f"Recording finished successfully for audio_id {audio_id}")
        reactor = context["reactor"]
        print("Stopping reactor")
        reactor.stop()
    d.addCallback(on_success)
    
    def on_error(error):
        print("Recording failed:", error)
    d.addErrback(on_error)

    # Give the reactor something to do, otherwise it partially shuts
    # down
    def print_running():
        print("The reactor is running")
    looping_call = LoopingCall(print_running)
    def start_looping():
        looping_call.start(1)
    reactor.callWhenRunning(start_looping)

    # Start reactor
    print("Starting reactor")
    reactor = context["reactor"]
    reactor.run()
    
    print("Finished")
