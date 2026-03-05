"""Noise cancellation using DeepFilterNet (optional, requires PyTorch)."""

import numpy as np
from processing.base_processor import NoiseProcessor


class DeepFilterProcessor(NoiseProcessor):
    """Uses DeepFilterNet for high-quality neural noise suppression.

    The df_state object is stateful - it retains STFT overlap buffers and
    RNN hidden states between calls, enabling true streaming processing.
    Requires: pip install torch torchaudio deepfilternet
    """

    def __init__(self):
        self._model = None
        self._df_state = None
        self._sample_rate = 48000
        self._frame_size = 480
        self._strength = 0.7
        self._accumulator = np.array([], dtype=np.float32)
        self._process_size = 4800  # 100ms chunks for DeepFilterNet

    def initialize(self, sample_rate, frame_size):
        from df.enhance import init_df

        self._sample_rate = sample_rate
        self._frame_size = frame_size
        self._model, self._df_state, _ = init_df()
        self.reset()

    def process_frame(self, audio_frame):
        import torch
        from df.enhance import enhance

        self._accumulator = np.concatenate([self._accumulator, audio_frame])

        if len(self._accumulator) >= self._process_size:
            chunk = self._accumulator[:self._process_size]
            self._accumulator = self._accumulator[self._process_size:]

            audio_tensor = torch.from_numpy(chunk).unsqueeze(0).unsqueeze(0).float()
            enhanced = enhance(self._model, self._df_state, audio_tensor)
            result = enhanced.squeeze().numpy().astype(np.float32)

            # Blend with original based on strength
            blended = audio_frame * (1 - self._strength) + result[:self._frame_size] * self._strength
            return blended

        return audio_frame.copy()

    def set_strength(self, strength):
        self._strength = max(0.0, min(1.0, strength))

    def reset(self):
        self._accumulator = np.array([], dtype=np.float32)

    @property
    def name(self):
        return "DeepFilter"
