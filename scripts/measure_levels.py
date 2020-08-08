from singtclient.pre_flight.measure_levels import measure_levels

if __name__ == "__main__":
    #     0         1         2         3         4         5         6         7         8
    #     012345678901234567890123456789012345678901234567890123456789012345678901234567890
    print("")
    print("Measuring Levels")
    print("================")
    print("")
    print("We are now going to measure the levels heard by your microphone when we play")
    print("some tones.  These levels will be used later, when measuring the latency in")
    print("your system.")          
    print("")
    print("You will need to adjust the position of the microphone and output device.  For")
    print("this measurement, the microphone needs to be able to hear the output.  So, for")
    print("example, if you have headphones with an inline microphone, place the microphone")
    print("over one of the ear pieces.")
    print("")
    print("The process takes a few seconds.  It will first record the background noise,")
    print("then it will play a couple of tones.  You will need to ensure the volume is")
    print("sufficiently high so that the microphone can reliably hear the output.")
    print("")
    print("Do not move the microphone or output device once the system can hear the")
    print("constant tone.  Do not make any noise during this measurement.")
    print("")
    print("Press enter to start.")
    print("")

    input() # wait for enter key

    levels = measure_levels(
        desired_latency = 100/1000
        #desired_latency="high"
        #desired_latency="low"
    )
    print(levels)
