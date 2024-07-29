# %%
from nidaqworker import NIWorker

# %%
worker = NIWorker("Dev2")

# %%
isi = (45, 90)
repititions = 1
# All tasks take samples as input except for isi and iti which are in seconds
worker.create_ramp_task(
    fs=1000,
    pulse_t=5000,
    ramp_t=3000,
    offset_t=1000,
    v_range=2,
    min_v=1,
    repititions=repititions,
    isi=isi,
    channels=[2, 3],
)
worker.create_sine_task(
    fs=1000,
    f0=40,
    pulse_t=5000,
    sine_t=3000,
    offset_t=0,
    min_v=1.0,
    v_range=1,
    repititions=repititions,
    isi=isi,
    channels=[2, 3],
)
worker.create_ttl_task(
    fs=1000,
    pulse_t=5000,
    ttl_width=3,
    offset_t=1000,
    min_v=0.0,
    v_range=3.0,
    repititions=repititions,
    isi=isi,
    channels=[2, 3],
    task_name="ttl",
)
worker.create_ttl_freq_task(
    fs=1000,
    f0=7,
    pulse_t=5000,
    ttl_t=3000,
    ttl_width=5,
    offset_t=1000,
    min_v=0.0,
    v_range=3.0,
    repititions=repititions,
    isi=isi,
    channels=[2, 3],
    task_name="test"
)

# %%
worker.run_tasks(iti=1)

# %%
worker.reset_tasks()

# %%
