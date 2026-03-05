"""Abstract base class for noise cancellation engines."""

from abc import ABC, abstractmethod
import numpy as np


class NoiseProcessor(ABC):
    """Interface that all noise cancellation engines must implement."""

    @abstractmethod
    def initialize(self, sample_rate, frame_size):
        """Initialize the processor with audio parameters."""
        pass

    @abstractmethod
    def process_frame(self, audio_frame):
        """Process a single audio frame and return denoised audio.

        Args:
            audio_frame: float32 numpy array, shape (frame_size,), values in [-1, 1]
        Returns:
            Denoised float32 numpy array, same shape
        """
        pass

    @abstractmethod
    def set_strength(self, strength):
        """Set noise reduction strength (0.0 to 1.0)."""
        pass

    @abstractmethod
    def reset(self):
        """Reset internal state."""
        pass

    @property
    @abstractmethod
    def name(self):
        """Human-readable name of the engine."""
        pass
