from pathlib import Path

import pytest
from twisted.internet import reactor
from twisted.internet.task import LoopingCall

from singtclient import RecordingMode
from singtclient import SessionFiles

def test_create_recording_mode():
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
        reactor_ = context["reactor"]
        print("Stopping reactor")
        reactor_.stop()
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

    # Start reactor
    print("Starting reactor")
    reactor_ = context["reactor"]
    reactor_.callWhenRunning(start_looping)
    reactor_.run()
    
    print("Finished")


