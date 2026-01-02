# %%
from nidaqworker import (
    NIWorker,
    AnalogTaskGroup,
    Sine,
    Ramp,
    TTL,
    Chirp,
)
import matplotlib.pyplot as plt
import numpy as np

# %%
NIWorker.available_devices()

# %%
worker = NIWorker("Dev2")

# %%
channels = worker.available_ao_channels()

# %%
fs = 1000
task_t = 4

# %%
task1 = Sine(f0=7, channel=channels[0], offset_t=1, signal_t=2, min=1)
sig = task1.signal(fs, task_t)
plt.plot(np.arange(sig.size) / 1000, sig)


# %%
task2 = TTL(f0=7, channel=channels[1], offset_t=0, signal_t=4, min=1, ttl_width=0.002)
sig = task2.signal(fs, task_t)
plt.plot(np.arange(sig.size) / 1000, sig)

# %%
task3 = Ramp(channel=channels[2], offset_t=1, signal_t=2, min=1)
sig = task3.signal(fs, task_t)
plt.plot(np.arange(sig.size) / 1000, sig)

# %%
task4 = Chirp(f0=0.2, f1=20, channel=channels[0], offset_t=1, signal_t=2, min=1)
sig = task4.signal(fs, task_t)
plt.plot(np.arange(sig.size) / 1000, sig)

# %%
# Sine task on two channels with a TTL task for indentification
sine_task = AnalogTaskGroup(fs, task_t, "sine_task")
task1 = Sine(f0=7, channel=channels[0], offset_t=1, signal_t=2, min=1)
task2 = Sine(f0=7, channel=channels[1], offset_t=1, signal_t=2, min=1)
task3 = TTL(
    f0=1,
    channel=channels[2],
    offset_t=0,
    signal_t=4,
    min=1,
    ttl_width=0.002,
)
# Tasks to task group
sine_task.add_waveforms(task1, task2, task3)

# %%
# Ramp task with TTL task for identification
ramp_task = AnalogTaskGroup(fs, task_t, "ramp_task")
task1 = task3 = Ramp(channel=channels[0], offset_t=1, signal_t=2, min=1)
task2 = task3 = Ramp(channel=channels[1], offset_t=1, signal_t=2, min=1)
task3 = TTL(
    f0=2,
    channel=channels[2],
    offset_t=0,
    signal_t=4,
    min=1,
    ttl_width=0.002,
)
# Tasks to task group
ramp_task.add_waveforms(task1, task2, task3)

# %%
# Task with not break between repeats
worker.run_tasks(sine_task)

# %%
# Task with iti of 30 between tasks
worker.run_tasks((sine_task, ramp_task), repeats=2, iti=10, repeat_type="tile")

# %%
