import time
from typing import NamedTuple, Union

import nidaqmx
from nidaqmx.constants import WAIT_INFINITELY
from nidaqmx.stream_writers import AnalogMultiChannelWriter
from nidaqmx.system import System
from nidaqmx.system import Device
import numpy as np


class TaskSettings(NamedTuple):
    fs: int
    data: np.ndarray
    task_name: str
    repititions: int
    length: int
    isi: Union[float, int, tuple[float, int]]
    trigger: str
    channels: list


class NIWorker:
    def __init__(self, device_name=None, inplace=True):
        self.tasks = []
        self.sys_info = System()
        if device_name is None:
            self.device = Device(self.sys_info.devices.device_names[0])
        else:
            self.device = device_name
        self.inplace = inplace
        self.ni_task = None
        self.callback = print
        self.rng = np.random.default_rng()

    def create_sine_task(
        self,
        fs: int,
        f0: int,
        pulse_t: int,
        sine_t: int,
        offset_t: int = 0,
        v_range: Union[float, int] = 10,
        min_v: Union[float, int] = -5,
        repititions: int = 1,
        isi: Union[int, float, tuple[int, float]] = 0,
        channels: Union[list, int] = 0,
        task_name: str = "sine",
        trigger: str = "",
    ):
        if isinstance(channels, int):
            channels = [channels]
        assert (offset_t + sine_t) < pulse_t

        samples = np.arange(sine_t) / fs
        sine_curve = np.sin(2 * np.pi * f0 * samples + (np.pi * 3 / 2))
        sine_curve -= sine_curve.min()
        sine_curve /= sine_curve.max()
        sine_curve *= v_range
        sine_curve += min_v
        sine_data = np.zeros((len(channels), pulse_t))
        for i in range(len(channels)):
            sine_data[i, offset_t : int(offset_t + samples.size)] = sine_curve

        task = TaskSettings(
            fs=fs,
            data=sine_data,
            task_name=task_name,
            repititions=repititions,
            length=sine_data.shape[1],
            isi=isi,
            trigger=trigger,
            channels=channels,
        )
        self.tasks.append(task)

        if not self.inplace:
            return self

    def create_ttl_freq_task(
        self,
        fs: int,
        f0: int,
        pulse_t: int,
        ttl_t: int,
        ttl_width: int,
        offset_t: int = 0,
        v_range: Union[float, int] = 10,
        min_v: Union[float, int] = -5,
        repititions: int = 1,
        isi: Union[int, float, tuple[int, float]] = 0,
        channels: Union[list, int] = 0,
        task_name: str = "",
        trigger: str = "",
    ):
        ttl_indexes = np.linspace(
            0, ttl_t, num=int((ttl_t / fs) * f0), endpoint=False, dtype=int
        )
        ttl_data = np.zeros((len(channels), pulse_t))
        ttl_indexes += offset_t
        for i in ttl_indexes:
            for j in range(ttl_width):
                ttl_data[0, int(i + j)] = v_range
                ttl_data[1, int(i + j)] = v_range

        ttl_data += min_v

        task = TaskSettings(
            fs=fs,
            data=ttl_data,
            task_name=task_name,
            repititions=repititions,
            length=ttl_data.shape[0],
            isi=isi,
            trigger=trigger,
            channels=channels,
        )
        self.tasks.append(task)

        if not self.inplace:
            return self

    def create_ramp_task(
        self,
        fs: int,
        pulse_t: int,
        ramp_t: int,
        offset_t: int = 0,
        v_range: Union[float, int] = 10,
        min_v: Union[float, int] = -5,
        repititions: int = 1,
        isi: Union[int, float, tuple[int, float]] = 0,
        channels: Union[list, int] = 0,
        task_name: str = "ramp",
        trigger: str = "",
    ):
        if isinstance(channels, int):
            channels = [channels]
        assert (offset_t + ramp_t) < pulse_t

        samples = np.linspace(min_v, v_range + min_v, num=ramp_t)
        ramp_data = np.zeros((len(channels), pulse_t))
        for i in range(len(channels)):
            ramp_data[i, offset_t : int(offset_t + samples.size)] = samples

        task = TaskSettings(
            fs=fs,
            data=ramp_data,
            task_name=task_name,
            repititions=repititions,
            length=ramp_data.shape[1],
            isi=isi,
            trigger=trigger,
            channels=channels,
        )
        self.tasks.append(task)

        if not self.inplace:
            return self

    def create_ttl_task(
        self,
        fs: int,
        pulse_t: int,
        ttl_width: int,
        offset_t: int = 0,
        v_range: Union[float, int] = 3,
        min_v: Union[float, int] = 0,
        repititions: int = 1,
        isi: Union[int, float, tuple[int, float]] = 0,
        channels: Union[list, int] = 0,
        task_name: str = "ttl",
        trigger: str = "",
    ):
        if isinstance(channels, int):
            channels = [channels]
        assert (offset_t + ttl_width) < pulse_t

        ttl_data = np.full((len(channels), pulse_t), min_v)
        for i in range(len(channels)):
            ttl_data[i, offset_t : int(offset_t + ttl_width)] += v_range

        task = TaskSettings(
            fs=fs,
            data=ttl_data,
            task_name=task_name,
            repititions=repititions,
            length=ttl_data.shape[1],
            isi=isi,
            trigger=trigger,
            channels=channels,
        )
        self.tasks.append(task)

        if not self.inplace:
            return self

    def run_tasks(self, iti: Union[float, int, tuple[float, int]]):
        for i, task in enumerate(self.tasks):
            if i > 0:
                if isinstance(iti, (list, np.ndarray, tuple)):
                    r = iti[1] - iti[0]
                    tm = self.rng.random(
                        size=1,
                    )
                    tm *= r
                    tm += iti[0]
                else:
                    tm = iti
                time.sleep(tm)
            self.run_task(task)

    def run_task(self, task_settings: TaskSettings):
        self.ni_task = nidaqmx.Task(task_settings.task_name)
        self.set_ao_channels(task_settings)
        self.ni_task.timing.cfg_samp_clk_timing(
            rate=task_settings.fs, samps_per_chan=task_settings.length
        )
        if task_settings.trigger != "":
            self.ni_task.triggers.start_trigger.cfg_dig_edge_start_trig(
                f"/{self.device}/{task_settings.trigger}"
            )

        outstream = self.ni_task.out_stream
        writer = AnalogMultiChannelWriter(outstream)
        writer.write_many_sample(task_settings.data)
        if task_settings.repititions == 1:
            self.ni_task.start()
            self.ni_task.wait_until_done(timeout=WAIT_INFINITELY)
            self.ni_task.stop()
        else:
            for i in range(task_settings.repititions):
                if i > 0:
                    if isinstance(task_settings.isi):
                        r = task_settings.isi[1] - task_settings.isi[0]
                        tm = self.rng.random(
                            size=1,
                        )[0]
                        tm *= r
                        tm += task_settings.isi[0]
                    else:
                        tm = task_settings.isi
                    time.sleep(tm)
                self.ni_task.start()
                self.ni_task.wait_until_done(timeout=WAIT_INFINITELY)
                self.ni_task.stop()
        self.ni_task.close()
        self.ni_task = None

    def set_ao_channels(self, task):
        for i in task.channels:
            self.ni_task.ao_channels.add_ao_voltage_chan(f"{self.device}/ao{i}")

    def reset_tasks(self):
        self.tasks = []

        if not self.inplace:
            return self

    def available_ao_channels(self):
        print(Device(self.device).ao_physical_chans.channel_names)

    @staticmethod
    def available_devices():
        sys_info = System()
        print(sys_info.devices.device_names)
