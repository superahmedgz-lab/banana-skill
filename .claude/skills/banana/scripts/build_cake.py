#!/usr/bin/env python3
"""Build cake-ready layouts (vertical 2:3 / horizontal 3:2) from a collage
image plus a perfectly rendered Arabic congratulation below it.

Arabic is shaped with arabic_reshaper + python-bidi so letters join and read
right-to-left correctly (no libraqm needed). Text is rendered with a real
Arabic font, so names are exact.
"""
import argparse
from PIL import Image, ImageDraw, ImageFont

# Pillow here is built with raqm, so it shapes + bidi-orders Arabic natively.
# Pass RAW logical text with direction="rtl"; do NOT pre-shape.

ARABIC = ("نبارك لعموم عائلة سعد بن محمد بن حسين الدوسري تخرج أبنائها "
          "إبراهيم ومحمد، وحفيدها محمد بن عبدالله، سائلين الله لهم "
          "مستقبلاً زاهراً حافلاً بالنجاح والتميز.")

FONT_PATH = "/tmp/fonts/Amiri-Bold.ttf"
CREAM_TOP = (248, 241, 228)
CREAM_BOT = (240, 228, 200)
GOLD = (190, 150, 70)
INK = (74, 47, 18)          # warm dark brown for text


def vgradient(w, h, top, bot):
    base = Image.new("RGB", (w, h), top)
    px = base.load()
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(top[0] + (bot[0] - top[0]) * t)
        g = int(top[1] + (bot[1] - top[1]) * t)
        b = int(top[2] + (bot[2] - top[2]) * t)
        for x in range(w):
            px[x, y] = (r, g, b)
    return base


def confetti(img):
    """Scatter subtle gold confetti flecks deterministically (no RNG)."""
    d = ImageDraw.Draw(img, "RGBA")
    w, h = img.size
    seed = 12345
    for i in range(80):
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        x = seed % w
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        y = seed % h
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        s = 4 + seed % 9
        d.rectangle([x, y, x + s, int(s * 0.5) + y], fill=(GOLD[0], GOLD[1], GOLD[2], 60))
    return img


def rtl_len(draw, text, font):
    return draw.textlength(text, font=font, direction="rtl")


def wrap(text, font, max_w, draw):
    words = text.split(" ")
    lines, cur = [], ""
    for wd in words:
        trial = wd if not cur else cur + " " + wd
        if rtl_len(draw, trial, font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def fit_text(draw, text, max_w, max_h, start=96, min_size=28):
    """Find the largest font size whose wrapped text fits in max_w x max_h."""
    for size in range(start, min_size - 1, -2):
        font = ImageFont.truetype(FONT_PATH, size)
        lines = wrap(text, font, max_w, draw)
        lh = int(size * 1.6)
        if lh * len(lines) <= max_h:
            return font, lines, lh
    font = ImageFont.truetype(FONT_PATH, min_size)
    return font, wrap(text, font, max_w, draw), int(min_size * 1.6)


def build(orientation, collage_path, out_path):
    if orientation == "vertical":
        W, H = 2000, 3000          # 2:3  (28cm x 42cm)
        margin = 90
        coll_w = W - 2 * margin
    else:
        W, H = 3000, 2000          # 3:2  (42cm x 28cm)
        margin = 90
        # leave a comfortable text band at the bottom
        coll_w = H - 2 * margin - 470

    canvas = vgradient(W, H, CREAM_TOP, CREAM_BOT)
    canvas = confetti(canvas)
    draw = ImageDraw.Draw(canvas)

    coll = Image.open(collage_path).convert("RGB")
    coll = coll.resize((coll_w, coll_w), Image.LANCZOS)   # source is square
    coll_x = (W - coll_w) // 2
    coll_y = margin
    # soft shadow + gold frame
    draw.rectangle([coll_x - 8, coll_y - 8, coll_x + coll_w + 8, coll_y + coll_w + 8], outline=GOLD, width=6)
    canvas.paste(coll, (coll_x, coll_y))

    # divider flourish
    band_top = coll_y + coll_w + 70
    cx = W // 2
    draw.line([(margin + 120, band_top), (W - margin - 120, band_top)], fill=GOLD, width=4)
    draw.ellipse([cx - 12, band_top - 12, cx + 12, band_top + 12], fill=GOLD)

    # text area
    text_top = band_top + 60
    text_max_w = W - 2 * (margin + 80)
    text_max_h = H - text_top - 90
    font, lines, lh = fit_text(draw, ARABIC, text_max_w, text_max_h)

    block_h = lh * len(lines)
    y = text_top + max(0, (text_max_h - block_h) // 2)
    for ln in lines:
        draw.text((W / 2, y), ln, font=font, fill=INK, direction="rtl", anchor="ma")
        y += lh

    canvas.save(out_path, "PNG", quality=95)
    print(out_path, f"{W}x{H}", f"font={font.size}", f"lines={len(lines)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--orientation", choices=["vertical", "horizontal"], required=True)
    ap.add_argument("--collage", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    build(a.orientation, a.collage, a.out)
