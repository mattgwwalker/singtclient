# Check that audio can be played... at all.
import pyogg
import time
import sounddevice as sd
import numpy
from enum import Enum
import time
import threading
import math
import operator
import wave
from .measure_levels import measure_levels
from .measure_latency_phase_one import measure_latency_phase_one
from .measure_latency_phase_two import measure_latency_phase_two


def measure_latency(desired_latency="high", repeats=3):
    print("Desired latency:", desired_latency)
    levels = measure_levels(desired_latency)

    phase_one_median_latencies = []
    for i in range(repeats):
        print("\n")
        latencies = measure_latency_phase_one(levels, desired_latency)
        median_latency = numpy.median(latencies)
        print("median latency (ms):", round(median_latency*1000))
        phase_one_median_latencies.append(median_latency)

    phase_two_median_latencies = []
    for i in range(repeats):
        print("\n")
        latencies = measure_latency_phase_two(levels, desired_latency)
        print("latencies:", latencies)
        if latencies is None:
            # Insufficient number of successful measures (multiple possible clicks detected)
            print("Warning: No median produced")
        else:
            median_latency = numpy.median(latencies)
            print("median latency (ms):", round(median_latency*1000))
            phase_two_median_latencies.append(median_latency)

    if len(phase_one_median_latencies) > 0:
        phase_one_mean_median_latency = numpy.mean(phase_one_median_latencies)
        print(
            "Phase One: Mean of the median latencies (ms):",
            round(phase_one_mean_median_latency*1000)
        )
    else:
        phase_one_mean_median_latency = None
        print("Phase One: Insufficient results to calculate mean of median latencies")

    if len(phase_two_median_latencies) > 0:
        phase_two_mean_median_latency = numpy.mean(phase_two_median_latencies)
        print(
            "Phase Two: Mean of the median latencies (ms):",
            round(phase_two_mean_median_latency*1000)
        )
    else:
        phase_two_mean_median_latency = None
        print("Phase Two: Insufficient results to calculate mean of median latencies")
    
    return {
        "levels":levels,
        "phase_one_mean_median_latency":phase_one_mean_median_latency,
        "phase_two_mean_median_latency":phase_two_mean_median_latency
    }
