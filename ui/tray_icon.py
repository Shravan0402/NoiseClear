"""System tray integration using pystray."""

import threading
from PIL import Image, ImageDraw


class TrayIcon:
    """System tray icon with quick toggle and show/quit actions.

    Runs pystray in a daemon thread since customtkinter needs the main thread.
    """

    def __init__(self, app_window):
        self._app = app_window
        self._icon = None
        self._running = False

    def _create_icon_image(self, active=True):
        """Generate a simple mic icon programmatically."""
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        color = (46, 204, 113) if active else (85, 85, 85)

        # Mic body (rounded rectangle approximation)
        draw.rounded_rectangle(
            [20, 8, 44, 38], radius=10, fill=color,
        )

        # Mic stand arc
        draw.arc([14, 20, 50, 48], start=0, end=180, fill=color, width=3)

        # Mic stand pole
        draw.line([32, 48, 32, 56], fill=color, width=3)

        # Base
        draw.line([22, 56, 42, 56], fill=color, width=3)

        return img

    def minimize_to_tray(self):
        """Hide window and show system tray icon."""
        import pystray

        self._app.withdraw()

        if self._icon is not None:
            return

        image = self._create_icon_image(self._app._pipeline.enabled)
        menu = pystray.Menu(
            pystray.MenuItem("Show NoiseClear", self._show_window, default=True),
            pystray.MenuItem(
                "Noise Cancellation",
                self._toggle_nc,
                checked=lambda item: self._app._pipeline.enabled,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit),
        )
        self._icon = pystray.Icon("NoiseClear", image, "NoiseClear", menu)
        self._running = True

        thread = threading.Thread(target=self._icon.run, daemon=True)
        thread.start()

    def _show_window(self, icon=None, item=None):
        if self._icon:
            self._icon.stop()
            self._icon = None
        self._app.after(0, self._app.deiconify)
        self._app.after(100, self._app.lift)

    def _toggle_nc(self, icon, item):
        self._app.after(0, self._app._main_panel.set_active,
                        not self._app._pipeline.enabled)
        # Update icon color
        self._app.after(200, self._update_icon)

    def _update_icon(self):
        if self._icon:
            self._icon.icon = self._create_icon_image(self._app._pipeline.enabled)

    def _quit(self, icon, item):
        self._running = False
        if self._icon:
            self._icon.stop()
            self._icon = None
        self._app.after(0, self._app._force_quit)

    def stop(self):
        self._running = False
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
