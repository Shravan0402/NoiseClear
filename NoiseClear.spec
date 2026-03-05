# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for NoiseClear."""

import os
import sys

block_cipher = None

# Get paths
project_dir = os.path.dirname(os.path.abspath(SPECPATH))

# Find customtkinter package location for bundling its assets
import customtkinter
ctk_path = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ['main.py'],
    pathex=[project_dir],
    binaries=[],
    datas=[
        ('icon.ico', '.'),
        ('icon.png', '.'),
        (ctk_path, 'customtkinter'),
    ],
    hiddenimports=[
        'config',
        'config.settings',
        'audio',
        'audio.ring_buffer',
        'audio.level_meter',
        'audio.device_manager',
        'audio.audio_pipeline',
        'processing',
        'processing.base_processor',
        'processing.spectral_gate_processor',
        'processing.processor_factory',
        'ui',
        'ui.theme',
        'ui.level_meter_widget',
        'ui.main_panel',
        'ui.device_selector',
        'ui.tray_icon',
        'ui.app_window',
        'noisereduce',
        'scipy.signal',
        'scipy.fft',
        'scipy._lib.messagestream',
        'pystray._win32',
        'PIL._tkinter_finder',
        'sounddevice',
        'numpy',
        'joblib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'torch',
        'torchaudio',
        'df',
        'pyrnnoise',
        'pytest',
        'IPython',
        'notebook',
        'sphinx',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NoiseClear',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window - GUI only
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NoiseClear',
)
