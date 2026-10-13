#!/usr/bin/env python3
"""Generate MySQL IDLE's Windows executable and Inno Setup artwork.

The source of truth is vector-like drawing code here; generated binary files are
created during the build so the repository does not need opaque icon binaries.
Requires Pillow (installed by the Windows build workflow).
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

NAVY = (15, 23, 42)
BLUE = (37, 99, 235)
CYAN = (34, 211, 238)
WHITE = (248, 250, 252)
MUTED = (148, 163, 184)
DARKER = (11, 18, 32)


def _font(size: int, bold: bool = False):
    candidates = (
        [r"C:\Windows\Fonts\seguisb.ttf", r"C:\Windows\Fonts\arialbd.ttf"]
        if bold
        else [r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"]
    )
    candidates += (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if bold
        else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _render_mark(size: int, include_tile: bool = True) -> Image.Image:
    """Draw a clean terminal chevron/cursor mark at high resolution then downsample."""
    scale = 4
    n = max(1, size) * scale
    image = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    if include_tile:
        inset = int(n * 0.055)
        draw.rounded_rectangle(
            (inset, inset, n - inset - 1, n - inset - 1),
            radius=int(n * 0.235),
            fill=NAVY + (255,),
        )
    # The chevron reads as a SQL prompt; the cursor makes the symbol distinct
    # from generic database cylinders at small launcher/icon sizes.
    chevron = [
        (0.275, 0.315), (0.355, 0.245), (0.565, 0.455),
        (0.355, 0.665), (0.275, 0.595), (0.415, 0.455),
    ]
    draw.polygon([(int(x * n), int(y * n)) for x, y in chevron], fill=CYAN + (255,))
    draw.rounded_rectangle(
        (int(0.57 * n), int(0.61 * n), int(0.77 * n), int(0.69 * n)),
        radius=max(1, int(0.025 * n)),
        fill=BLUE + (255,),
    )
    if size < 48:
        return image.resize((size, size), Image.Resampling.LANCZOS)
    # Three tiny status lights lend the tile a subtle terminal-window motif.
    radius = max(2, int(n * 0.022))
    cy = int(0.19 * n)
    for cx, c in ((0.25, CYAN), (0.34, BLUE), (0.43, (71, 85, 105))):
        px = int(cx * n)
        draw.ellipse((px-radius, cy-radius, px+radius, cy+radius), fill=c + (255,))
    return image.resize((size, size), Image.Resampling.LANCZOS)


def _centered_text(draw: ImageDraw.ImageDraw, center_x: int, top: int, text: str, font, fill) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    width = box[2] - box[0]
    draw.text((center_x - width // 2, top), text, font=font, fill=fill)


def _wizard_image() -> Image.Image:
    width, height = 164, 314
    image = Image.new("RGB", (width, height), NAVY)
    pix = image.load()
    for y in range(height):
        t = y / max(height - 1, 1)
        c = tuple(round(DARKER[i] * (1 - t) + NAVY[i] * t) for i in range(3))
        for x in range(width):
            pix[x, y] = c
    draw = ImageDraw.Draw(image)
    # restrained geometric accents, kept clear of the installer text
    draw.arc((-48, 18, 210, 276), 205, 330, fill=(26, 50, 83), width=2)
    draw.arc((-28, 36, 190, 254), 205, 330, fill=(23, 42, 70), width=2)
    logo = _render_mark(84, include_tile=False).convert("RGBA")
    tile = Image.new("RGBA", (92, 92), NAVY + (255,))
    tile_draw = ImageDraw.Draw(tile)
    tile_draw.rounded_rectangle((1, 1, 90, 90), radius=22, fill=NAVY + (255,))
    tile.alpha_composite(logo, (4, 4))
    image.paste(tile.convert("RGB"), ((width - 92) // 2, 25))
    draw = ImageDraw.Draw(image)
    _centered_text(draw, width // 2, 132, "MySQL IDLE", _font(16, True), WHITE)
    _centered_text(draw, width // 2, 158, "SQL WORKSPACE", _font(9, True), CYAN)
    draw.rounded_rectangle((32, 190, 132, 192), radius=1, fill=BLUE)
    # abstract query rows make the image feel product-specific without tiny copy
    for y, x2, color in ((218, 127, CYAN), (237, 111, (71, 85, 105)), (256, 139, (71, 85, 105))):
        draw.rounded_rectangle((25, y, x2, y + 5), radius=2, fill=color)
    draw.ellipse((25, 281, 31, 287), fill=CYAN)
    draw.rounded_rectangle((38, 282, 118, 286), radius=2, fill=(51, 65, 85))
    return image


def _wizard_small() -> Image.Image:
    image = Image.new("RGB", (55, 55), WHITE)
    mark = _render_mark(49, include_tile=True)
    image.paste(mark.convert("RGB"), (3, 3))
    return image


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    ico = _render_mark(256, include_tile=True)
    ico.save(
        ASSETS / "mysqlidle.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    _wizard_image().save(ASSETS / "wizard-image.bmp", format="BMP")
    _wizard_small().save(ASSETS / "wizard-small.bmp", format="BMP")
    print("Generated assets/mysqlidle.ico, wizard-image.bmp (164x314), wizard-small.bmp (55x55).")


if __name__ == "__main__":
    main()
