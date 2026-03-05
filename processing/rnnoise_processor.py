"""Noise cancellation using RNNoise via pyrnnoise (optional, lightweight)."""

import numpy as np
from processing.base_processor import NoiseProcessor


class RNNoiseProcessor(NoiseProcessor):
    """Uses RNNoise neural network for lightweight noise suppression.

    RNNoise operates on exactly 480-sample frames at 48kHz (10ms),
    which aligns perfectly with our pipeline frame size.
    Requires: pip install pyrnnoise
    """

    def __init__(self):
        self._denoiser = None
        self._sample_rate = 48000
        self._frame_size = 480
        self._strength = 0.7

    def initialize(self, sample_rate, frame_size):
        from pyrnnoise import RNNoise

        self._sample_rate = sample_rate
        self._frame_size = frame_size
        self._denoiser = RNNoise()

    def process_frame(self, audio_frame):
        if self._denoiser is None:
            return audio_frame

        # pyrnnoise expects int16 PCM frames of exactly 480 samples
        frame_int16 = (audio_frame * 32767).astype(np.int16)

        # Process in 480-sample chunks
        output = np.zeros_like(audio_frame)
        pos = 0
        while pos + 480 <= len(frame_int16):
            chunk = frame_int16[pos:pos + 480]
            denoised_bytes = self._denoiser.process_frame(chunk.tobytes())
            denoised = np.frombuffer(denoised_bytes, dtype=np.int16).astype(np.float32) / 32767.0
            output[pos:pos + 480] = denoised
            pos += 480

        # Blend with original based on strength
        result = audio_frame * (1 - self._strength) + output * self._strength
        return result.astype(np.float32)

    def set_strength(self, strength):
        self._strength = max(0.0, min(1.0, strength))

    def reset(self):
        if self._denoiser is not None:
            from pyrnnoise import RNNoise
            self._denoiser = RNNoise()

    @property
    def name(self):
        return "RNNoise"
