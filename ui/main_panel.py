"""Main panel with toggle button, level meters, and controls."""

import customtkinter as ctk
from ui.theme import COLORS, FONTS
from ui.level_meter_widget import LevelMeterWidget


class MainPanel(ctk.CTkFrame):
    """Central panel: big toggle button, status, level meters, strength slider."""

    def __init__(self, parent, pipeline, settings, on_engine_change=None):
        super().__init__(parent, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=20, pady=(10, 5))

        self._pipeline = pipeline
        self._settings = settings
        self._on_engine_change = on_engine_change

        # --- App Title ---
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(pady=(5, 15))

        title = ctk.CTkLabel(
            title_frame, text="NoiseClear",
            font=FONTS["title"], text_color=COLORS["accent_blue"],
        )
        title.pack()

        subtitle = ctk.CTkLabel(
            title_frame, text="Real-Time Noise Cancellation",
            font=FONTS["caption"], text_color=COLORS["text_muted"],
        )
        subtitle.pack()

        # --- Big Toggle Button ---
        self._active = self._settings.get("noise_cancellation_enabled")
        self._pipeline.enabled = self._active

        btn_color = COLORS["accent_active"] if self._active else COLORS["accent_inactive"]
        self._toggle_btn = ctk.CTkButton(
            self,
            text="ON" if self._active else "OFF",
            font=("Segoe UI", 28, "bold"),
            fg_color=btn_color,
            hover_color=COLORS["accent_hover"] if self._active else "#666666",
            width=120, height=120,
            corner_radius=60,
            command=self._toggle,
        )
        self._toggle_btn.pack(pady=(5, 8))

        # --- Status Label ---
        status_text = "Noise Cancellation Active" if self._active else "Noise Cancellation Off"
        self._status_label = ctk.CTkLabel(
            self, text=status_text,
            font=FONTS["status_bold"],
            text_color=COLORS["accent_active"] if self._active else COLORS["text_muted"],
        )
        self._status_label.pack(pady=(0, 12))

        # --- Level Meters ---
        meter_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        meter_frame.pack(fill="x", pady=(0, 10))

        meter_inner = ctk.CTkFrame(meter_frame, fg_color="transparent")
        meter_inner.pack(pady=12, padx=20)

        # Input meter
        input_col = ctk.CTkFrame(meter_inner, fg_color="transparent")
        input_col.pack(side="left", padx=(20, 40))

        ctk.CTkLabel(
            input_col, text="INPUT",
            font=FONTS["caption"], text_color=COLORS["text_secondary"],
        ).pack(pady=(0, 4))

        self._input_meter = LevelMeterWidget(input_col, width=28, height=120)
        self._input_meter.pack()

        self._input_db_label = ctk.CTkLabel(
            input_col, text="-60 dB",
            font=FONTS["caption"], text_color=COLORS["text_muted"],
        )
        self._input_db_label.pack(pady=(4, 0))

        # Output meter
        output_col = ctk.CTkFrame(meter_inner, fg_color="transparent")
        output_col.pack(side="left", padx=(40, 20))

        ctk.CTkLabel(
            output_col, text="OUTPUT",
            font=FONTS["caption"], text_color=COLORS["text_secondary"],
        ).pack(pady=(0, 4))

        self._output_meter = LevelMeterWidget(output_col, width=28, height=120)
        self._output_meter.pack()

        self._output_db_label = ctk.CTkLabel(
            output_col, text="-60 dB",
            font=FONTS["caption"], text_color=COLORS["text_muted"],
        )
        self._output_db_label.pack(pady=(4, 0))

        # --- Noise Reduction Strength ---
        strength_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
        strength_frame.pack(fill="x", pady=(0, 10))

        strength_header = ctk.CTkFrame(strength_frame, fg_color="transparent")
        strength_header.pack(fill="x", padx=15, pady=(10, 2))

        ctk.CTkLabel(
            strength_header, text="Noise Reduction",
            font=FONTS["body"], text_color=COLORS["text_secondary"],
        ).pack(side="left")

        initial_strength = self._settings.get("noise_reduction_strength")
        self._strength_value_label = ctk.CTkLabel(
            strength_header, text=f"{int(initial_strength * 100)}%",
            font=FONTS["status_bold"], text_color=COLORS["accent_blue"],
        )
        self._strength_value_label.pack(side="right")

        self._strength_slider = ctk.CTkSlider(
            strength_frame,
            from_=0, to=1,
            number_of_steps=20,
            command=self._on_strength_changed,
            fg_color=COLORS["slider_track"],
            progress_color=COLORS["accent_blue"],
            button_color=COLORS["accent_blue"],
            button_hover_color=COLORS["text_primary"],
            width=280,
        )
        self._strength_slider.set(initial_strength)
        self._strength_slider.pack(padx=15, pady=(2, 12))

        # --- Engine Selector ---
        from processing.processor_factory import ProcessorFactory
        available = ProcessorFactory.get_available_engines()
        display_names = ProcessorFactory.get_engine_display_names()

        if len(available) > 1:
            engine_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12)
            engine_frame.pack(fill="x", pady=(0, 5))

            ctk.CTkLabel(
                engine_frame, text="Engine",
                font=FONTS["caption"], text_color=COLORS["text_secondary"],
            ).pack(anchor="w", padx=15, pady=(10, 4))

            engine_values = [display_names.get(e, e) for e in available]
            current_engine = self._settings.get("engine")
            current_display = display_names.get(current_engine, engine_values[0])

            self._engine_var = ctk.StringVar(value=current_display)
            engine_menu = ctk.CTkOptionMenu(
                engine_frame,
                variable=self._engine_var,
                values=engine_values,
                command=self._on_engine_changed,
                font=FONTS["body"],
                fg_color=COLORS["bg_secondary"],
                button_color=COLORS["accent_blue"],
                width=280,
            )
            engine_menu.pack(padx=15, pady=(0, 12))

            self._engine_id_map = {display_names.get(e, e): e for e in available}

    def _toggle(self):
        self._active = not self._active
        self._pipeline.enabled = self._active
        self._settings.set("noise_cancellation_enabled", self._active)

        if self._active:
            self._toggle_btn.configure(
                text="ON",
                fg_color=COLORS["accent_active"],
                hover_color=COLORS["accent_hover"],
            )
            self._status_label.configure(
                text="Noise Cancellation Active",
                text_color=COLORS["accent_active"],
            )
        else:
            self._toggle_btn.configure(
                text="OFF",
                fg_color=COLORS["accent_inactive"],
                hover_color="#666666",
            )
            self._status_label.configure(
                text="Noise Cancellation Off",
                text_color=COLORS["text_muted"],
            )

    def _on_strength_changed(self, value):
        self._strength_value_label.configure(text=f"{int(value * 100)}%")
        self._settings.set("noise_reduction_strength", value)
        if self._pipeline._processor:
            self._pipeline._processor.set_strength(value)

    def _on_engine_changed(self, display_name):
        engine_id = self._engine_id_map.get(display_name)
        if engine_id and self._on_engine_change:
            self._on_engine_change(engine_id)

    def update_levels(self, input_meter, output_meter):
        """Update level meter displays (called from UI timer)."""
        in_rms = input_meter.rms_db
        in_peak = input_meter.peak_db
        out_rms = output_meter.rms_db
        out_peak = output_meter.peak_db

        self._input_meter.set_level(in_rms, in_peak)
        self._output_meter.set_level(out_rms, out_peak)

        self._input_db_label.configure(text=f"{max(in_rms, -60):.0f} dB")
        self._output_db_label.configure(text=f"{max(out_rms, -60):.0f} dB")

    def set_active(self, active):
        """Set toggle state programmatically (from tray icon)."""
        if active != self._active:
            self._toggle()
