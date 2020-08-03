# Check that audio can be played... at all.
import pyogg
import time
import sounddevice as sd
import pkg_resources

def check_play_audio():
    filename = pkg_resources.resource_filename("singtclient", "sounds/warm-up.opus")

    print("Loading sound file...")
    opus_file = pyogg.OpusFile(filename)
    pcm = opus_file.as_array()

    print("Playing...")
    sd.play(pcm,
            opus_file.frequency)

    
    

if __name__ == "__main__":
    print("")
    print("Playing Audio")
    print("=============")
    print("")
    print("This test checks that we can play an Opus file and that you can hear it.\n")

    device_strings = sd.query_devices()
    default_output_index = sd.default.device[1]
    default_device_string = device_strings[default_output_index]["name"]
    print("Selected output device:", default_device_string)

    print("\nCan you hear the audio?")
    print("Type 'y' followed by enter if you can hear the audio correctly.")
    print("")
    print("If you can't hear Choeur Adleisia warming up, then try turning up the")
    print("volume on your speakers.  If your speakers have an 'on' switch, check")
    print("that they're turned on.  Check that you haven't muted your speakers.")
    print("Check the sound output settings on your operating system.")
    print("")
    print("To stop playback, and to indicate that this check has failed, just press enter.")
    
    check_play_audio()
    user_input = input()
    
    if len(user_input)>=1 and (user_input[0] == "y" or user_input[0]=="Y"):
        print("Check passed.")
    else:
        print("Check failed.")
