"""Noise cancellation using noisereduce spectral gating."""

import collections
import numpy as np
from processing.base_processor import NoiseProcessor


class SpectralGateProcessor(NoiseProcessor):
    """Uses noisereduce library with non-stationary spectral gating.

    Accumulates audio into chunks (100ms) before processing to give the
    spectral gate enough context. Uses overlap-add with Hann windowing
    at chunk boundaries to prevent clicks/artifacts.
    """

    def __init__(self):
        self._sample_rate = 48000
        self._frame_size = 480
        self._strength = 0.7
        self._accumulator = np.array([], dtype=np.float32)
        self._chunk_size = 4800  # 100ms at 48kHz
        self._overlap = 960     # 20ms overlap
        self._output_buffer = collections.deque()
        self._prev_tail = None  # For overlap-add crossfade
        self._window = None

    def initialize(self, sample_rate, frame_size):
        self._sample_rate = sample_rate
        self._frame_size = frame_size
        self._chunk_size = int(sample_rate * 0.1)  # 100ms
        self._overlap = int(sample_rate * 0.02)    # 20ms
        self._window = np.hanning(self._overlap * 2).astype(np.float32)
        self.reset()

    def process_frame(self, audio_frame):
        """Accumulate frames, process when enough context, return denoised frames."""
        self._accumulator = np.concatenate([self._accumulator, audio_frame])

        # Process when we have enough accumulated audio
        while len(self._accumulator) >= self._chunk_size:
            chunk = self._accumulator[:self._chunk_size]
            self._accumulator = self._accumulator[self._chunk_size - self._overlap:]

            # Apply noise reduction
            denoised = self._denoise_chunk(chunk)

            # Overlap-add crossfade with previous chunk
            if self._prev_tail is not None and len(denoised) >= self._overlap:
                fade_out = self._window[self._overlap:]  # second half = fade out
                fade_in = self._window[:self._overlap]   # first half = fade in
                denoised[:self._overlap] = (
                    self._prev_tail * fade_out + denoised[:self._overlap] * fade_in
                )
                # Queue the main body (excluding overlap region for next crossfade)
                output_samples = denoised[:len(denoised) - self._overlap]
            else:
                output_samples = denoised[:len(denoised) - self._overlap]

            # Save tail for next crossfade
            self._prev_tail = denoised[len(denoised) - self._overlap:].copy()

            # Add processed samples to output buffer
            for sample in output_samples:
                self._output_buffer.append(sample)

        # Return a frame-sized chunk from output buffer
        if len(self._output_buffer) >= self._frame_size:
            result = np.array(
                [self._output_buffer.popleft() for _ in range(self._frame_size)],
                dtype=np.float32,
            )
            return result
        else:
            # Not enough processed data yet, return silence
            return np.zeros(self._frame_size, dtype=np.float32)

    def _denoise_chunk(self, chunk):
        """Apply noisereduce to a chunk of audio."""
        import noisereduce as nr

        # Map strength (0-1) to prop_decrease and threshold
        prop_decrease = 0.5 + self._strength * 0.5  # 0.5 to 1.0
        n_std = 2.5 - self._strength * 1.5          # 2.5 to 1.0

        try:
            denoised = nr.reduce_noise(
                y=chunk,
                sr=self._sample_rate,
                stationary=False,
                prop_decrease=prop_decrease,
                n_std_thresh_stationary=n_std,
                n_fft=512,
                hop_length=128,
                time_mask_smooth_ms=50,
                freq_mask_smooth_hz=500,
            )
            return denoised.astype(np.float32)
        except Exception:
            return chunk

    def set_strength(self, strength):
        self._strength = max(0.0, min(1.0, strength))

    def reset(self):
        self._accumulator = np.array([], dtype=np.float32)
        self._output_buffer.clear()
        self._prev_tail = None

    @property
    def name(self):
        return "Spectral Gate"
