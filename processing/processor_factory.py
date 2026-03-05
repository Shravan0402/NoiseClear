"""Factory for creating noise processor instances."""

from processing.spectral_gate_processor import SpectralGateProcessor


class ProcessorFactory:
    """Creates noise processor instances and detects available engines."""

    @staticmethod
    def get_available_engines():
        """Return list of engine names that can be instantiated."""
        available = ["spectral_gate"]

        try:
            import pyrnnoise  # noqa: F401
            available.append("rnnoise")
        except ImportError:
            pass

        try:
            import df  # noqa: F401
            available.append("deepfilter")
        except ImportError:
            pass

        return available

    @staticmethod
    def get_engine_display_names():
        """Return dict mapping engine id to display name."""
        return {
            "spectral_gate": "Spectral Gate",
            "rnnoise": "RNNoise",
            "deepfilter": "DeepFilter",
        }

    @staticmethod
    def create(engine_name):
        """Create a noise processor by engine name."""
        if engine_name == "spectral_gate":
            return SpectralGateProcessor()
        elif engine_name == "deepfilter":
            from processing.deepfilter_processor import DeepFilterProcessor
            return DeepFilterProcessor()
        elif engine_name == "rnnoise":
            from processing.rnnoise_processor import RNNoiseProcessor
            return RNNoiseProcessor()
        raise ValueError(f"Unknown engine: {engine_name}")
