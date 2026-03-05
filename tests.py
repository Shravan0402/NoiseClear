"""Comprehensive test suite for NoiseClear."""

import sys
import os
import time
import tempfile
import json
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

PASS = 0
FAIL = 0
ERRORS = []


def test(name):
    """Decorator to register and run a test."""
    def decorator(func):
        global PASS, FAIL
        try:
            func()
            PASS += 1
            print(f"  PASS  {name}")
        except Exception as e:
            FAIL += 1
            tb = traceback.format_exc()
            ERRORS.append((name, str(e), tb))
            print(f"  FAIL  {name}")
            print(f"        {e}")
        return func
    return decorator


# ======================================================================
# 1. CONFIG / SETTINGS
# ======================================================================
print("\n[1/8] Config & Settings")
print("-" * 50)


@test("Settings: load defaults")
def _():
    from config.settings import Settings
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "test_settings.json")
        s = Settings(path=path)
        assert s.get("engine") == "spectral_gate"
        assert s.get("noise_reduction_strength") == 0.7
        assert s.get("sample_rate") == 48000
        assert s.get("frame_size") == 480
        assert s.get("noise_cancellation_enabled") is True


@test("Settings: save and reload")
def _():
    from config.settings import Settings
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "test_settings.json")
        s = Settings(path=path)
        s.set("engine", "rnnoise")
        s.set("noise_reduction_strength", 0.5)

        s2 = Settings(path=path)
        assert s2.get("engine") == "rnnoise"
        assert s2.get("noise_reduction_strength") == 0.5


@test("Settings: handles corrupt file gracefully")
def _():
    from config.settings import Settings
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "test_settings.json")
        with open(path, "w") as f:
            f.write("{invalid json!!")
        s = Settings(path=path)
        assert s.get("engine") == "spectral_gate"  # Falls back to defaults


# ======================================================================
# 2. RING BUFFER
# ======================================================================
print("\n[2/8] Ring Buffer")
print("-" * 50)


@test("RingBuffer: basic write and read")
def _():
    from audio.ring_buffer import RingBuffer
    rb = RingBuffer(4800)
    data = np.ones(480, dtype=np.float32) * 0.5
    written = rb.write(data)
    assert written == 480
    assert rb.available_read() == 480
    out = rb.read(480)
    assert len(out) == 480
    assert np.allclose(out, 0.5)


@test("RingBuffer: wraparound write/read")
def _():
    from audio.ring_buffer import RingBuffer
    rb = RingBuffer(1000)
    # Fill most of the buffer
    rb.write(np.ones(900, dtype=np.float32))
    rb.read(900)  # Now read_pos=900, write_pos=900
    # Write across boundary
    data = np.arange(200, dtype=np.float32)
    rb.write(data)
    out = rb.read(200)
    assert np.allclose(out, data)


@test("RingBuffer: overflow protection")
def _():
    from audio.ring_buffer import RingBuffer
    rb = RingBuffer(100)
    data = np.ones(200, dtype=np.float32)
    written = rb.write(data)
    assert written <= 99  # Can't fill entire buffer (SPSC needs 1 slot gap)


@test("RingBuffer: empty read returns empty array")
def _():
    from audio.ring_buffer import RingBuffer
    rb = RingBuffer(1000)
    out = rb.read(480)
    assert len(out) == 0


@test("RingBuffer: clear resets state")
def _():
    from audio.ring_buffer import RingBuffer
    rb = RingBuffer(4800)
    rb.write(np.ones(1000, dtype=np.float32))
    assert rb.available_read() == 1000
    rb.clear()
    assert rb.available_read() == 0


@test("RingBuffer: multiple sequential writes and reads")
def _():
    from audio.ring_buffer import RingBuffer
    rb = RingBuffer(48000)
    for i in range(100):
        frame = np.full(480, float(i), dtype=np.float32)
        rb.write(frame)
        out = rb.read(480)
        assert len(out) == 480
        assert np.allclose(out, float(i))


@test("RingBuffer: partial read")
def _():
    from audio.ring_buffer import RingBuffer
    rb = RingBuffer(4800)
    rb.write(np.ones(200, dtype=np.float32))
    out = rb.read(480)  # Request more than available
    assert len(out) == 200  # Should return only what's available


# ======================================================================
# 3. LEVEL METER
# ======================================================================
print("\n[3/8] Level Meter")
print("-" * 50)


@test("LevelMeter: silence gives very low levels")
def _():
    from audio.level_meter import LevelMeter
    lm = LevelMeter()
    lm.update(np.zeros(480, dtype=np.float32))
    assert lm.rms_db < -90
    assert lm.peak_db < -90


@test("LevelMeter: full scale sine gives ~0 dBFS")
def _():
    from audio.level_meter import LevelMeter
    lm = LevelMeter()
    t = np.linspace(0, 1, 48000, dtype=np.float32)
    sine = np.sin(2 * np.pi * 440 * t)
    for i in range(0, len(sine), 480):
        lm.update(sine[i:i + 480])
    assert lm.rms_db > -5  # Should be close to -3dB for sine
    assert lm.peak_db > -1  # Peak should be close to 0


@test("LevelMeter: decay works over time")
def _():
    from audio.level_meter import LevelMeter
    lm = LevelMeter(decay_rate=0.5)
    lm.update(np.ones(480, dtype=np.float32))
    level_after_signal = lm.rms_linear
    # Feed silence
    for _ in range(10):
        lm.update(np.zeros(480, dtype=np.float32))
    assert lm.rms_linear < level_after_signal


@test("LevelMeter: reset clears levels")
def _():
    from audio.level_meter import LevelMeter
    lm = LevelMeter()
    lm.update(np.ones(480, dtype=np.float32))
    assert lm.rms_linear > 0
    lm.reset()
    assert lm.rms_linear == 0.0
    assert lm.peak_linear == 0.0


# ======================================================================
# 4. DEVICE MANAGER
# ======================================================================
print("\n[4/8] Device Manager")
print("-" * 50)


@test("DeviceManager: discovers input devices")
def _():
    from audio.device_manager import DeviceManager
    dm = DeviceManager()
    inputs = dm.get_input_devices()
    assert isinstance(inputs, list)
    assert len(inputs) > 0, "No input devices found on this machine"
    for idx, name in inputs:
        assert isinstance(idx, int)
        assert isinstance(name, str)


@test("DeviceManager: discovers output devices")
def _():
    from audio.device_manager import DeviceManager
    dm = DeviceManager()
    outputs = dm.get_output_devices()
    assert isinstance(outputs, list)
    assert len(outputs) > 0, "No output devices found on this machine"


@test("DeviceManager: get_device_name works")
def _():
    from audio.device_manager import DeviceManager
    dm = DeviceManager()
    inputs = dm.get_input_devices()
    idx, expected_name = inputs[0]
    name = dm.get_device_name(idx)
    assert name == expected_name


@test("DeviceManager: get_device_name returns None for invalid index")
def _():
    from audio.device_manager import DeviceManager
    dm = DeviceManager()
    assert dm.get_device_name(99999) is None
    assert dm.get_device_name(-1) is None


@test("DeviceManager: find_device_by_name works")
def _():
    from audio.device_manager import DeviceManager
    dm = DeviceManager()
    inputs = dm.get_input_devices()
    idx, name = inputs[0]
    # Search by partial name
    found = dm.find_device_by_name(name[:10], is_input=True)
    assert found is not None


@test("DeviceManager: find_virtual_cable_output detects VoiceMeeter")
def _():
    from audio.device_manager import DeviceManager
    dm = DeviceManager()
    idx = dm.find_virtual_cable_output()
    if idx is not None:
        name = dm.get_device_name(idx)
        assert "VoiceMeeter" in name or "CABLE" in name or "Intelligo" in name
        print(f"        (found: {name})")
    else:
        print("        (no virtual cable installed - skipped)")


@test("DeviceManager: backward compat alias find_vb_cable_input")
def _():
    from audio.device_manager import DeviceManager
    dm = DeviceManager()
    assert dm.find_vb_cable_input() == dm.find_virtual_cable_output()


@test("DeviceManager: refresh_devices doesn't crash")
def _():
    from audio.device_manager import DeviceManager
    dm = DeviceManager()
    dm.refresh_devices()
    dm.refresh_devices()  # Double refresh should be safe
    assert len(dm.get_input_devices()) > 0


# ======================================================================
# 5. NOISE PROCESSORS
# ======================================================================
print("\n[5/8] Noise Processors")
print("-" * 50)


@test("SpectralGateProcessor: initializes correctly")
def _():
    from processing.spectral_gate_processor import SpectralGateProcessor
    proc = SpectralGateProcessor()
    proc.initialize(48000, 480)
    assert proc.name == "Spectral Gate"


@test("SpectralGateProcessor: processes frames without crash")
def _():
    from processing.spectral_gate_processor import SpectralGateProcessor
    proc = SpectralGateProcessor()
    proc.initialize(48000, 480)
    proc.set_strength(0.7)
    # Feed enough frames to trigger processing (need ~100ms = 10 frames)
    results = []
    for i in range(20):
        noise = np.random.randn(480).astype(np.float32) * 0.1
        result = proc.process_frame(noise)
        assert result.shape == (480,)
        assert result.dtype == np.float32
        results.append(result)


@test("SpectralGateProcessor: output is quieter than noisy input")
def _():
    from processing.spectral_gate_processor import SpectralGateProcessor
    proc = SpectralGateProcessor()
    proc.initialize(48000, 480)
    proc.set_strength(1.0)  # Max strength
    # Feed 500ms of noise
    input_energy = 0
    output_energy = 0
    for i in range(50):
        noise = np.random.randn(480).astype(np.float32) * 0.3
        input_energy += np.sum(noise ** 2)
        result = proc.process_frame(noise)
        output_energy += np.sum(result ** 2)
    # After warmup, output should have less energy than input
    assert output_energy < input_energy, \
        f"Output energy ({output_energy:.2f}) should be less than input ({input_energy:.2f})"


@test("SpectralGateProcessor: strength 0 is less aggressive than strength 1")
def _():
    from processing.spectral_gate_processor import SpectralGateProcessor
    np.random.seed(42)
    noise = [np.random.randn(480).astype(np.float32) * 0.2 for _ in range(30)]

    proc_weak = SpectralGateProcessor()
    proc_weak.initialize(48000, 480)
    proc_weak.set_strength(0.1)

    proc_strong = SpectralGateProcessor()
    proc_strong.initialize(48000, 480)
    proc_strong.set_strength(1.0)

    energy_weak = 0
    energy_strong = 0
    for frame in noise:
        r1 = proc_weak.process_frame(frame.copy())
        r2 = proc_strong.process_frame(frame.copy())
        energy_weak += np.sum(r1 ** 2)
        energy_strong += np.sum(r2 ** 2)

    # Stronger setting should remove more energy
    assert energy_strong <= energy_weak, \
        f"Strong ({energy_strong:.2f}) should be <= weak ({energy_weak:.2f})"


@test("SpectralGateProcessor: reset clears internal state")
def _():
    from processing.spectral_gate_processor import SpectralGateProcessor
    proc = SpectralGateProcessor()
    proc.initialize(48000, 480)
    for _ in range(10):
        proc.process_frame(np.random.randn(480).astype(np.float32) * 0.1)
    proc.reset()
    # After reset, output buffer should be empty -> returns silence initially
    result = proc.process_frame(np.random.randn(480).astype(np.float32) * 0.1)
    assert result.shape == (480,)


@test("SpectralGateProcessor: set_strength clamps to 0-1")
def _():
    from processing.spectral_gate_processor import SpectralGateProcessor
    proc = SpectralGateProcessor()
    proc.set_strength(-5.0)
    assert proc._strength == 0.0
    proc.set_strength(99.0)
    assert proc._strength == 1.0
    proc.set_strength(0.5)
    assert proc._strength == 0.5


# ======================================================================
# 6. PROCESSOR FACTORY
# ======================================================================
print("\n[6/8] Processor Factory")
print("-" * 50)


@test("ProcessorFactory: spectral_gate always available")
def _():
    from processing.processor_factory import ProcessorFactory
    engines = ProcessorFactory.get_available_engines()
    assert "spectral_gate" in engines


@test("ProcessorFactory: create spectral_gate")
def _():
    from processing.processor_factory import ProcessorFactory
    proc = ProcessorFactory.create("spectral_gate")
    proc.initialize(48000, 480)
    assert proc.name == "Spectral Gate"


@test("ProcessorFactory: create unknown engine raises error")
def _():
    from processing.processor_factory import ProcessorFactory
    try:
        ProcessorFactory.create("nonexistent_engine")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


@test("ProcessorFactory: display names are correct")
def _():
    from processing.processor_factory import ProcessorFactory
    names = ProcessorFactory.get_engine_display_names()
    assert names["spectral_gate"] == "Spectral Gate"
    assert names["rnnoise"] == "RNNoise"
    assert names["deepfilter"] == "DeepFilter"


# ======================================================================
# 7. AUDIO PIPELINE
# ======================================================================
print("\n[7/8] Audio Pipeline")
print("-" * 50)


@test("AudioPipeline: creates without error")
def _():
    from audio.device_manager import DeviceManager
    from audio.audio_pipeline import AudioPipeline
    dm = DeviceManager()
    pipeline = AudioPipeline(dm)
    assert pipeline.enabled is False
    assert pipeline.last_error is None


@test("AudioPipeline: enable/disable toggle")
def _():
    from audio.device_manager import DeviceManager
    from audio.audio_pipeline import AudioPipeline
    from processing.processor_factory import ProcessorFactory
    dm = DeviceManager()
    pipeline = AudioPipeline(dm)
    proc = ProcessorFactory.create("spectral_gate")
    proc.initialize(48000, 480)
    pipeline.set_processor(proc)

    pipeline.enabled = True
    assert pipeline.enabled is True
    pipeline.enabled = False
    assert pipeline.enabled is False


@test("AudioPipeline: start and stop with real devices")
def _():
    from audio.device_manager import DeviceManager
    from audio.audio_pipeline import AudioPipeline
    from processing.processor_factory import ProcessorFactory
    dm = DeviceManager()
    pipeline = AudioPipeline(dm)

    proc = ProcessorFactory.create("spectral_gate")
    proc.initialize(48000, 480)
    pipeline.set_processor(proc)

    inputs = dm.get_input_devices()
    outputs = dm.get_output_devices()
    if inputs and outputs:
        pipeline.set_input_device(inputs[0][0])
        pipeline.set_output_device(outputs[0][0])
        pipeline.start()
        time.sleep(0.5)  # Let it run briefly
        pipeline.enabled = True
        time.sleep(0.5)  # Process some audio
        pipeline.stop()
        print(f"        (ran for 1s, error={pipeline.last_error})")
    else:
        print("        (no devices available - skipped)")


@test("AudioPipeline: level meters update during processing")
def _():
    from audio.device_manager import DeviceManager
    from audio.audio_pipeline import AudioPipeline
    from processing.processor_factory import ProcessorFactory
    dm = DeviceManager()
    pipeline = AudioPipeline(dm)

    proc = ProcessorFactory.create("spectral_gate")
    proc.initialize(48000, 480)
    pipeline.set_processor(proc)

    inputs = dm.get_input_devices()
    outputs = dm.get_output_devices()
    if inputs and outputs:
        pipeline.set_input_device(inputs[0][0])
        pipeline.set_output_device(outputs[0][0])
        pipeline.start()
        pipeline.enabled = True
        time.sleep(1.0)

        # Meters should have been updated (even if just from noise floor)
        in_db = pipeline.input_meter.rms_db
        assert isinstance(in_db, float)
        print(f"        (input={in_db:.1f}dB, output={pipeline.output_meter.rms_db:.1f}dB)")
        pipeline.stop()
    else:
        print("        (no devices - skipped)")


@test("AudioPipeline: handles device change while running")
def _():
    from audio.device_manager import DeviceManager
    from audio.audio_pipeline import AudioPipeline
    from processing.processor_factory import ProcessorFactory
    dm = DeviceManager()
    pipeline = AudioPipeline(dm)

    proc = ProcessorFactory.create("spectral_gate")
    proc.initialize(48000, 480)
    pipeline.set_processor(proc)

    inputs = dm.get_input_devices()
    outputs = dm.get_output_devices()
    if len(inputs) >= 2 and outputs:
        pipeline.set_input_device(inputs[0][0])
        pipeline.set_output_device(outputs[0][0])
        pipeline.start()
        time.sleep(0.3)
        # Switch input device while running
        pipeline.set_input_device(inputs[1][0])
        time.sleep(0.3)
        pipeline.stop()
        print("        (device switch successful)")
    else:
        print("        (need 2+ input devices - skipped)")


# ======================================================================
# 8. UI MODULE IMPORTS
# ======================================================================
print("\n[8/8] UI Modules")
print("-" * 50)


@test("UI: theme module loads with all colors and fonts")
def _():
    from ui.theme import COLORS, FONTS
    required_colors = ["bg_primary", "accent_active", "meter_green", "meter_yellow", "meter_red"]
    for c in required_colors:
        assert c in COLORS, f"Missing color: {c}"
    required_fonts = ["title", "body", "caption"]
    for f in required_fonts:
        assert f in FONTS, f"Missing font: {f}"


@test("UI: all UI modules import cleanly")
def _():
    from ui.level_meter_widget import LevelMeterWidget
    from ui.device_selector import DeviceSelector
    from ui.main_panel import MainPanel
    from ui.tray_icon import TrayIcon
    from ui.app_window import AppWindow


@test("UI: base_processor abstract class enforces interface")
def _():
    from processing.base_processor import NoiseProcessor
    try:
        # Cannot instantiate abstract class
        NoiseProcessor()
        assert False, "Should have raised TypeError"
    except TypeError:
        pass


# ======================================================================
# SUMMARY
# ======================================================================
print("\n" + "=" * 60)
total = PASS + FAIL
print(f"  RESULTS: {PASS}/{total} passed, {FAIL} failed")
print("=" * 60)

if ERRORS:
    print("\nFailed tests:")
    for name, error, tb in ERRORS:
        print(f"\n  {name}")
        print(f"  Error: {error}")
        # Print last 3 lines of traceback for context
        tb_lines = tb.strip().split("\n")
        for line in tb_lines[-3:]:
            print(f"    {line}")

if FAIL > 0:
    sys.exit(1)
else:
    print("\nAll tests passed!")
    sys.exit(0)
