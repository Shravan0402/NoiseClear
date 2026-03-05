"""NoiseClear - Real-time Noise Cancellation for Windows.

Usage:
    1. Install VB-CABLE from https://vb-audio.com/Cable/
    2. pip install -r requirements.txt
    3. python main.py
    4. Select your real microphone as Input
    5. Select 'CABLE Input' as Output
    6. In Zoom/Discord/Meet, set microphone to 'CABLE Output'
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from audio.device_manager import DeviceManager
from audio.audio_pipeline import AudioPipeline
from processing.processor_factory import ProcessorFactory


def create_processor(settings):
    """Create and initialize the noise processor."""
    engine_name = settings.get("engine")
    available = ProcessorFactory.get_available_engines()

    if engine_name not in available:
        engine_name = "spectral_gate"
        settings.set("engine", engine_name)

    processor = ProcessorFactory.create(engine_name)
    processor.initialize(
        sample_rate=settings.get("sample_rate"),
        frame_size=settings.get("frame_size"),
    )
    processor.set_strength(settings.get("noise_reduction_strength"))
    return processor


def main():
    # Load settings
    settings = Settings()

    # Initialize device manager
    device_manager = DeviceManager()

    # Create audio pipeline
    pipeline = AudioPipeline(device_manager)

    # Initialize noise processor
    processor = create_processor(settings)
    pipeline.set_processor(processor)

    # Set initial enabled state
    pipeline.enabled = settings.get("noise_cancellation_enabled")

    def on_engine_change(engine_id):
        """Handle engine switch from UI."""
        settings.set("engine", engine_id)
        try:
            new_processor = ProcessorFactory.create(engine_id)
            new_processor.initialize(
                sample_rate=settings.get("sample_rate"),
                frame_size=settings.get("frame_size"),
            )
            new_processor.set_strength(settings.get("noise_reduction_strength"))
            pipeline.set_processor(new_processor)
        except Exception as e:
            print(f"Failed to switch engine to {engine_id}: {e}")
            # Fall back to spectral gate
            fallback = ProcessorFactory.create("spectral_gate")
            fallback.initialize(
                sample_rate=settings.get("sample_rate"),
                frame_size=settings.get("frame_size"),
            )
            fallback.set_strength(settings.get("noise_reduction_strength"))
            pipeline.set_processor(fallback)
            settings.set("engine", "spectral_gate")

    # Start audio pipeline
    pipeline.start()

    # Create and run GUI
    from ui.app_window import AppWindow

    app = AppWindow(pipeline, device_manager, settings,
                    on_engine_change=on_engine_change)

    try:
        app.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        pipeline.stop()
        settings.save()


if __name__ == "__main__":
    main()
