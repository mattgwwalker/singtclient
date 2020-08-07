import math
import threading

import numpy
import pkg_resources
import pyogg
import sounddevice as sd


def play_file(filename):
    opus_file = pyogg.OpusFile(filename)
    pcm = opus_file.as_array()
    sd.play(pcm,
            opus_file.frequency)
    sd.wait()

    
def measure_gain(instructions_filename,
                 desired_latency,
                 seconds_to_collect,
                 max_gain):
    # Play instructions
    play_file(instructions_filename)

    # Play recording sound
    recording_filename = pkg_resources.resource_filename(
        "singtclient",
        "sounds/recording.opus"
    )
    play_file(recording_filename)


    # Record
    event = threading.Event()

    samples_per_second = 48000
    channels = 1 # mono

    data = None
    samples_to_collect = (
        samples_per_second
        * seconds_to_collect
    )

    def callback(indata, outdata, frames, time, status):
        nonlocal data

        if status:
            print(status)

        # Record the PCM
        if data is None:
            data = indata.copy()
        else:
            data = numpy.concatenate((
                data,
                indata
            ))

        # Check if we've heard enough
        if len(data) > samples_to_collect:
            raise sd.CallbackStop

        # Monitor the recording
        outdata[:] = indata

    print("Recording...")
    with sd.Stream(samplerate=samples_per_second,
                   latency=desired_latency,
                   channels=channels,
                   callback=callback,
                   finished_callback=event.set):
        event.wait()


    # Play ding
    ding_filename = pkg_resources.resource_filename(
        "singtclient",
        "sounds/discussion.opus"
    )
    play_file(ding_filename)


    # Calculate required gain
    max_data = numpy.max(numpy.abs(data))
    db = 20*math.log10(max_data)
    print(f"Maximum volume of recording: {db:0.1f}dB of full scale (or {max_data*100:0.1f}% on a linear scale).")

    desired_max = 0.5
    gain = desired_max / max_data

    print(f"Calculated gain of {gain:0.1f}-fold")
    if gain > max_gain:
        gain = max_gain
        print(f"Limited gain to {gain:0.1f}-fold")

    gain_db = 20 * math.log10(gain)

    # Apply gain to recording
    adjusted_recording = data * gain


    # Playback adjusted recording
    print("Playing...")
    sd.play(adjusted_recording,
            samples_per_second)

    sd.wait()


    print("Finished")

    return(db, gain_db, gain)


if __name__ == "__main__":
    instructions_filename = pkg_resources.resource_filename(
        "singtclient",
        "sounds/speak-normally.opus"
    )

    desired_latency = 20/1000 # seconds
    seconds_to_collect = 3
    max_gain = 20
    
    db, gain_db, gain = measure_gain(
        instructions_filename,
        desired_latency,
        seconds_to_collect,
        max_gain
    )
    
    print(gain)
