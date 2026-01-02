from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar

import numpy as np
from scipy.signal import chirp
from .waveforms import AnalogWaveform


@dataclass
class AnalogTaskGroup:
    fs: float | int
    task_t: float | int | None = None
    name: str = ""
    trigger: str = ""
    tasks: list[AnalogWaveform] = field(default_factory=list)

    def _check_channels(self, items: tuple[AnalogWaveform, ...]):
        temp = {i.channel for i in items}
        temp2 = {i.channel for i in self.tasks}
        union = temp.union(temp2)
        if len(union) != (len(temp) + len(temp2)):
            raise ValueError("Cannot have multiple tasks on the same channel.")

    def _check_length(self, items: tuple[AnalogWaveform, ...]):
        temp = [i.signal_t + i.offset_t for i in items]
        if self.task_t is None:
            self.task_t = max(temp)
        for i in temp:
            if i > self.task_t:
                raise ValueError(f"All tasks must be less than {self.task_t}")

    def add_waveforms(self, *tasks: AnalogWaveform):
        self._check_channels(tasks)
        self._check_length(tasks)
        self.tasks.extend(tasks)

    @property
    def signal(self):
        if self.task_t is None:
            raise ValueError("task_t must be set or tasks must be added")
        signal = np.zeros((len(self.tasks), int(self.task_t * self.fs)))
        for i, task in enumerate(self.tasks):
            signal[i] = task.signal(self.fs, self.task_t)
        return signal

    @property
    def length(self):
        if self.task_t is None:
            raise ValueError("task_t must be set or tasks must be added")
        return int(self.task_t * self.fs)

    @property
    def channels(self):
        return [i.channel for i in self.tasks]
