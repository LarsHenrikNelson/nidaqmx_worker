import time
from typing import Union, Literal

import nidaqmx
from nidaqmx.constants import WAIT_INFINITELY
from nidaqmx.stream_writers import AnalogMultiChannelWriter
from nidaqmx.system import System
from nidaqmx.system import Device
import numpy as np
from .tasks import AnalogTaskGroup


class NIWorker:
    def __init__(self, device_name: str | None = None, seed: int = 42):
        self.sys_info = System()
        if device_name is None:
            self.device = Device(self.sys_info.devices.device_names[0])
        else:
            if device_name in self.sys_info.devices.device_names:
                self.device = device_name
            else:
                raise ValueError("Device not recognized.")
        self.ni_task = None
        self.callback = print
        self.rng = np.random.default_rng(seed)

    def available_ao_channels(self):
        print(Device(self.device).ao_physical_chans.channel_names)

    @staticmethod
    def available_devices():
        sys_info = System()
        print(sys_info.devices.device_names)

    def _create_tasks(self, tasks, repeats, repeat_type):
        if repeat_type == "tile":
            output_tasks = [tasks for _ in range(repeats)]
        elif repeat_type == "repeat":
            output_tasks = []
            for i in tasks:
                output_tasks.append([i] * repeats)
        elif repeat_type == "random":
            indices = np.arange(len(tasks))
            output_tasks = []
            for i in range(repeats):
                temp = self.rng.permuted(indices)
                output_tasks.append([tasks[i] for i in temp])
        return output_tasks

    def run_tasks(
        self,
        tasks: AnalogTaskGroup | tuple[AnalogTaskGroup, ...] | list[AnalogTaskGroup],
        iti: Union[float, int, tuple[float, int]] = 0,
        repeats: int = 1,
        repeat_iti: Union[float, int, tuple[float, int]] = 0,
        repeat_type: Literal["tile", "repeat", "random"] = "tile",
    ) -> None:
        if not isinstance(tasks, (tuple, list)):
            tasks = (tasks,)
        run_tasks = self._create_tasks(tasks, repeats, repeat_type)
        for i, task in enumerate(run_tasks):
            self.callback(f"Running iteration {i + 1} for task group: {task.name}")
            for j, subtask in enumerate(task):
                if j > 0:
                    tm = self._iti(iti)
                    time.sleep(tm)
                self.run_task(subtask)
            tm = self._iti(repeat_iti)
            time.sleep(tm)

    def _iti(self, iti):
        if isinstance(iti, (list, np.ndarray, tuple)):
            r = iti[1] - iti[0]
            tm = self.rng.random(
                size=1,
            )
            tm *= r
            tm += iti[0]
        else:
            tm = iti
        return tm

    def run_task(self, task_settings: AnalogTaskGroup):
        ni_task = nidaqmx.Task(task_settings.name)
        self.callback(f"Running task {task_settings.name}")
        self.set_ao_channels(task_settings, ni_task)
        ni_task.timing.cfg_samp_clk_timing(
            rate=task_settings.fs, samps_per_chan=task_settings.length
        )
        if task_settings.trigger != "":
            ni_task.triggers.start_trigger.cfg_dig_edge_start_trig(
                f"/{self.device}/{task_settings.trigger}"
            )

        outstream = ni_task.out_stream
        writer = AnalogMultiChannelWriter(outstream)
        writer.write_many_sample(task_settings.signal)
        ni_task.start()
        ni_task.wait_until_done(timeout=WAIT_INFINITELY)
        ni_task.stop()
        ni_task.close()
        ni_task = None

    def set_ao_channels(self, task: AnalogTaskGroup, ni_task):
        for i in task.channels:
            ni_task.ao_channels.add_ao_voltage_chan(f"{self.device}/ao{i}")
