"""JSON-based settings persistence for NoiseClear."""

import json
from pathlib import Path


class Settings:
    """Persists user preferences to %APPDATA%/NoiseClear/settings.json."""

    DEFAULT_PATH = Path.home() / "AppData" / "Roaming" / "NoiseClear" / "settings.json"

    DEFAULTS = {
        "input_device_name": None,
        "output_device_name": None,
        "noise_reduction_strength": 0.7,
        "noise_cancellation_enabled": True,
        "engine": "spectral_gate",
        "start_minimized": False,
        "minimize_to_tray_on_close": True,
        "sample_rate": 48000,
        "frame_size": 480,
    }

    def __init__(self, path=None):
        self._path = Path(path) if path else self.DEFAULT_PATH
        self._data = dict(self.DEFAULTS)
        self.load()

    def load(self):
        if self._path.exists():
            try:
                with open(self._path, "r") as f:
                    saved = json.load(f)
                self._data.update(saved)
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)

    def get(self, key):
        return self._data.get(key, self.DEFAULTS.get(key))

    def set(self, key, value):
        self._data[key] = value
        self.save()
