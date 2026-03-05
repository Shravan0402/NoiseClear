"""Lock-free single-producer single-consumer ring buffer for real-time audio."""

import numpy as np


class RingBuffer:
    """SPSC lock-free circular buffer using numpy.

    Designed for the PortAudio callback (producer) and processing thread
    (consumer) to exchange audio data without locks. The PortAudio callback
    runs in a real-time thread where blocking is not allowed.
    """

    def __init__(self, capacity):
        self._buffer = np.zeros(capacity, dtype=np.float32)
        self._capacity = capacity
        self._write_pos = 0
        self._read_pos = 0

    def write(self, data):
        """Write samples into the buffer. Returns number of samples written."""
        n = len(data)
        available = self.available_write()
        if n > available:
            n = available
        if n == 0:
            return 0

        end = self._write_pos + n
        if end <= self._capacity:
            self._buffer[self._write_pos:end] = data[:n]
        else:
            first = self._capacity - self._write_pos
            self._buffer[self._write_pos:] = data[:first]
            self._buffer[:n - first] = data[first:n]

        self._write_pos = (self._write_pos + n) % self._capacity
        return n

    def read(self, count):
        """Read up to count samples. Returns available samples as numpy array."""
        available = self.available_read()
        n = min(count, available)
        if n == 0:
            return np.array([], dtype=np.float32)

        end = self._read_pos + n
        if end <= self._capacity:
            result = self._buffer[self._read_pos:end].copy()
        else:
            first = self._capacity - self._read_pos
            result = np.concatenate([
                self._buffer[self._read_pos:],
                self._buffer[:n - first]
            ])

        self._read_pos = (self._read_pos + n) % self._capacity
        return result

    def available_read(self):
        """Number of samples available to read."""
        diff = self._write_pos - self._read_pos
        if diff < 0:
            diff += self._capacity
        return diff

    def available_write(self):
        """Number of samples that can be written without overwriting."""
        return self._capacity - self.available_read() - 1

    def clear(self):
        """Reset the buffer."""
        self._read_pos = 0
        self._write_pos = 0
