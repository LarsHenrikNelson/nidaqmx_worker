from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar

import numpy as np
from scipy.signal import chirp


@dataclass
class AnalogWaveform(ABC):
    task_name: ClassVar[str]
    channel: str
    offset_t: float | int
    signal_t: float | int
    max: float | int = 5
    min: float | int = -5
    trigger: str = ""

    @abstractmethod
    def signal(self, fs, task_t) -> np.ndarray: ...

    def _create_line(self, signal, fs):
        return np.linspace(0, signal, num=int(signal * fs), endpoint=False)

    def _create_zeros(self, signal, fs):
        return np.zeros(int(signal * fs))


@dataclass(kw_only=True)
class Sine(AnalogWaveform):
    f0: float | int
    phi: float = np.pi * 3 / 2
    task_name: ClassVar[str] = "sine"

    def signal(self, fs: float | int, task_t: float | int | None = None) -> np.ndarray:
        samples = self._create_line(self.signal_t, fs)
        sine_curve = np.sin(2 * np.pi * self.f0 * samples + self.phi)
        sine_curve -= sine_curve.min()
        sine_curve /= sine_curve.max()
        sine_curve *= self.max - self.min
        sine_curve += self.min
        if task_t is None:
            task_t = self.signal_t + self.offset_t
        sine_data = self._create_zeros(task_t, fs)
        start = int(self.offset_t * fs)
        end = start + int(self.signal_t * fs)
        sine_data[start:end] = sine_curve
        return sine_data


@dataclass(kw_only=True)
class Chirp(AnalogWaveform):
    f0: float | int
    f1: float | int
    phi: float = np.pi
    task_name: ClassVar[str] = "chirp"

    def signal(self, fs: float | int, task_t: float | int | None = None) -> np.ndarray:
        samples = self._create_line(self.signal_t, fs)
        h = chirp(
            samples, f0=self.f0, f1=self.f1, phi=np.rad2deg(self.phi), t1=samples[-1]
        )
        if task_t is None:
            task_t = self.signal_t + self.offset_t
        chirp_data = self._create_zeros(task_t, fs)
        h -= h.min()
        h /= h.max()
        h *= self.max - self.min
        h += self.min
        start = int(self.offset_t * fs)
        end = start + int(self.signal_t * fs)
        chirp_data[start:end] = h
        return chirp_data


@dataclass(kw_only=True)
class Ramp(AnalogWaveform):
    task_name: ClassVar[str] = "ramp"

    def signal(self, fs: float | int, task_t: float | int | None = None) -> np.ndarray:
        samples = np.linspace(self.min, self.max, num=int(self.signal_t * fs))
        if task_t is None:
            task_t = self.signal_t + self.offset_t
        ramp_data = self._create_zeros(task_t, fs)
        start = int(self.offset_t * fs)
        end = start + int(self.signal_t * fs)
        ramp_data[start:end] = samples
        return ramp_data


@dataclass(kw_only=True)
class TTL(AnalogWaveform):
    f0: float | int
    ttl_width: float | int
    task_name: ClassVar[str] = "ttl"

    def signal(self, fs: float | int, task_t: float | int | None = None) -> np.ndarray:
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
        if task_t is None:
            task_t = self.signal_t + self.offset_t
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
                ttl_data[int(i) : int(i + width)] = self.max - self.min
            else:
                raise ValueError("TTL pulse is longer than task_t.")
        start = int(self.offset_t * fs)
        end = start + int(self.signal_t * fs)
        ttl_data[start:end] += self.min

        return ttl_data
