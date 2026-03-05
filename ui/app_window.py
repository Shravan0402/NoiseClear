"""Main application window."""

import customtkinter as ctk
from ui.theme import COLORS
from ui.main_panel import MainPanel
from ui.device_selector import DeviceSelector
from ui.tray_icon import TrayIcon


class AppWindow(ctk.CTk):
    """Root NoiseClear window. Coordinates UI, pipeline, and system tray."""

    def __init__(self, pipeline, device_manager, settings, on_engine_change=None):
        super().__init__()

        self._pipeline = pipeline
        self._device_manager = device_manager
        self._settings = settings
        self._quitting = False

        # Window configuration
        self.title("NoiseClear")
        self.geometry("400x720")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_primary"])

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Try to set window icon
        try:
            self.iconbitmap(default="icon.ico")
        except Exception:
            pass

        # Build UI
        self._main_panel = MainPanel(
            self, pipeline, settings,
            on_engine_change=on_engine_change,
        )
        self._device_selector = DeviceSelector(
            self, device_manager, pipeline, settings,
        )

        # Error display at bottom
        self._error_label = ctk.CTkLabel(
            self, text="",
            font=("Segoe UI", 10),
            text_color=COLORS["warning"],
        )
        self._error_label.pack(pady=(0, 5))

        # System tray
        self._tray = TrayIcon(self)

        # Window close behavior
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Start periodic UI updates (~30fps)
        self._update_meters()

        # Monitor for device changes
        self._device_manager.start_monitoring(
            interval_sec=2.0,
            on_change=lambda: self.after(0, self._device_selector._refresh_devices),
        )

    def _update_meters(self):
        """Periodic timer to update level meters and error display."""
        if self._quitting:
            return
        self._main_panel.update_levels(
            self._pipeline.input_meter,
            self._pipeline.output_meter,
        )

        # Show pipeline errors
        error = self._pipeline.last_error
        if error:
            self._error_label.configure(text=f"Warning: {error}")
        else:
            self._error_label.configure(text="")

        self.after(33, self._update_meters)

    def _on_close(self):
        """Minimize to tray on window close."""
        if self._settings.get("minimize_to_tray_on_close"):
            self._tray.minimize_to_tray()
        else:
            self._force_quit()

    def _force_quit(self):
        """Actually quit the application."""
        self._quitting = True
        self._device_manager.stop_monitoring()
        self._pipeline.stop()
        self._tray.stop()
        self._settings.save()
        self.quit()
        self.destroy()
