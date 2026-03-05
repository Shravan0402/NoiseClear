"""Generate NoiseClear app icon (.ico and .png) programmatically."""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background circle with gradient effect
        margin = max(1, size // 16)
        cx, cy = size // 2, size // 2
        radius = size // 2 - margin

        # Dark blue circle background
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=(15, 15, 35, 255),
            outline=(52, 152, 219, 255),
            width=max(1, size // 32),
        )

        # Inner glow ring
        inner_r = int(radius * 0.85)
        draw.ellipse(
            [cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r],
            fill=(26, 26, 46, 255),
        )

        # Microphone body (rounded rectangle)
        mic_w = max(2, int(size * 0.22))
        mic_h = max(3, int(size * 0.35))
        mic_x = cx - mic_w // 2
        mic_y = cy - int(size * 0.25)
        mic_radius = max(1, mic_w // 2)

        draw.rounded_rectangle(
            [mic_x, mic_y, mic_x + mic_w, mic_y + mic_h],
            radius=mic_radius,
            fill=(46, 204, 113, 255),  # Green
        )

        # Mic holder arc
        arc_w = max(3, int(size * 0.36))
        arc_h = max(3, int(size * 0.22))
        arc_x = cx - arc_w // 2
        arc_y = mic_y + mic_h - int(size * 0.06)
        arc_width = max(1, size // 24)

        draw.arc(
            [arc_x, arc_y, arc_x + arc_w, arc_y + arc_h],
            start=0, end=180,
            fill=(46, 204, 113, 255),
            width=arc_width,
        )

        # Mic stand (vertical line)
        stand_top = arc_y + arc_h // 2
        stand_bottom = stand_top + max(2, int(size * 0.1))
        stand_width = max(1, size // 24)

        draw.line(
            [cx, stand_top, cx, stand_bottom],
            fill=(46, 204, 113, 255),
            width=stand_width,
        )

        # Base line
        base_w = max(3, int(size * 0.2))
        draw.line(
            [cx - base_w // 2, stand_bottom, cx + base_w // 2, stand_bottom],
            fill=(46, 204, 113, 255),
            width=stand_width,
        )

        # Sound wave arcs (right side)
        wave_color = (52, 152, 219, 180)  # Blue, slightly transparent
        for j in range(2):
            wave_r = int(size * (0.12 + j * 0.08))
            wave_cx = cx + int(size * 0.12)
            wave_cy = cy - int(size * 0.05)
            wave_width = max(1, size // 32)
            draw.arc(
                [wave_cx - wave_r, wave_cy - wave_r,
                 wave_cx + wave_r, wave_cy + wave_r],
                start=-45, end=45,
                fill=wave_color,
                width=wave_width,
            )

        images.append(img)

    # Save as .ico (multi-size)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ico_path = os.path.join(script_dir, "icon.ico")
    png_path = os.path.join(script_dir, "icon.png")

    # Save the 256px version as PNG (for tray icon)
    images[-1].save(png_path, "PNG")
    print(f"Saved {png_path}")

    # Save multi-size ICO
    images[0].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"Saved {ico_path}")


if __name__ == "__main__":
    create_icon()
