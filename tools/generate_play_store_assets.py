#!/usr/bin/env python3
"""Generate dimension-checked Google Play artwork and shared 512px app branding."""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

NAVY = (11, 16, 32)
PANEL = (17, 26, 43)
PANEL2 = (20, 31, 50)
LINE = (42, 56, 80)
TEXT = (237, 243, 255)
MUTED = (158, 172, 195)
ACCENT = (97, 168, 255)
BLUE = (37, 99, 235)
CYAN = (34, 211, 238)
GREEN = (102, 217, 167)
PAPER = (248, 250, 252)
INK = (15, 23, 42)
LIGHT_MUTED = (100, 116, 139)
WHITE = (255, 255, 255)


def font(size: int, bold: bool = False, mono: bool = False):
    candidates = (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "C:/Windows/Fonts/consola.ttf"]
        if mono else
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/seguisb.ttf", "C:/Windows/Fonts/arialbd.ttf"]
        if bold else
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"]
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def gradient(size, top=NAVY, bottom=(16, 24, 39)):
    w, h = size
    im = Image.new("RGB", size)
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(1, h - 1)
        t = t * t * (3 - 2 * t)
        c = tuple(round(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        d.line((0, y, w, y), fill=c)
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((int(w * .48), -int(h * .30), int(w * 1.05), int(h * .34)), fill=(37, 99, 235, 45))
    glow = glow.filter(ImageFilter.GaussianBlur(max(18, w // 30)))
    return Image.alpha_composite(im.convert("RGBA"), glow).convert("RGB")


def logo_from(path: Path, size=512):
    with Image.open(path) as source:
        source.load()
        logo = source.convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    return logo.filter(ImageFilter.UnsharpMask(radius=max(1, size // 160), percent=110, threshold=3))


def roundbox(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def centered(draw, xy, text, fnt, fill):
    draw.text(xy, text, font=fnt, fill=fill, anchor="mm")


def paragraph(draw, xy, text, fnt, fill, width, leading=1.25, max_lines=None):
    x, y = xy
    lines, line = [], ""
    for word in text.split():
        candidate = word if not line else line + " " + word
        if draw.textbbox((0, 0), candidate, font=fnt)[2] <= width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    if max_lines:
        lines = lines[:max_lines]
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += int(fnt.size * leading)
    return y


def field(draw, x, y, w, label, value, dark=True, hint=None, height=67):
    label_color = MUTED if dark else LIGHT_MUTED
    text_color = TEXT if dark else INK
    draw.text((x, y), label, font=font(22, True), fill=label_color)
    roundbox(draw, (x, y + 32, x + w, y + 32 + height), 13,
             (9, 17, 31) if dark else WHITE,
             outline=(52, 68, 94) if dark else (203, 213, 225), width=2)
    value_font = font(24)
    v = value
    while draw.textbbox((0, 0), v, font=value_font)[2] > w - 30 and len(v) > 5:
        v = v[:-4] + "…"
    draw.text((x + 16, y + 32 + (height - value_font.size) // 2, ), v, font=value_font, fill=text_color)
    end = y + 32 + height
    if hint:
        end = paragraph(draw, (x, end + 8), hint, font(18), label_color, w, 1.18)
    return end


def button(draw, x, y, w, text, primary=True, dark=True, h=68):
    fill = BLUE if primary else ((28, 40, 60) if dark else (241, 245, 249))
    outline = (75, 129, 220) if primary else (52, 68, 94)
    roundbox(draw, (x, y, x + w, y + h), 15, fill, outline, 2)
    centered(draw, (x + w / 2, y + h / 2), text, font(25, True), WHITE if primary or dark else INK)


def status_bar(draw, w, dark=True):
    fg = TEXT if dark else INK
    draw.text((38, 22), "9:41", font=font(23, True), fill=fg)
    x = w - 158
    for idx, h in enumerate((10, 15, 20, 25)):
        roundbox(draw, (x + idx * 12, 43 - h, x + idx * 12 + 7, 43), 2, fg)
    draw.arc((w - 94, 12, w - 54, 49), 205, 335, fill=fg, width=4)
    draw.arc((w - 84, 23, w - 64, 43), 205, 335, fill=fg, width=4)
    roundbox(draw, (w - 44, 20, w - 13, 39), 5, None, fg, 2)
    roundbox(draw, (w - 40, 24, w - 20, 35), 2, fg)


def brand_header(im, logo, connected=False, scale=1):
    d = ImageDraw.Draw(im)
    w = im.width
    d.rectangle((0, 0, w, 156), fill=(11, 16, 32))
    d.line((0, 155, w, 155), fill=LINE, width=2)
    mark = logo.resize((92, 92), Image.Resampling.LANCZOS)
    im.paste(mark, (34, 32), mark)
    d.text((148, 36), "MySQL IDLE", font=font(44, True), fill=TEXT)
    d.text((148, 91), "Android companion · SQL workspace", font=font(25), fill=MUTED)
    label = "Connected" if connected else "Not connected"
    bw = 190 if connected else 225
    roundbox(d, (w - bw - 30, 54, w - 30, 106), 24,
             (19, 54, 48) if connected else (35, 47, 68), LINE, 2)
    centered(d, (w - bw / 2 - 30, 80), label, font(21, True), GREEN if connected else MUTED)


def panel(draw, x, y, w, h, title):
    roundbox(draw, (x, y, x + w, y + h), 26, PANEL, LINE, 2)
    draw.text((x + 28, y + 24), title, font(32, True), fill=TEXT)


def phone_connect(logo, path):
    w, h = 1080, 1920
    im = Image.new("RGB", (w, h), PAPER); d = ImageDraw.Draw(im); status_bar(d, w, False)
    im.paste(logo.resize((140, 140), Image.Resampling.LANCZOS), (44, 100), logo.resize((140, 140), Image.Resampling.LANCZOS))
    d.text((214, 112), "MySQL IDLE", font=font(57, True), fill=INK)
    d.text((216, 182), "Mobile companion", font=font(38), fill=BLUE)
    y = 305; d.text((54, y), "Connect to the desktop", font=font(42, True), fill=INK); y += 54
    d.text((54, y), "companion", font=font(42, True), fill=INK); y += 74
    y = paragraph(d, (54, y), "On Windows, open Tools → Android / Mobile Companion. Enter the HTTPS address and compare the full SHA-256 fingerprint before connecting.", font(28), LIGHT_MUTED, 960, 1.28) + 28
    y = field(d, 54, y, 972, "Desktop companion URL", "https://192.168.1.20:8765", False, height=76) + 22
    y = field(d, 54, y, 972, "Desktop certificate SHA-256 fingerprint", "AA:BB:CC:… (64 hex digits)", False, height=76) + 18
    y = paragraph(d, (54, y), "HTTPS is required. Use a trusted private network and verify the fingerprint shown on Windows.", font(25), LIGHT_MUTED, 960, 1.25) + 24
    button(d, 54, y, 972, "Verify and connect", True, False, 80); y += 112
    d.text((54, y), "Network security", font=font(31, True), fill=INK); y += 49
    paragraph(d, (54, y), "The app pins the desktop HTTPS certificate. Only private LAN IPv4 addresses are accepted. Database credentials are not saved by this app.", font(23), LIGHT_MUTED, 960, 1.25)
    d.text((54, 1790), "Privacy Policy", font=font(24, True), fill=BLUE)
    im.rounded_rectangle((450, 1883, 630, 1892), 5, fill=(31, 41, 55))
    im.save(path, format="PNG", optimize=True)


def phone_pair(logo, path):
    w, h = 1080, 1920
    im = gradient((w, h)); d = ImageDraw.Draw(im); status_bar(d, w); brand_header(im, logo, False); d = ImageDraw.Draw(im)
    x, y, pw = 42, 190, 996; panel(d, x, y, pw, 1255, "Unlock and pair with desktop"); y += 90
    y = paragraph(d, (x + 30, y), "Enter the same master password set on Windows and the temporary code shown in Tools → Android / Mobile Companion. Compare the certificate fingerprint before connecting.", font(24), MUTED, pw - 60, 1.32) + 26
    y = field(d, x + 30, y, pw - 60, "MySQL IDLE master password", "••••••••••••", True, "Checked over HTTPS; not saved on Android.", 68) + 24
    y = field(d, x + 30, y, pw - 60, "Temporary pairing code", "12345 67890", True, "Enter the current 10-digit code displayed on the desktop.", 68) + 30
    button(d, x + 30, y, pw - 60, "Unlock and pair", True, True, 78); y += 111
    roundbox(d, (x + 30, y, x + pw - 30, y + 90), 17, (21, 45, 44), (42, 86, 70), 2)
    d.ellipse((x + 54, y + 33, x + 74, y + 53), fill=GREEN)
    d.text((x + 90, y + 28), "Ready when both fields are supplied.", font=font(23, True), fill=GREEN)
    d.text((52, 1545), "SECURITY BUILT IN", font=font(22, True), fill=CYAN)
    paragraph(d, (52, 1588), "Certificate-pinned HTTPS · Private LAN only · Session expires after inactivity", font(23), MUTED, 950, 1.28)
    im.rounded_rectangle((450, 1883, 630, 1892), 5, fill=(226, 232, 240))
    im.save(path, format="PNG", optimize=True)


def phone_connection(logo, path):
    w, h = 1080, 1920
    im = gradient((w, h)); d = ImageDraw.Draw(im); status_bar(d, w); brand_header(im, logo, True); d = ImageDraw.Draw(im)
    x, y, pw = 42, 190, 996; panel(d, x, y, pw, 1115, "MySQL connection"); x0, y = x + 30, y + 90; fw = pw - 60
    y = field(d, x0, y, fw // 2 - 10, "Host (as seen by desktop)", "localhost", True, height=58) + 10
    field(d, x0 + fw // 2 + 10, y - 100, fw // 2 - 10, "Port", "3306", True, height=58)
    y += 12
    y = field(d, x0, y, fw, "Username", "db_user", True, height=58) + 12
    y = field(d, x0, y, fw, "Password (not saved)", "••••••••••", True, "Hidden by default and cleared after a successful connection.", 58) + 14
    roundbox(d, (x0, y, x0 + fw, y + 68), 12, (9, 17, 31), (52, 68, 94), 2)
    d.rectangle((x0 + 18, y + 20, x0 + 47, y + 49), outline=ACCENT, width=3)
    d.line((x0 + 23, y + 34, x0 + 30, y + 41, x0 + 43, y + 25), fill=ACCENT, width=3)
    d.text((x0 + 62, y + 20), "Require verified TLS to MySQL", font=font(22, True), fill=TEXT); y += 84
    y = field(d, x0, y, fw, "MySQL CA certificate path (optional)", r"C:\certs\mysql-ca.pem", True, height=50) + 12
    y = field(d, x0, y, fw, "Database (optional)", "sales", True, height=50) + 16
    button(d, x0, y, fw, "Connect to MySQL", True, True, 67)
    panel(d, 42, 1370, 996, 295, "Before you connect")
    paragraph(d, (76, 1440), "The Windows desktop makes the MySQL connection. Use a least-privilege database account and a trusted private network.", font(24), MUTED, 900, 1.32)
    im.rounded_rectangle((450, 1883, 630, 1892), 5, fill=(226, 232, 240))
    im.save(path, format="PNG", optimize=True)


def phone_query(logo, path):
    w, h = 1080, 1920
    im = gradient((w, h)); d = ImageDraw.Draw(im); status_bar(d, w); brand_header(im, logo, True); d = ImageDraw.Draw(im)
    roundbox(d, (42, 178, 1038, 246), 16, (17, 55, 48), (44, 91, 75), 2)
    d.ellipse((68, 202, 88, 222), fill=GREEN); d.text((108, 191), "Connected to MySQL", font=font(25, True), fill=GREEN)
    panel(d, 42, 274, 996, 560, "SQL editor")
    d.text((76, 337), "Ctrl/⌘ + Enter to run", font=font(21), fill=MUTED)
    roundbox(d, (74, 382, 1006, 557), 13, (7, 15, 28), (52, 68, 94), 2)
    d.text((100, 413), "SELECT 1 AS status;", font=font(30, mono=True), fill=(124, 211, 255))
    d.text((100, 472), "-- quick check", font=font(26, mono=True), fill=(119, 157, 178))
    button(d, 74, 585, 220, "Run SQL", True, True, 60); button(d, 310, 585, 160, "Clear", False, True, 60)
    button(d, 486, 585, 210, "Previous", False, True, 60); button(d, 712, 585, 210, "Next", False, True, 60)
    d.text((76, 666), "Quick SQL template…", font=font(22), fill=MUTED); d.text((76, 714), "1/50 queries in memory", font=font(19), fill=MUTED)
    panel(d, 42, 770, 996, 490, "Result")
    button(d, 730, 822, 278, "Export complete CSV", False, True, 54)
    roundbox(d, (74, 900, 1006, 1000), 12, (9, 17, 31), (52, 68, 94), 2)
    d.text((96, 932), "1 row  ·  1 column", font=font(22, True), fill=GREEN)
    roundbox(d, (74, 1020, 1006, 1203), 12, (9, 17, 31), (52, 68, 94), 2)
    d.rectangle((75, 1021, 1005, 1070), fill=(30, 45, 67))
    d.text((100, 1033), "status", font=font(22, True), fill=TEXT); d.line((74, 1071, 1006, 1071), fill=LINE, width=2)
    d.text((100, 1090), "1", font=font(25, mono=True), fill=TEXT)
    panel(d, 42, 1290, 996, 320, "Session controls")
    paragraph(d, (76, 1360), "Query history stays in memory for the active session and clears when you disconnect or the session expires.", font(24), MUTED, 900, 1.32)
    im.rounded_rectangle((450, 1883, 630, 1892), 5, fill=(226, 232, 240))
    im.save(path, format="PNG", optimize=True)


def landscape(path, title, mode):
    w, h = 1920, 1080
    im = gradient((w, h)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, 110), fill=(8, 14, 27)); d.line((0, 109, w, 109), fill=LINE, width=2)
    d.text((46, 22), "MySQL IDLE", font=font(42, True), fill=TEXT)
    d.text((48, 72), "Android companion · responsive SQL workspace", font=font(21), fill=MUTED)
    roundbox(d, (w - 310, 30, w - 44, 80), 23, (18, 52, 46), (39, 83, 70), 2)
    centered(d, (w - 177, 55), "Connected to desktop", font(19, True), GREEN)
    d.text((54, 140), title, font=font(33, True), fill=TEXT)
    if mode == "editor":
        panel(d, 46, 190, 1120, 570, "SQL editor")
        d.text((80, 252), "Ctrl/⌘ + Enter to run", font=font(20), fill=MUTED)
        roundbox(d, (78, 300, 1134, 520), 14, (7, 15, 28), (52, 68, 94), 2)
        d.text((110, 335), "SELECT 1 AS status;", font=font(35, mono=True), fill=(124, 211, 255))
        button(d, 78, 554, 188, "Run SQL", True, True, 60)
        button(d, 282, 554, 150, "Clear", False, True, 60)
        button(d, 448, 554, 210, "Previous", False, True, 60)
        button(d, 674, 554, 184, "Next", False, True, 60)
        panel(d, 1200, 190, 674, 570, "Result")
        roundbox(d, (1240, 275, 1834, 362), 12, (9, 17, 31), (52, 68, 94), 2)
        d.text((1270, 305), "1 row · 1 column", font=font(24, True), fill=GREEN)
        roundbox(d, (1240, 382, 1834, 520), 12, (9, 17, 31), (52, 68, 94), 2)
        d.rectangle((1241, 383, 1833, 438), fill=(30, 45, 67))
        d.text((1270, 397), "status", font=font(23, True), fill=TEXT); d.text((1270, 460), "1", font=font(25, mono=True), fill=TEXT)
        panel(d, 46, 790, 1828, 190, "Session query history")
        d.text((84, 864), "SELECT 1 AS status;", font=font(25, mono=True), fill=TEXT)
        d.text((84, 916), "History is held in memory and cleared when the session ends.", font=font(21), fill=MUTED)
    elif mode == "connection":
        panel(d, 46, 190, 1130, 710, "MySQL connection")
        field(d, 84, 266, 500, "Host (as seen by desktop)", "localhost", True, height=50)
        field(d, 625, 266, 500, "Port", "3306", True, height=50)
        field(d, 84, 370, 500, "Username", "db_user", True, height=50)
        field(d, 625, 370, 500, "Password (not saved)", "••••••••••", True, height=50)
        field(d, 84, 474, 1040, "MySQL CA certificate path (optional)", r"C:\certs\mysql-ca.pem", True, height=50)
        field(d, 84, 575, 1040, "Database (optional)", "sales", True, height=50)
        button(d, 84, 686, 1040, "Connect to MySQL", True, True, 60)
        panel(d, 1210, 190, 664, 710, "Connection notes")
        paragraph(d, (1250, 278), "The Windows desktop makes the MySQL connection. Mobile requests go over certificate-pinned HTTPS.", font(26), MUTED, 580, 1.35)
        roundbox(d, (1250, 510, 1835, 625), 16, (16, 49, 43), (40, 83, 68), 2)
        d.text((1280, 540), "Credentials not saved on Android", font=font(21, True), fill=GREEN)
    elif mode == "pairing":
        panel(d, 46, 190, 890, 710, "Unlock and pair with desktop")
        paragraph(d, (84, 270), "Use the same MySQL IDLE master password set on Windows and the temporary 10-digit code shown by the desktop.", font(25), MUTED, 800, 1.35)
        field(d, 84, 375, 805, "MySQL IDLE master password", "••••••••••••", True, height=55)
        field(d, 84, 478, 805, "Temporary pairing code", "12345 67890", True, height=55)
        button(d, 84, 605, 805, "Unlock and pair", True, True, 64)
        panel(d, 980, 190, 894, 710, "Connection safety")
        for i, (title, body) in enumerate([
            ("Certificate fingerprint", "Compare the complete SHA-256 value with Windows."),
            ("Private network only", "Both devices should use a trusted local network."),
            ("Session expiry", "Sessions expire after 30 minutes of inactivity."),
        ]):
            y = 280 + i * 180
            d.ellipse((1020, y + 5, 1064, y + 49), fill=(22, 72, 62), outline=(55, 128, 102), width=2)
            centered(d, (1042, y + 27), "✓", font(25, True), GREEN)
            d.text((1090, y), title, font=font(23, True), fill=TEXT)
            paragraph(d, (1090, y + 40), body, font(20), MUTED, 710, 1.25)
    else:
        panel(d, 46, 190, 1828, 710, "SQL results · session workspace")
        d.text((84, 268), "SELECT 1 AS status;", font=font(33, mono=True), fill=(124, 211, 255))
        roundbox(d, (84, 340, 1835, 430), 12, (9, 17, 31), (52, 68, 94), 2)
        d.text((120, 370), "1 row · 1 column", font=font(24, True), fill=GREEN)
        roundbox(d, (84, 450, 1835, 710), 12, (9, 17, 31), (52, 68, 94), 2)
        d.rectangle((85, 451, 1834, 518), fill=(30, 45, 67))
        d.text((120, 472), "status", font=font(25, True), fill=TEXT)
        d.line((84, 519, 1835, 519), fill=LINE, width=2); d.text((120, 550), "1", font=font(27, mono=True), fill=TEXT)
        d.text((120, 635), "Use Export complete CSV to save the returned result set.", font=font(21), fill=MUTED)
    im.save(path, format="PNG", optimize=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = p.parse_args()
    root = args.root.resolve()
    source = root / "assets" / "mysqlidle-logo.png"
    if not source.is_file():
        raise SystemExit("Required source logo not found: " + str(source))
    out = root / "dist" / "google-play-assets"
    out.mkdir(parents=True, exist_ok=True)
    logo = logo_from(source)
    # Google Play store icon: opaque square background, no rounded corners baked in.
    store_icon = Image.new("RGBA", (512, 512), NAVY + (255,))
    mark = logo.resize((448, 448), Image.Resampling.LANCZOS)
    store_icon.alpha_composite(mark, (32, 32))
    store_icon.convert("RGB").save(out / "app-icon-512.png", format="PNG", optimize=True)
    (root / "assets").mkdir(exist_ok=True)
    logo.save(root / "assets" / "mysqlidle-logo-highres.png", format="PNG", optimize=True)
    android_logo = root / "android-app/app/src/main/res/drawable-nodpi/ic_mysqlidle_logo.png"
    if not android_logo.parent.is_dir():
        raise SystemExit("Android icon resource folder not found: " + str(android_logo.parent))
    logo.save(android_logo, format="PNG", optimize=True)
    feature = gradient((1024, 500), (8, 18, 34), (16, 30, 50))
    fd = ImageDraw.Draw(feature)
    for i in range(5):
        yy = 60 + i * 84
        fd.arc((590, yy - 60, 1110, yy + 180), 190, 320, fill=(30, 61, 94), width=3)
    feature.alpha_composite(logo.resize((210, 210)), (64, 125))
    fd = ImageDraw.Draw(feature)
    fd.text((315, 114), "MySQL IDLE", font=font(62, True), fill=WHITE)
    fd.text((318, 194), "SQL workspace", font=font(44, True), fill=CYAN)
    fd.text((318, 257), "for MySQL & MariaDB", font=font(31), fill=TEXT)
    fd.line((318, 326, 890, 326), fill=(52, 76, 108), width=2)
    roundbox(fd, (318, 352, 620, 409), 22, (17, 43, 62), (41, 78, 108), 2)
    centered(fd, (469, 381), "WINDOWS DESKTOP", font(19, True), TEXT)
    roundbox(fd, (639, 352, 886, 409), 22, (17, 43, 62), (41, 78, 108), 2)
    centered(fd, (762, 381), "ANDROID COMPANION", font(17, True), TEXT)
    fd.text((318, 439), "Pair securely over a trusted private network", font=font(20), fill=MUTED)
    feature.convert("RGB").save(out / "feature-graphic-1024x500.png", format="PNG", optimize=True)
    phone_files = [
        ("phone-01-connect-and-verify-1080x1920.png", phone_connect),
        ("phone-02-unlock-and-pair-1080x1920.png", phone_pair),
        ("phone-03-mysql-connection-1080x1920.png", phone_connection),
        ("phone-04-sql-editor-and-results-1080x1920.png", phone_query),
    ]
    for name, fn in phone_files:
        fn(logo, out / name)
    wide = [
        ("01-sql-editor.png", "SQL editor and quick templates", "editor"),
        ("02-mysql-connection.png", "Connect through the desktop companion", "connection"),
        ("03-secure-pairing.png", "Pair with a trusted Windows desktop", "pairing"),
        ("04-query-results.png", "Review results and export CSV", "results"),
    ]
    for folder in ("tablet-7-inch", "tablet-10-inch", "desktop"):
        dest = out / folder
        dest.mkdir(exist_ok=True)
        for name, title, mode in wide:
            landscape(dest / name, title, mode)
    items = []
    for path in sorted(out.rglob("*.png")):
        with Image.open(path) as im:
            items.append({"file": path.relative_to(out).as_posix(), "width": im.width, "height": im.height, "bytes": path.stat().st_size})
    manifest = {
        "product": "MySQL IDLE Mobile",
        "notes": [
            "App icon is 512x512 PNG with an opaque background and no rounded corners baked in.",
            "Feature graphic is 1024x500 PNG.",
            "Phone screenshots are 1080x1920 PNG previews based on the committed UI. Verify against the final app on a real device before submission.",
            "Tablet and desktop screenshots are 1920x1080 PNG previews; upload only where those form factors apply and after validation.",
            "XR artwork is omitted because this product is not an XR application. Video fields are intentionally blank until a real public/unlisted YouTube video exists."
        ],
        "assets": items,
    }
    (out / "ASSET-MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    zip_path = root / "dist" / "MySQLIDLE-Play-Store-Assets.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(out.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(out.parent))
    print("Generated store icon, feature graphic, 4 phone screenshots and 12 landscape previews.")
    print("Packaged " + str(zip_path))


if __name__ == "__main__":
    main()
