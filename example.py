# %%
from nidaqworker.tasks import SineTask, RampTask, TTLTask, AnalogTaskGroup
from nidaqworker import NIWorker
import matplotlib.pyplot as plt
import numpy as np

# %%
fs = 1000
task_t = 4
task1 = SineTask(f0=7, channel="A1", offset_t=1, signal_t=2, min_v=1)
sig = task1.signal(fs, task_t)
plt.plot(np.arange(sig.size) / 1000, sig)

# %%
task2 = TTLTask(
    f0=7,
    channel="A2",
    offset_t=0,
    signal_t=4,
    min_v=1,
    ttl_width=0.002,
)
sig = task2.signal(fs, task_t)
plt.plot(np.arange(sig.size) / 1000, sig)

# %%
task3 = RampTask(
    channel="A3",
    offset_t=1,
    signal_t=2,
    min_v=1,
)
sig = task3.signal(fs, task_t)
plt.plot(np.arange(sig.size) / 1000, sig)

# %%
x = AnalogTaskGroup(fs, task_t)
x.add_tasks(task1, task2, task3)


# %%
worker = NIWorker("Dev2")

# %%


# %%
worker.run_tasks((x,))

# %%
