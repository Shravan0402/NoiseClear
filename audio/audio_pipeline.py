"""Core audio pipeline: capture -> noise cancellation -> output."""

import threading
import time
import numpy as np
import sounddevice as sd

from audio.ring_buffer import RingBuffer
from audio.level_meter import LevelMeter


class AudioPipeline:
    """Manages the full audio pipeline: mic capture -> denoise -> VB-CABLE output.

    Threading model:
    - PortAudio input callback (real-time thread): writes to input ring buffer
    - PortAudio output callback (real-time thread): reads from output ring buffer
    - Processing thread (daemon): reads input -> processes -> writes output
    - All shared state is through lock-free ring buffers
    """

    SAMPLE_RATE = 48000
    FRAME_SIZE = 480       # 10ms frames
    CHANNELS = 1           # Mono
    BUFFER_SECONDS = 1     # Ring buffer capacity

    def __init__(self, device_manager):
        self._device_manager = device_manager
        self._processor = None
        self._input_device_index = None
        self._output_device_index = None
        self._enabled = False
        self._running = False

        # Audio streams
        self._input_stream = None
        self._output_stream = None

        # Ring buffers for lock-free audio transfer
        buffer_size = self.SAMPLE_RATE * self.BUFFER_SECONDS
        self._input_ring = RingBuffer(capacity=buffer_size)
        self._output_ring = RingBuffer(capacity=buffer_size)

        # Level meters for UI visualization
        self.input_meter = LevelMeter()
        self.output_meter = LevelMeter()

        # Processing thread
        self._processing_thread = None

        # Error tracking
        self._last_error = None
        self._underrun_count = 0

    def set_processor(self, processor):
        self._processor = processor

    def set_input_device(self, device_index):
        self._input_device_index = device_index
        if self._running:
            self._restart_streams()

    def set_output_device(self, device_index):
        self._output_device_index = device_index
        if self._running:
            self._restart_streams()

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value
        if not value and self._processor:
            self._processor.reset()

    @property
    def last_error(self):
        return self._last_error

    def start(self):
        """Start the audio pipeline."""
        if self._running:
            return

        self._running = True
        self._input_ring.clear()
        self._output_ring.clear()
        self.input_meter.reset()
        self.output_meter.reset()

        self._start_streams()

        self._processing_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True,
            name="NoiseClear-Processing",
        )
        self._processing_thread.start()

    def stop(self):
        """Stop all audio streams and processing."""
        self._running = False
        if self._processing_thread:
            self._processing_thread.join(timeout=2.0)
            self._processing_thread = None
        self._stop_streams()

    def _input_callback(self, indata, frames, time_info, status):
        """PortAudio input callback - runs in real-time thread.
        No blocking, no memory allocation, no locks allowed.
        """
        if status:
            self._last_error = f"Input: {status}"
        mono = indata[:, 0] if indata.ndim > 1 else indata.flatten()
        self._input_ring.write(mono)

    def _output_callback(self, outdata, frames, time_info, status):
        """PortAudio output callback - runs in real-time thread.
        No blocking, no memory allocation, no locks allowed.
        """
        if status:
            self._underrun_count += 1
        available = self._output_ring.available_read()
        if available >= frames:
            data = self._output_ring.read(frames)
            outdata[:, 0] = data
        else:
            # Underrun: output silence
            outdata.fill(0)

    def _processing_loop(self):
        """Main processing loop - runs in dedicated thread.
        Reads from input ring, processes through noise cancellation,
        writes to output ring.
        """
        # Set thread priority high on Windows
        try:
            import ctypes
            handle = ctypes.windll.kernel32.GetCurrentThread()
            ctypes.windll.kernel32.SetThreadPriority(handle, 2)  # ABOVE_NORMAL
        except Exception:
            pass

        while self._running:
            if self._input_ring.available_read() >= self.FRAME_SIZE:
                frame = self._input_ring.read(self.FRAME_SIZE)
                self.input_meter.update(frame)

                if self._enabled and self._processor:
                    try:
                        processed = self._processor.process_frame(frame)
                    except Exception as e:
                        self._last_error = f"Processing: {e}"
                        processed = frame
                else:
                    processed = frame  # Passthrough when disabled

                self.output_meter.update(processed)
                self._output_ring.write(processed)
            else:
                time.sleep(0.001)  # 1ms sleep to avoid busy-wait

    def _start_streams(self):
        """Start input and output audio streams."""
        self._last_error = None

        try:
            if self._input_device_index is not None:
                self._input_stream = sd.InputStream(
                    device=self._input_device_index,
                    samplerate=self.SAMPLE_RATE,
                    blocksize=self.FRAME_SIZE,
                    channels=self.CHANNELS,
                    dtype="float32",
                    callback=self._input_callback,
                    latency="low",
                )
                self._input_stream.start()
        except Exception as e:
            self._last_error = f"Input stream error: {e}"

        try:
            if self._output_device_index is not None:
                self._output_stream = sd.OutputStream(
                    device=self._output_device_index,
                    samplerate=self.SAMPLE_RATE,
                    blocksize=self.FRAME_SIZE,
                    channels=self.CHANNELS,
                    dtype="float32",
                    callback=self._output_callback,
                    latency="low",
                )
                self._output_stream.start()
        except Exception as e:
            self._last_error = f"Output stream error: {e}"

    def _stop_streams(self):
        """Stop and close audio streams."""
        if self._input_stream is not None:
            try:
                self._input_stream.stop()
                self._input_stream.close()
            except Exception:
                pass
            self._input_stream = None

        if self._output_stream is not None:
            try:
                self._output_stream.stop()
                self._output_stream.close()
            except Exception:
                pass
            self._output_stream = None

    def _restart_streams(self):
        """Restart streams after device change."""
        self._stop_streams()
        self._input_ring.clear()
        self._output_ring.clear()
        self._start_streams()
