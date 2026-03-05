"""Custom vertical audio level meter widget with gradient coloring."""

import tkinter as tk
from ui.theme import COLORS


class LevelMeterWidget(tk.Canvas):
    """Vertical audio level meter with green/yellow/red gradient.

    Visual design:
    - Dark background bar
    - Green fill from bottom to -12dB
    - Yellow fill from -12dB to -3dB
    - Red fill above -3dB
    - Thin peak hold indicator line
    """

    def __init__(self, parent, width=24, height=140, **kwargs):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=COLORS["bg_primary"],
            highlightthickness=0,
            **kwargs,
        )
        self._width = width
        self._height = height
        self._level = 0.0
        self._peak = 0.0
        self._draw_empty()

    def _draw_empty(self):
        """Draw the empty meter background."""
        self.delete("all")
        pad = 2
        self.create_rectangle(
            pad, pad, self._width - pad, self._height - pad,
            fill=COLORS["meter_bg"],
            outline=COLORS["border"],
            width=1,
        )

    def set_level(self, rms_db, peak_db):
        """Update the meter display. Values in dBFS (-60 to 0 range)."""
        # Map dB to 0-1 range (clamp -60 to 0)
        self._level = max(0.0, min(1.0, (rms_db + 60) / 60))
        self._peak = max(0.0, min(1.0, (peak_db + 60) / 60))
        self._redraw()

    def _redraw(self):
        self.delete("all")
        pad = 3
        bar_x0 = pad
        bar_x1 = self._width - pad
        bar_y0 = pad
        bar_y1 = self._height - pad
        bar_height = bar_y1 - bar_y0

        # Background
        self.create_rectangle(
            bar_x0, bar_y0, bar_x1, bar_y1,
            fill=COLORS["meter_bg"],
            outline=COLORS["border"],
            width=1,
        )

        if self._level <= 0:
            return

        # Fill height from bottom
        fill_height = self._level * bar_height
        fill_y = bar_y1 - fill_height

        # Thresholds (as fraction of total height)
        yellow_threshold = 0.6   # -12dB region
        red_threshold = 0.85     # -3dB region

        # Draw segments
        segments = []
        if self._level <= yellow_threshold:
            segments.append((fill_y, bar_y1, COLORS["meter_green"]))
        elif self._level <= red_threshold:
            yellow_y = bar_y1 - yellow_threshold * bar_height
            segments.append((yellow_y, bar_y1, COLORS["meter_green"]))
            segments.append((fill_y, yellow_y, COLORS["meter_yellow"]))
        else:
            yellow_y = bar_y1 - yellow_threshold * bar_height
            red_y = bar_y1 - red_threshold * bar_height
            segments.append((yellow_y, bar_y1, COLORS["meter_green"]))
            segments.append((red_y, yellow_y, COLORS["meter_yellow"]))
            segments.append((fill_y, red_y, COLORS["meter_red"]))

        inner_pad = pad + 1
        for y0, y1, color in segments:
            self.create_rectangle(
                inner_pad, max(y0, bar_y0 + 1),
                bar_x1 - 1, min(y1, bar_y1 - 1),
                fill=color, outline="",
            )

        # Peak hold indicator
        if self._peak > 0.01:
            peak_y = bar_y1 - self._peak * bar_height
            self.create_line(
                inner_pad, peak_y, bar_x1 - 1, peak_y,
                fill=COLORS["text_primary"], width=1,
            )
