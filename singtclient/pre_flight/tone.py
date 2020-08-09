import math
import numpy
import operator
from enum import Enum
import time # For debugging

# TODO: Tone would be better re-written so that it accepted commands
# (play, stop, fade-out-over-x-seconds) and stored those commands in
# internal state.  It would have another method, say, execute() which
# copied the appropriate data into the outdata.  The advantage of this
# approach would be fade-outs over periods longer than the frame size,
# and stopping that finished on a zero-crossing, which would stop
# clicks.

class Tone:
    class State(Enum):
        INACTIVE = 0
        PLAYING = 1
        FADING_IN = 2
        FADING_OUT = 3
        STOPPING = 4
        CLICKING = 5
                
    
    def __init__(self, freq, samples_per_second=48000,
                 channels=1, max_level=1, duration=1):
        """Freq in Hz, duration in seconds.  Will extend the duration so that
        a whole number of wavelengths are formed."""

        self._samples_per_second = samples_per_second
        self._freq = freq
        self._state = Tone.State.INACTIVE
        
        # Extend the duration so that the PCM finishes on a
        # zero-crossing.
        duration_wavelength = 1 / freq
        num_wavlengths = math.ceil(duration / duration_wavelength)
        duration = num_wavlengths * duration_wavelength
        samples = int(duration * samples_per_second)
        
        t = numpy.linspace(
            0,
            duration,
            samples,
            False
        )

        pcm = numpy.sin(freq * t * 2 * numpy.pi)

        if channels == 2:
            two_channels = [[x,x] for x in pcm]
            self._pcm = numpy.array(two_channels, dtype=numpy.float32)
        else:
            self._pcm = numpy.reshape(pcm, (samples,1))

        # Normalise
        self._pcm *= max_level

        self._pos = 0

        
    @property
    def inactive(self):
        return self._state == Tone.State.INACTIVE

        
    def reset(self):
        """Resets the position index to zero."""
        self._pos = 0
        self._state = Tone.State.INACTIVE

        
    def play(self):
        if self._state == Tone.State.INACTIVE:
            self._state = Tone.State.PLAYING

        
    def stop(self):
        if self._state != Tone.State.INACTIVE:
            self._state = Tone.State.STOPPING


    def _create_fade(self, from_, to_, duration):
        # Produce a linear fadeout multiplier
        samples = int(self._samples_per_second * duration)
        self._fade = numpy.linspace(from_, to_, samples)
        
        
    def fadein(self, duration):
        """Duration in seconds."""
        if self._state == Tone.State.INACTIVE:
            self._state = Tone.State.FADING_IN
            self._create_fade(0, 1, duration)
            self._fade_pos=0
        
        
    def fadeout(self, duration):
        if self._state == Tone.State.PLAYING:
            self._state = Tone.State.FADING_OUT
            self._create_fade(1, 0, duration)
            self._fade_pos=0

        
    def click(self, duration):
        if self._state == Tone.State.INACTIVE:
            self._state = Tone.State.CLICKING

            # Produce a fade profile
            samples = int(self._samples_per_second * duration)
            fade_in = numpy.linspace(0, 1, samples//2)
            fade_out = numpy.linspace(1, 0, samples//2)
            self._fade = numpy.concatenate((fade_in, fade_out))
            self._fade_pos = 0
        

    def _fill(self, outdata, op=None):
        """Op needs to be an in-place operator (see
        https://docs.python.org/3/library/operator.html).  If op is
        None, outdata will be overwritten.
        """
        # Ensure the number of channels is the same
        assert outdata.shape[1] == self._pcm.shape[1]

        # Extract number of samples in outdata
        samples = outdata.shape[0]

        if self._pos+samples <= len(self._pcm):
            # Copy tone in one hit
            data = self._pcm[self._pos:self._pos+samples]
            if op is None:
                outdata[:] = data[:]
            else:
                op(outdata, data)
            self._pos += samples
        else:
            # Need to loop back to the beginning of the tone
            remaining = len(self._pcm)-self._pos
            head = self._pcm[self._pos:len(self._pcm)]
            tail = self._pcm[:samples-remaining]
            if op is None:
                outdata[:remaining] = head[:]
                outdata[remaining:] = tail[:]
            else:
                op(outdata[:remaining], head[:])
                op(outdata[remaining:], tail[:])

            self._pos = samples-remaining

            
    def output(self, outdata, op = None):
        """Op needs to be an in-place operator (see
        https://docs.python.org/3/library/operator.html).  If op is
        None, outdata will be overwritten.
        """
        # Ensure the number of channels is the same
        if outdata.shape[1] != self._pcm.shape[1]:
            raise Exception(
                f"Number of channels for output ({outdata.shape[1]}) "+
                f"is not the same as the number of channels in the "+
                f"tone ({self._pcm.shape[1]})."
            )
        
        channels = outdata.shape[1]

        # Extract number of samples in outdata
        samples = outdata.shape[0]

        if self._state == Tone.State.INACTIVE:
            if op is None:
                outdata.fill(0)
            else:
                zeros = numpy.zeros((outdata.shape), numpy.float32)
                op(outdata, zeros)
        
        if self._state == Tone.State.PLAYING:
            self._fill(outdata, op)

        elif self._state == Tone.State.FADING_IN or \
             self._state == Tone.State.FADING_OUT or \
             self._state == Tone.State.CLICKING:
            # Get the length of the active section of the fade
            fade_length = len(self._fade) - self._fade_pos
            if fade_length > samples:
                # We can only output a portion of the fade during this
                # call.
                fade_length = samples

            # Adjust multiplier if two channels are needed and extract
            # the active section
            channels = outdata.shape[1]
            if channels == 2:
                fade = numpy.array([[x,x] for x in self._fade[
                    self._fade_pos:self._fade_pos+fade_length]])
            elif channels == 1:
                fade = self._fade[self._fade_pos:self._fade_pos+fade_length]
                fade = numpy.reshape(fade, (-1,1))
            else:
                raise Exception("Unsupported number of output channels")

            # Apply the fade
            self._fill(fade, op=operator.imul)

            # Copy the data to outdata
            if op is None:
                outdata[:fade_length] = fade[:]
            else:
                op(outdata[:fade_length], fade[:])
            
            # Update the position in the fade
            self._fade_pos += fade_length

            # If we've come to the end of the fade, move to either to
            # "playing" or "inactive", but fill the rest of the buffer.
            if self._fade_pos == len(self._fade):
                view = outdata[fade_length:]
                if self._state == Tone.State.FADING_IN:
                    self._state = Tone.State.PLAYING

                    # If we haven't entirely filled the buffer with the
                    # fade then fill the rest of the buffer now.
                    self._fill(view, op=op)
                else:
                    self._state = Tone.State.INACTIVE
                    self._pos = 0

                    # If we haven't entirely filled the buffer with the
                    # fade then fill the rest of the buffer now.
                    if op is None:
                        view.fill(0)
                    else:
                        zeros = numpy.zeros((view.shape), numpy.float32)
                        op(view, zeros)

                
        if self._state == Tone.State.STOPPING:
            # Calculate the location of the end of the wavelength
            duration_wavelength = 1 / self._freq
            samples_per_wavelength = int(
                self._samples_per_second * duration_wavelength
            )
            end_wavelength = (
                math.ceil(self._pos / samples_per_wavelength)
                * samples_per_wavelength
            )
            samples_remaining = end_wavelength - self._pos
            if samples_remaining > samples:
                # We can't stop in the current frame, so just fill as
                # normal
                print("WARNING: Can't stop in the current frame")
                self._fill(outdata, op)
            else:
                # We can stop in the current frame.
                # Fill up to the stop point and then fill with zeros.
                view1 = outdata[:samples_remaining]
                self._fill(view1, op)
                
                view2 = outdata[samples_remaining:]
                zeros = numpy.zeros(
                    (samples - samples_remaining,channels),
                    numpy.float32
                )
                if op is None:
                    view2[:] = zeros[:]
                else:
                    op(view2, zeros)
                self._state = Tone.State.INACTIVE
                self.reset()
