"""Generate NoiseClear app icon (.ico and .png) programmatically.

Creates a modern, professional logo with:
- Gradient circular background (deep navy to dark blue)
- Clean microphone silhouette in white
- Diagonal cancel line (noise cancellation concept)
- Subtle sound wave arcs
- Soft glow and shadow effects
"""

from PIL import Image, ImageDraw, ImageFilter
import math
import os


def _lerp_color(c1, c2, t):
    """Linearly interpolate between two RGBA colors."""
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def _draw_radial_gradient(img, cx, cy, radius, color_center, color_edge):
    """Draw a radial gradient circle using concentric rings."""
    draw = ImageDraw.Draw(img)
    for r in range(radius, 0, -1):
        t = 1.0 - (r / radius)
        color = _lerp_color(color_edge, color_center, t)
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            fill=color,
        )


def _draw_thick_arc(draw, bbox, start, end, fill, width):
    """Draw a thick arc (workaround for thin arc rendering at small sizes)."""
    draw.arc(bbox, start=start, end=end, fill=fill, width=width)


def create_icon():
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    # Color palette
    bg_outer = (10, 10, 30, 255)       # Deep navy edge
    bg_center = (22, 28, 50, 255)      # Slightly lighter center
    accent_green = (0, 200, 120, 255)  # Modern teal-green
    accent_glow = (0, 200, 120, 60)    # Green glow
    mic_color = (240, 245, 255, 255)   # Near-white for mic
    wave_color = (0, 200, 120, 120)    # Green waves, semi-transparent
    cancel_color = (220, 60, 60, 200)  # Red cancel line
    ring_color = (0, 200, 120, 100)    # Outer ring glow

    for size in sizes:
        # Work at 4x resolution for anti-aliasing, then downscale
        ss = 4  # supersampling factor
        s = size * ss
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        cx, cy = s // 2, s // 2
        margin = max(ss, s // 16)
        radius = s // 2 - margin

        # --- Background gradient circle ---
        _draw_radial_gradient(img, cx, cy, radius, bg_center, bg_outer)

        # --- Outer accent ring ---
        ring_w = max(ss, s // 28)
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            outline=accent_green,
            width=ring_w,
        )

        # --- Subtle inner glow ring ---
        glow_r = int(radius * 0.92)
        glow_w = max(ss, s // 48)
        draw.ellipse(
            [cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r],
            outline=ring_color,
            width=glow_w,
        )

        # --- Microphone ---
        # Mic capsule (rounded rect)
        mic_w = max(ss * 2, int(s * 0.20))
        mic_h = max(ss * 3, int(s * 0.32))
        mic_x = cx - mic_w // 2
        mic_y = cy - int(s * 0.24)
        mic_r = mic_w // 2  # Full round top/bottom

        draw.rounded_rectangle(
            [mic_x, mic_y, mic_x + mic_w, mic_y + mic_h],
            radius=mic_r,
            fill=mic_color,
        )

        # Mic grille lines (horizontal lines inside capsule)
        grille_count = max(1, size // 16)
        grille_spacing = mic_h / (grille_count + 1)
        grille_w = max(1, s // 128)
        grille_margin = int(mic_w * 0.2)
        for i in range(1, grille_count + 1):
            gy = int(mic_y + i * grille_spacing)
            draw.line(
                [mic_x + grille_margin, gy,
                 mic_x + mic_w - grille_margin, gy],
                fill=(22, 28, 50, 120),
                width=grille_w,
            )

        # Mic holder arc (U-shape around bottom of capsule)
        arc_w = max(ss * 3, int(s * 0.34))
        arc_h = max(ss * 3, int(s * 0.18))
        arc_x = cx - arc_w // 2
        arc_y = mic_y + mic_h - int(s * 0.04)
        arc_line_w = max(ss, s // 22)

        draw.arc(
            [arc_x, arc_y, arc_x + arc_w, arc_y + arc_h],
            start=0, end=180,
            fill=mic_color,
            width=arc_line_w,
        )

        # Mic stand (vertical line)
        stand_top = arc_y + arc_h // 2
        stand_bottom = stand_top + max(ss * 2, int(s * 0.10))
        stand_w = max(ss, s // 22)

        draw.line(
            [cx, stand_top, cx, stand_bottom],
            fill=mic_color,
            width=stand_w,
        )

        # Mic base (horizontal line)
        base_w = max(ss * 3, int(s * 0.18))
        draw.line(
            [cx - base_w // 2, stand_bottom, cx + base_w // 2, stand_bottom],
            fill=mic_color,
            width=stand_w,
        )

        # --- Sound wave arcs (left side, showing "noise" being cancelled) ---
        for j in range(3):
            wave_r = int(s * (0.10 + j * 0.07))
            wave_cx = cx - int(s * 0.10)
            wave_cy = cy - int(s * 0.04)
            wave_w = max(ss, s // 36)
            alpha = max(40, 120 - j * 30)
            wc = (0, 200, 120, alpha)
            _draw_thick_arc(
                draw,
                [wave_cx - wave_r, wave_cy - wave_r,
                 wave_cx + wave_r, wave_cy + wave_r],
                start=135, end=225,
                fill=wc,
                width=wave_w,
            )

        # --- Sound wave arcs (right side) ---
        for j in range(3):
            wave_r = int(s * (0.10 + j * 0.07))
            wave_cx = cx + int(s * 0.10)
            wave_cy = cy - int(s * 0.04)
            wave_w = max(ss, s // 36)
            alpha = max(40, 120 - j * 30)
            wc = (0, 200, 120, alpha)
            _draw_thick_arc(
                draw,
                [wave_cx - wave_r, wave_cy - wave_r,
                 wave_cx + wave_r, wave_cy + wave_r],
                start=-45, end=45,
                fill=wc,
                width=wave_w,
            )

        # --- Diagonal cancel line (noise cancellation symbol) ---
        cancel_w = max(ss, s // 18)
        # Draw from top-right to bottom-left across the mic area
        line_offset = int(radius * 0.55)
        draw.line(
            [cx + line_offset, cy - line_offset,
             cx - line_offset, cy + line_offset],
            fill=cancel_color,
            width=cancel_w,
        )

        # Rounded ends for the cancel line
        end_r = cancel_w // 2
        draw.ellipse(
            [cx + line_offset - end_r, cy - line_offset - end_r,
             cx + line_offset + end_r, cy - line_offset + end_r],
            fill=cancel_color,
        )
        draw.ellipse(
            [cx - line_offset - end_r, cy + line_offset - end_r,
             cx - line_offset + end_r, cy + line_offset + end_r],
            fill=cancel_color,
        )

        # --- Downscale with high-quality anti-aliasing ---
        img = img.resize((size, size), Image.LANCZOS)
        images.append(img)

    # Save files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ico_path = os.path.join(script_dir, "icon.ico")
    png_path = os.path.join(script_dir, "icon.png")

    # Save the 256px version as PNG (for tray icon and README)
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

    # Also save a high-res version for the README
    logo_path = os.path.join(script_dir, "assets", "logo.png")
    os.makedirs(os.path.join(script_dir, "assets"), exist_ok=True)

    # Generate a 512px version for README
    s = 512
    ss = 4
    s_full = s * ss
    img = Image.new("RGBA", (s_full, s_full), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = s_full // 2, s_full // 2
    margin = s_full // 16
    radius = s_full // 2 - margin

    _draw_radial_gradient(img, cx, cy, radius, bg_center, bg_outer)

    ring_w = s_full // 28
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=accent_green,
        width=ring_w,
    )
    glow_r = int(radius * 0.92)
    glow_w = s_full // 48
    draw.ellipse(
        [cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r],
        outline=ring_color,
        width=glow_w,
    )

    # Mic
    mic_w = int(s_full * 0.20)
    mic_h = int(s_full * 0.32)
    mic_x = cx - mic_w // 2
    mic_y = cy - int(s_full * 0.24)
    mic_r = mic_w // 2
    draw.rounded_rectangle(
        [mic_x, mic_y, mic_x + mic_w, mic_y + mic_h],
        radius=mic_r, fill=mic_color,
    )

    # Grille
    grille_count = 5
    grille_spacing = mic_h / (grille_count + 1)
    grille_w = max(1, s_full // 128)
    grille_margin = int(mic_w * 0.2)
    for i in range(1, grille_count + 1):
        gy = int(mic_y + i * grille_spacing)
        draw.line(
            [mic_x + grille_margin, gy, mic_x + mic_w - grille_margin, gy],
            fill=(22, 28, 50, 120), width=grille_w,
        )

    # Arc, stand, base
    arc_w_v = int(s_full * 0.34)
    arc_h_v = int(s_full * 0.18)
    arc_x_v = cx - arc_w_v // 2
    arc_y_v = mic_y + mic_h - int(s_full * 0.04)
    arc_line_w = s_full // 22
    draw.arc(
        [arc_x_v, arc_y_v, arc_x_v + arc_w_v, arc_y_v + arc_h_v],
        start=0, end=180, fill=mic_color, width=arc_line_w,
    )
    stand_top = arc_y_v + arc_h_v // 2
    stand_bottom = stand_top + int(s_full * 0.10)
    stand_w_v = s_full // 22
    draw.line([cx, stand_top, cx, stand_bottom], fill=mic_color, width=stand_w_v)
    base_w_v = int(s_full * 0.18)
    draw.line(
        [cx - base_w_v // 2, stand_bottom, cx + base_w_v // 2, stand_bottom],
        fill=mic_color, width=stand_w_v,
    )

    # Waves
    for j in range(3):
        wave_r = int(s_full * (0.10 + j * 0.07))
        alpha = max(40, 120 - j * 30)
        wc = (0, 200, 120, alpha)
        wave_w = s_full // 36
        # Left
        wcx = cx - int(s_full * 0.10)
        wcy = cy - int(s_full * 0.04)
        draw.arc(
            [wcx - wave_r, wcy - wave_r, wcx + wave_r, wcy + wave_r],
            start=135, end=225, fill=wc, width=wave_w,
        )
        # Right
        wcx = cx + int(s_full * 0.10)
        draw.arc(
            [wcx - wave_r, wcy - wave_r, wcx + wave_r, wcy + wave_r],
            start=-45, end=45, fill=wc, width=wave_w,
        )

    # Cancel line
    cancel_w = s_full // 18
    line_offset = int(radius * 0.55)
    draw.line(
        [cx + line_offset, cy - line_offset, cx - line_offset, cy + line_offset],
        fill=cancel_color, width=cancel_w,
    )
    end_r = cancel_w // 2
    draw.ellipse(
        [cx + line_offset - end_r, cy - line_offset - end_r,
         cx + line_offset + end_r, cy - line_offset + end_r],
        fill=cancel_color,
    )
    draw.ellipse(
        [cx - line_offset - end_r, cy + line_offset - end_r,
         cx - line_offset + end_r, cy + line_offset + end_r],
        fill=cancel_color,
    )

    img = img.resize((s, s), Image.LANCZOS)
    img.save(logo_path, "PNG")
    print(f"Saved {logo_path}")


if __name__ == "__main__":
    create_icon()
