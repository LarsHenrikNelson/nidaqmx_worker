from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar

import numpy as np


@dataclass
class AnalogTask(ABC):
    task_name: ClassVar[str]
    channel: str
    offset_t: float | int
    signal_t: float | int
    max_v: float | int = 5
    min_v: float | int = -5
    trigger: str = ""

    @abstractmethod
    def signal(self, fs, task_t) -> np.ndarray: ...

    def _create_line(self, signal, fs):
        return np.linspace(0, signal, num=int(signal * fs), endpoint=False)

    def _create_zeros(self, signal, fs):
        return np.zeros(int(signal * fs))


@dataclass
class AnalogTaskGroup:
    fs: float | int
    task_t: float | int
    name: str = ""
    trigger: str = ""
    tasks: list[AnalogTask] = field(default_factory=list)

    def _check_channels(self, items: tuple[AnalogTask, ...]):
        temp = {i.channel for i in items}
        temp2 = {i.channel for i in self.tasks}
        union = temp.union(temp2)
        if len(union) != (len(temp) + len(temp2)):
            raise ValueError("Cannot have multiple tasks on the same channel.")

    def _check_length(self, items: tuple[AnalogTask, ...]):
        temp = [i.signal_t + i.offset_t for i in items]
        for i in temp:
            if i > self.task_t:
                raise ValueError(f"All tasks must be less than {self.task_t}")

    def add_tasks(self, *tasks: AnalogTask):
        self._check_channels(tasks)
        self._check_length(tasks)
        self.tasks.extend(tasks)

    @property
    def signal(self):
        signal = np.zeros((len(self.tasks), int(self.task_t * self.fs)))
        for i, task in enumerate(self.tasks):
            signal[i] = task.signal(self.fs, self.task_t)
        return signal

    @property
    def length(self):
        return int(self.task_t * self.fs)

    @property
    def channels(self):
        return [i.channel for i in self.tasks]


@dataclass(kw_only=True)
class SineTask(AnalogTask):
    f0: float | int
    task_name: ClassVar[str] = "sine"

    def signal(self, fs: float | int, task_t: float | int):
        samples = self._create_line(self.signal_t, fs)
        sine_curve = np.sin(2 * np.pi * self.f0 * samples + (np.pi * 3 / 2))
        sine_curve -= sine_curve.min()
        sine_curve /= sine_curve.max()
        sine_curve *= self.max_v - self.min_v
        sine_curve += self.min_v
        sine_data = self._create_zeros(task_t, fs)
        start = int(self.offset_t * fs)
        end = start + int(self.signal_t * fs)
        sine_data[start:end] = sine_curve
        return sine_data


@dataclass(kw_only=True)
class RampTask(AnalogTask):
    task_name: ClassVar[str] = "ramp"

    def signal(self, fs: float | int, task_t: float | int):
        samples = np.linspace(self.min_v, self.max_v, num=int(self.signal_t * fs))
        ramp_data = self._create_zeros(task_t, fs)
        start = int(self.offset_t * fs)
        end = start + int(self.signal_t * fs)
        ramp_data[start:end] = samples
        return ramp_data


@dataclass(kw_only=True)
class TTLTask(AnalogTask):
    f0: float | int
    ttl_width: float | int
    task_name: ClassVar[str] = "sine"

    def signal(self, fs: float | int, task_t: float | int):
        num_pulses = int(self.signal_t * self.f0)
        if num_pulses == 0:
            num_pulses = 1
        ttl_indexes = np.linspace(
            0,
            int(self.signal_t * fs),
            num=num_pulses,
            endpoint=False,
            dtype=int,
        )
        width = int(self.ttl_width * fs)
        if num_pulses > 1:
            temp = ttl_indexes[-1] - ttl_indexes[0]
            if temp < width:
                raise ValueError("TTL width too wide for f0.")
        else:
            if (self.ttl_width + self.offset_t) > task_t:
                raise ValueError("TTL width too wide for task_t.")
        ttl_data = self._create_zeros(task_t, fs)
        ttl_indexes += int(self.offset_t * fs)
        for i in ttl_indexes:
            if int(i + width) < ttl_data.size:
                ttl_data[int(i) : int(i + width)] = self.max_v - self.min_v
            else:
                raise ValueError("TTL pulse is longer than task_t.")
        start = int(self.offset_t * fs)
        end = start + int(self.signal_t * fs)
        ttl_data[start:end] += self.min_v

        return ttl_data
