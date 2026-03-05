"""Input/output device dropdown selectors."""

import customtkinter as ctk
from ui.theme import COLORS, FONTS


class DeviceSelector(ctk.CTkFrame):
    """Dropdown selectors for input microphone and output device."""

    def __init__(self, parent, device_manager, pipeline, settings):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=12)
        self.pack(fill="x", padx=20, pady=(5, 10))

        self._device_manager = device_manager
        self._pipeline = pipeline
        self._settings = settings

        self._input_devices = []
        self._output_devices = []

        # --- Input Device ---
        input_label = ctk.CTkLabel(
            self, text="Input Microphone",
            font=FONTS["caption"], text_color=COLORS["text_secondary"],
        )
        input_label.pack(anchor="w", padx=15, pady=(12, 2))

        self._input_var = ctk.StringVar(value="Select microphone...")
        self._input_dropdown = ctk.CTkOptionMenu(
            self,
            variable=self._input_var,
            values=["Loading..."],
            command=self._on_input_changed,
            font=FONTS["body"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent_blue"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_secondary"],
            dropdown_hover_color=COLORS["bg_tertiary"],
            width=310,
        )
        self._input_dropdown.pack(padx=15, pady=(2, 8))

        # --- Output Device ---
        output_label = ctk.CTkLabel(
            self, text="Output Device (Virtual Cable)",
            font=FONTS["caption"], text_color=COLORS["text_secondary"],
        )
        output_label.pack(anchor="w", padx=15, pady=(4, 2))

        self._output_var = ctk.StringVar(value="Select output...")
        self._output_dropdown = ctk.CTkOptionMenu(
            self,
            variable=self._output_var,
            values=["Loading..."],
            command=self._on_output_changed,
            font=FONTS["body"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["accent_blue"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_secondary"],
            dropdown_hover_color=COLORS["bg_tertiary"],
            width=310,
        )
        self._output_dropdown.pack(padx=15, pady=(2, 4))

        # --- VB-CABLE warning ---
        self._warning_label = ctk.CTkLabel(
            self, text="",
            font=FONTS["caption"], text_color=COLORS["warning"],
        )
        self._warning_label.pack(padx=15, pady=(0, 4))

        # --- Refresh button ---
        refresh_btn = ctk.CTkButton(
            self, text="Refresh Devices",
            font=FONTS["caption"],
            fg_color=COLORS["bg_secondary"],
            hover_color=COLORS["bg_tertiary"],
            width=120, height=28,
            command=self._refresh_devices,
        )
        refresh_btn.pack(pady=(2, 12))

        # Initial populate
        self._refresh_devices()

    def _refresh_devices(self):
        self._device_manager.refresh_devices()
        self._populate_dropdowns()

    def _populate_dropdowns(self):
        # Input devices
        self._input_devices = self._device_manager.get_input_devices()
        input_names = [name for _, name in self._input_devices]
        if input_names:
            self._input_dropdown.configure(values=input_names)
            # Restore saved selection
            saved_input = self._settings.get("input_device_name")
            if saved_input and saved_input in input_names:
                self._input_var.set(saved_input)
                self._on_input_changed(saved_input)
            else:
                self._input_var.set(input_names[0])
                self._on_input_changed(input_names[0])
        else:
            self._input_dropdown.configure(values=["No input devices found"])

        # Output devices
        self._output_devices = self._device_manager.get_output_devices()
        output_names = [name for _, name in self._output_devices]
        if output_names:
            self._output_dropdown.configure(values=output_names)
            # Try to auto-select virtual cable (VB-CABLE, VoiceMeeter, etc.)
            saved_output = self._settings.get("output_device_name")
            vcable_idx = self._device_manager.find_virtual_cable_output()

            if saved_output and saved_output in output_names:
                self._output_var.set(saved_output)
                self._on_output_changed(saved_output)
                self._warning_label.configure(text="")
            elif vcable_idx is not None:
                vb_name = self._device_manager.get_device_name(vcable_idx)
                if vb_name in output_names:
                    self._output_var.set(vb_name)
                    self._on_output_changed(vb_name)
                    self._warning_label.configure(
                        text=f"Auto-detected: {vb_name}"
                    )
            else:
                self._output_var.set(output_names[0])
                self._on_output_changed(output_names[0])
                self._warning_label.configure(
                    text="No virtual cable detected! Install VB-CABLE from vb-audio.com/Cable"
                )
        else:
            self._output_dropdown.configure(values=["No output devices found"])

    def _on_input_changed(self, selected_name):
        for idx, name in self._input_devices:
            if name == selected_name:
                self._pipeline.set_input_device(idx)
                self._settings.set("input_device_name", name)
                break

    def _on_output_changed(self, selected_name):
        for idx, name in self._output_devices:
            if name == selected_name:
                self._pipeline.set_output_device(idx)
                self._settings.set("output_device_name", name)
                # Clear warning if VB-CABLE selected
                if "CABLE" in name:
                    self._warning_label.configure(text="")
                break
