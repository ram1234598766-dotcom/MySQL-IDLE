#!/usr/bin/env python3
"""Generate MySQL IDLE's Windows icon and polished Inno Setup artwork.

The vector-like drawing code is the source of truth. Assets are regenerated
during the Windows build, so generated binary files do not need to be checked in.
Requires Pillow (installed by the Windows build workflow).
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

# MySQL visual references informed the blue/teal palette; the product mark below
# is original artwork (a database stack and SQL prompt), not the MySQL dolphin.
NAVY = (11, 24, 42)
DEEP_NAVY = (5, 14, 27)
BLUE = (37, 99, 235)
MYSQL_BLUE = (68, 121, 161)
TEAL = (0, 117, 143)
CYAN = (34, 211, 238)
PALE_CYAN = (155, 240, 248)
ORANGE = (242, 145, 17)
WHITE = (248, 250, 252)
MUTED = (148, 163, 184)


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


def _draw_database(draw: ImageDraw.ImageDraw, n: int) -> None:
    """Draw a distinctive database cylinder with an SQL prompt overlay."""
    x0, x1 = int(0.19 * n), int(0.73 * n)
    y0, y1 = int(0.245 * n), int(0.77 * n)
    stroke = max(1, int(0.012 * n))

    # Soft cast shadow separates the mark from the tile.
    draw.ellipse(
        (x0 + int(0.035 * n), y1 - int(0.015 * n),
         x1 + int(0.035 * n), y1 + int(0.075 * n)),
        fill=(2, 8, 17, 145),
    )
    # Database body: blue side wall with subtle highlights.
    draw.rounded_rectangle(
        (x0, y0 + int(0.105 * n), x1, y1 - int(0.025 * n)),
        radius=int(0.075 * n),
        fill=MYSQL_BLUE + (255,),
    )
    draw.rounded_rectangle(
        (x0 + int(0.035 * n), y0 + int(0.14 * n),
         x0 + int(0.115 * n), y1 - int(0.06 * n)),
        radius=max(1, int(0.025 * n)),
        fill=(119, 174, 201, 160),
    )

    # Data tiers make the cylinder readable at launcher and taskbar sizes.
    for fraction in (0.31, 0.435):
        y = y0 + int(fraction * n)
        draw.line(
            (x0 + int(0.045 * n), y, x1 - int(0.045 * n), y),
            fill=(137, 201, 219, 220),
            width=stroke,
        )

    # Top ellipse and its rim provide depth without copying any third-party mark.
    top = (x0, y0, x1, y0 + int(0.22 * n))
    draw.ellipse(top, fill=TEAL + (255,), outline=PALE_CYAN + (255,), width=stroke)
    draw.arc(
        (x0 + int(0.035 * n), y0 + int(0.035 * n),
         x1 - int(0.035 * n), y0 + int(0.175 * n)),
        190, 350, fill=(112, 231, 240, 240), width=stroke,
    )

    # A bright SQL chevron and amber cursor are the product's own distinguishing cue.
    points = [
        (int(0.385 * n), int(0.425 * n)),
        (int(0.465 * n), int(0.495 * n)),
        (int(0.385 * n), int(0.565 * n)),
    ]
    draw.line(points, fill=WHITE + (255,), width=max(2, int(0.052 * n)), joint="curve")
    cursor = (
        int(0.505 * n), int(0.545 * n),
        int(0.605 * n), int(0.595 * n),
    )
    draw.rounded_rectangle(
        cursor, radius=max(1, int(0.012 * n)), fill=ORANGE + (255,)
    )


def _render_mark(size: int, include_tile: bool = True) -> Image.Image:
    """Render the product mark at 4x resolution and downsample with antialiasing."""
    scale = 4
    n = max(1, size) * scale
    image = Image.new("RGBA", (n, n), (0, 0, 0, 0))

    if include_tile:
        inset = int(n * 0.045)
        radius = int(n * 0.235)
        gradient = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        gradient_draw = ImageDraw.Draw(gradient)
        for y in range(n):
            t = y / max(n - 1, 1)
            color = tuple(
                round(DEEP_NAVY[i] * (1 - t) + NAVY[i] * t) for i in range(3)
            )
            gradient_draw.line((0, y, n, y), fill=color + (255,))
        mask = Image.new("L", (n, n), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (inset, inset, n - inset - 1, n - inset - 1),
            radius=radius, fill=255,
        )
        gradient.putalpha(mask)
        image.alpha_composite(gradient)

        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle(
            (inset, inset, n - inset - 1, n - inset - 1),
            radius=radius, outline=(87, 151, 187, 195),
            width=max(1, int(n * 0.008)),
        )
        # Restrained glass highlight, clipped naturally inside the tile inset.
        draw.arc(
            (int(0.11 * n), int(0.09 * n), int(0.88 * n), int(0.68 * n)),
            190, 340, fill=(111, 188, 219, 85), width=max(1, int(n * 0.009)),
        )
        if size >= 64:
            for cx, color in (
                (0.22, CYAN), (0.32, BLUE), (0.42, (76, 96, 119))
            ):
                r = max(2, int(n * 0.016))
                cy = int(0.16 * n)
                px = int(cx * n)
                draw.ellipse((px-r, cy-r, px+r, cy+r), fill=color + (255,))

    _draw_database(ImageDraw.Draw(image), n)
    return image.resize((size, size), Image.Resampling.LANCZOS)


def _centered_text(
    draw: ImageDraw.ImageDraw, center_x: int, top: int, text: str, font, fill
) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    width = box[2] - box[0]
    draw.text((center_x - width // 2, top), text, font=font, fill=fill)


def _wizard_image() -> Image.Image:
    """Draw the modern installer side panel (Inno Setup expects 164x314)."""
    width, height = 164, 314
    image = Image.new("RGB", (width, height), NAVY)
    pix = image.load()
    for y in range(height):
        t = y / max(height - 1, 1)
        color = tuple(
            round(DEEP_NAVY[i] * (1 - t) + NAVY[i] * t) for i in range(3)
        )
        for x in range(width):
            pix[x, y] = color

    draw = ImageDraw.Draw(image)
    # Low-contrast orbital lines and a glow ring add depth without competing with text.
    draw.arc((-72, 8, 214, 282), 205, 335, fill=(28, 57, 88), width=2)
    draw.arc((-50, 32, 192, 255), 205, 335, fill=(20, 45, 72), width=2)
    draw.ellipse((38, 20, 126, 108), outline=(38, 85, 123), width=2)

    logo = _render_mark(72, include_tile=True)
    image.paste(logo, ((width - 72) // 2, 28), logo)
    draw = ImageDraw.Draw(image)
    _centered_text(draw, width // 2, 118, "MySQL IDLE", _font(16, True), WHITE)
    _centered_text(draw, width // 2, 143, "SQL WORKSPACE", _font(8, True), CYAN)

    draw.rounded_rectangle((32, 171, 132, 174), radius=1, fill=BLUE)
    # Small capability chips establish a more intentional product identity.
    chips = (
        (12, 191, 57, 213, "QUERY"),
        (60, 191, 105, 213, "BROWSE"),
        (108, 191, 153, 213, "EXPORT"),
    )
    for x0, y0, x1, y1, label in chips:
        draw.rounded_rectangle(
            (x0, y0, x1, y1), radius=5,
            fill=(18, 39, 61), outline=(39, 76, 108), width=1,
        )
        _centered_text(
            draw, (x0 + x1) // 2, y0 + 7, label, _font(6, True), PALE_CYAN
        )

    # Stylized result rows suggest a real SQL workspace instead of stock artwork.
    draw.rounded_rectangle((20, 235, 144, 240), radius=2, fill=(46, 74, 102))
    draw.rounded_rectangle((20, 247, 117, 252), radius=2, fill=(36, 60, 86))
    draw.rounded_rectangle((20, 259, 132, 264), radius=2, fill=(36, 60, 86))
    draw.ellipse((20, 281, 27, 288), fill=CYAN)
    draw.text((34, 279), "MySQL + MariaDB", font=_font(7, True), fill=MUTED)
    return image


def _wizard_small() -> Image.Image:
    image = Image.new("RGB", (55, 55), WHITE)
    mark = _render_mark(47, include_tile=True)
    image.paste(mark, ((55 - 47) // 2, (55 - 47) // 2), mark)
    return image


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    icon = _render_mark(256, include_tile=True)
    icon.save(
        ASSETS / "mysqlidle.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
               (64, 64), (128, 128), (256, 256)],
    )
    _wizard_image().save(ASSETS / "wizard-image.bmp", format="BMP")
    _wizard_small().save(ASSETS / "wizard-small.bmp", format="BMP")
    print(
        "Generated database/SQL-prompt product icon and polished Inno Setup artwork."
    )


if __name__ == "__main__":
    main()
