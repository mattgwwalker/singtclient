from enum import Enum

import numpy

from singtclient.pre_flight.tone import Tone


if __name__ == "__main__":
    import sounddevice as sd
    import threading
    import queue
    import wave

    samples_per_second = 48000
    channels = 1

    class ProcessState(Enum):
        RESET = 0
        FADEIN = 10
        PLAY = 20
        PLAYING = 25
        FADEOUT = 30
        FADING_OUT = 40
        STOP = 50
        CLICK = 60
        
    class Variables:
        def __init__(self):
            self.process_state = ProcessState.RESET
            
            self.frequency = 375 # Hz
            self.tone = Tone(
                self.frequency,
                channels = channels,
                max_level=0.5
            )

    # Create an instance of the class holding variables to be sotred
    # between calls of the callback
    v = Variables()
            
    # Threading event on which to wait
    event = threading.Event()

    # Queue to store output data for writing later
    q = queue.Queue()

    def callback(outdata, samples, time, status):
        global v
        
        if status:
            print(status)

        # Store any exceptions to be raised
        exception = None

        # Transitions
        # ===========

        if v.process_state == ProcessState.RESET:
            v.process_state = ProcessState.FADEIN

        elif v.process_state == ProcessState.FADEIN:
            v.process_state = ProcessState.PLAYING
            v.state_started = time.outputBufferDacTime

        elif v.process_state == ProcessState.PLAY: 
            v.process_state = ProcessState.PLAYING
            v.state_started = time.outputBufferDacTime

        elif v.process_state == ProcessState.PLAYING:
            duration = time.outputBufferDacTime - v.state_started
            if duration >= 2:
                v.process_state = ProcessState.FADEOUT

        elif v.process_state == ProcessState.FADEOUT:
            v.process_state = ProcessState.FADING_OUT
            
        elif v.process_state == ProcessState.FADING_OUT:
            if v.tone.inactive:
                v.process_state = ProcessState.CLICK
                
        elif v.process_state == ProcessState.CLICK:
            if v.tone.inactive:
                v.process_state = ProcessState.STOP
            
        elif v.process_state == ProcessState.STOP:
            pass

        # Actions
        # =======

        if v.process_state == ProcessState.RESET:
            # Actively fill the output buffer to avoid artefacts.
            outdata.fill(0)

        elif v.process_state == ProcessState.FADEIN:
            print("Fade-in")
            fadein_duration = 0.5 # seconds
            v.tone.fadein(fadein_duration)
            v.tone.output(outdata)
            
        elif v.process_state == ProcessState.PLAY:
            print("Play")
            v.tone.play()
            v.tone.output(outdata)
            
        elif v.process_state == ProcessState.PLAYING:
            #print("Playing")
            v.tone.output(outdata)

        elif v.process_state == ProcessState.FADEOUT:
            print("Fade-out")
            fadeout_duration = 0.5 # seconds
            v.tone.fadeout(fadeout_duration)
            v.tone.output(outdata)
            
        elif v.process_state == ProcessState.FADING_OUT:
            #print("Fading out")
            v.tone.output(outdata)
            
        elif v.process_state == ProcessState.CLICK:
            print("Click")
            click_duration = 10/1000 # seconds
            v.tone.click(click_duration)
            v.tone.output(outdata)

            
            
        elif v.process_state == ProcessState.STOP:
            print("Stop")
            v.tone.stop()
            v.tone.output(outdata)
            assert v.tone.inactive
            exception = sd.CallbackStop

            

            
        # Store output
        # ============
        q.put(outdata.copy())

        # Terminate if required
        # =====================
        if exception is not None:
            raise exception
            
        
            
    # Open an output stream
    stream = sd.OutputStream(
        samplerate=samples_per_second,
        channels=channels,
        dtype=numpy.float32,
        callback=callback,
        finished_callback=event.set)

    with stream:
        event.wait()

        
    # Save output as wave file
    print("Writing wave file")
    wave_file = wave.open("out.wav", "wb")
    wave_file.setnchannels(channels)
    wave_file.setsampwidth(2) # bytes per datatype
    wave_file.setframerate(samples_per_second)
    while True:
        try:
            data = q.get_nowait()
        except:
            break
        data = data * (2**15-1)
        data = data.astype(numpy.int16)
        wave_file.writeframes(data)
    wave_file.close()

        
    print("Finished.")
    
