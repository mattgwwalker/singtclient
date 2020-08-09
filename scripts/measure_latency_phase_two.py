from singtclient.pre_flight.measure_levels import measure_levels
from singtclient.pre_flight.measure_latency_phase_two import measure_latency_phase_two

if __name__ == "__main__":
    print("")
    print("Measuring Latency: Phase Two")
    print("============================")
    print("FIXME: NEEDS RE_WRITE")
    print("We are now going to measure the latency in your audio system.  Latency is the time")
    print("starting from when the program requests that a sound is made, until the program hears")
    print("that sound in a recording of itself.  This latency measure is used to adjust recordings")
    print("so that they are synchronised with the backing track.  If you change the configuration")
    print("of the either the playback or the recording device then you will need to re-run this")
    print("measurement.")
    print("")
    print("You will need to adjust the position of the microphone and output device.  For this")
    print("measurement, the microphone needs to be able to hear the output.  So, for example, if")
    print("you have headphones with an inline microphone, place the microphone over one of the")
    print("ear pieces.")
    print("")
    print("The process takes a few seconds.  It will play a constant tone.  You will need to ")
    print("increase the volume until the microphone can reliably hear the output.  It will then")
    print("play a number of tones until it has approximately measured the latency in your system.")
    print("It will then play a number of clicks to accurately measure the latency.")
    print("")
    print("Do not move the microphone or output device once the system can hear the constant tone.")
    print("Do not make any noise during this measurement.")
    print("")
    print("Press enter to start.")
    print("")

    input() # wait for enter key

    desired_latency = 100/1000 # seconds
    levels = measure_levels(desired_latency)
    measure_latency_phase_two(
        levels=levels,
        desired_latency=desired_latency,
        channels=(1,1)
        #channels=(2,2)
    )
