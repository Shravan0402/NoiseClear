"""Audio device enumeration and monitoring."""

import threading
import sounddevice as sd


class DeviceManager:
    """Manages audio device discovery, VB-CABLE detection, and change monitoring."""

    def __init__(self):
        self._devices = []
        self._on_change_callbacks = []
        self._monitor_thread = None
        self._monitoring = False
        self._last_device_hash = None
        self.refresh_devices()

    def refresh_devices(self):
        """Re-query all audio devices from PortAudio."""
        sd._terminate()
        sd._initialize()
        self._devices = sd.query_devices()

    def get_input_devices(self):
        """Return list of (index, name) for input-capable devices."""
        results = []
        for i, d in enumerate(self._devices):
            if d["max_input_channels"] > 0:
                results.append((i, d["name"]))
        return results

    def get_output_devices(self):
        """Return list of (index, name) for output-capable devices."""
        results = []
        for i, d in enumerate(self._devices):
            if d["max_output_channels"] > 0:
                results.append((i, d["name"]))
        return results

    def find_virtual_cable_output(self):
        """Find a virtual audio cable output device (our app writes to this).

        Supports:
        - VB-CABLE: 'CABLE Input' = output device (we write here)
        - VoiceMeeter: 'VoiceMeeter Input' = output device (we write here)
        - Intelligo VAC: 'Line Out 1 (Intelligo' = output device

        In all cases, the companion input device appears as a microphone
        in other apps (Zoom, Discord, etc.).
        """
        # Priority order: VB-CABLE first, then VoiceMeeter, then others
        candidates = [
            "CABLE Input",
            "VoiceMeeter Input",
            "Line Out 1 (Intelligo",
        ]
        for keyword in candidates:
            for i, d in enumerate(self._devices):
                if keyword in d["name"] and d["max_output_channels"] > 0:
                    return i
        return None

    # Keep backward compat alias
    def find_vb_cable_input(self):
        return self.find_virtual_cable_output()

    def get_device_name(self, index):
        """Get device name by index."""
        if 0 <= index < len(self._devices):
            return self._devices[index]["name"]
        return None

    def find_device_by_name(self, name, is_input=True):
        """Find device index by name. Returns None if not found."""
        if name is None:
            return None
        for i, d in enumerate(self._devices):
            if name in d["name"]:
                if is_input and d["max_input_channels"] > 0:
                    return i
                elif not is_input and d["max_output_channels"] > 0:
                    return i
        return None

    def _device_hash(self):
        """Create a hash of current device list for change detection."""
        names = tuple(d["name"] for d in self._devices)
        return hash(names)

    def start_monitoring(self, interval_sec=2.0, on_change=None):
        """Start polling for device changes in a background thread."""
        if on_change:
            self._on_change_callbacks.append(on_change)
        self._last_device_hash = self._device_hash()
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval_sec,),
            daemon=True,
        )
        self._monitor_thread.start()

    def stop_monitoring(self):
        self._monitoring = False

    def _monitor_loop(self, interval):
        import time
        while self._monitoring:
            time.sleep(interval)
            try:
                self.refresh_devices()
                current_hash = self._device_hash()
                if current_hash != self._last_device_hash:
                    self._last_device_hash = current_hash
                    for cb in self._on_change_callbacks:
                        cb()
            except Exception:
                pass

    def on_device_change(self, callback):
        self._on_change_callbacks.append(callback)
