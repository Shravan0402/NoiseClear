"""RMS and peak level calculation for audio visualization."""

import numpy as np


class LevelMeter:
    """Calculates smoothed RMS and peak levels for UI meters."""

    def __init__(self, decay_rate=0.93):
        self._rms = 0.0
        self._peak = 0.0
        self._decay = decay_rate

    def update(self, audio_frame):
        """Update levels from an audio frame (float32, -1 to 1)."""
        if len(audio_frame) == 0:
            return
        rms = float(np.sqrt(np.mean(audio_frame ** 2)))
        peak = float(np.max(np.abs(audio_frame)))
        self._rms = max(rms, self._rms * self._decay)
        self._peak = max(peak, self._peak * self._decay)

    @property
    def rms_db(self):
        """RMS level in dBFS (-60 to 0)."""
        return 20 * np.log10(max(self._rms, 1e-10))

    @property
    def peak_db(self):
        """Peak level in dBFS (-60 to 0)."""
        return 20 * np.log10(max(self._peak, 1e-10))

    @property
    def rms_linear(self):
        """RMS level as linear 0-1 value."""
        return min(self._rms, 1.0)

    @property
    def peak_linear(self):
        """Peak level as linear 0-1 value."""
        return min(self._peak, 1.0)

    def reset(self):
        self._rms = 0.0
        self._peak = 0.0
