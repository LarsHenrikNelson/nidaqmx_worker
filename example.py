from nidaqworker import NIWorker


worker = NIWorker("Dev2")

# All tasks take samples as input except for isi and iti which are in seconds
worker.create_ramp_task(
    fs=1000,
    pulse_t=5000,
    ramp_t=3000,
    offset_t=1000,
    v_range=3,
    min_v=0,
    repititions=5,
    isi=60,
    channels=[1, 2],
)
worker.create_sine_task(
    fs=1000,
    f0=40,
    pulse_t=5000,
    sine_t=3000,
    offset_t=0,
    min_v=1.0,
    v_range=1,
    repititions=5,
    isi=60,
    channels=[1, 2],
)
worker.create_ttl_task(
    fs=1000,
    f0=40,
    pulse_t=5000,
    sine_t=300,
    offset_t=0,
    min_v=0.0,
    v_range=3.0,
    repititions=5,
    isi=60,
    channels=[1, 2],
)

worker.run_tasks(30)
