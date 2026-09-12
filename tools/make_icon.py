"""自绘应用图标，生成 assets/tomato.png 与 assets/tomato.ico。

运行：python tools/make_icon.py
"""

import math
import os

from PIL import Image, ImageDraw, ImageFilter

SIZE = 1024
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "assets")
PREVIEW = os.path.join(ROOT, "tools", "preview.png")

TILE_TOP = (44, 40, 66)
TILE_BOTTOM = (24, 21, 38)
BODY = (232, 84, 84)
BODY_HILIGHT = (255, 150, 150)
LEAF = (61, 190, 107)
LEAF_DARK = (47, 150, 84)
STEM = (86, 150, 96)


def vertical_gradient(size, top, bottom):
    img = Image.new("RGB", (1, size))
    for y in range(size):
        t = y / (size - 1)
        img.putpixel((0, y), tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img.resize((size, size))


def make_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    # 圆角深色底
    radius = int(SIZE * 0.235)
    tile_mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(tile_mask).rounded_rectangle(
        [0, 0, SIZE - 1, SIZE - 1], radius=radius, fill=255)
    img.paste(vertical_gradient(SIZE, TILE_TOP, TILE_BOTTOM).convert("RGBA"), (0, 0), tile_mask)

    cx, cy = SIZE * 0.5, SIZE * 0.57
    rx, ry = SIZE * 0.30, SIZE * 0.285

    # 番茄本体
    body_mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(body_mask).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)

    body = Image.new("RGBA", (SIZE, SIZE), BODY + (255,))

    highlight = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(highlight).ellipse(
        [cx - rx * 0.9, cy - ry, cx + rx * 0.25, cy + ry * 0.15],
        fill=BODY_HILIGHT + (170,))
    highlight = highlight.filter(ImageFilter.GaussianBlur(SIZE * 0.055))
    body = Image.alpha_composite(body, highlight)

    shade = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(shade).ellipse(
        [cx - rx, cy + ry * 0.15, cx + rx, cy + ry * 1.1], fill=(0, 0, 0, 110))
    shade = shade.filter(ImageFilter.GaussianBlur(SIZE * 0.07))
    body = Image.alpha_composite(body, shade)

    img.paste(body, (0, 0), body_mask)

    # 果蒂叶片
    leaves = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ld = ImageDraw.Draw(leaves)
    topx, topy = cx, cy - ry * 0.82
    for ang in (-78, -40, 0, 40, 78):
        a = math.radians(ang - 90)
        length = SIZE * (0.20 if ang == 0 else 0.17)
        tip = (topx + math.cos(a) * length, topy + math.sin(a) * length)
        perp = a + math.pi / 2
        b = SIZE * 0.05
        shoulder = SIZE * 0.032
        p1 = (topx + math.cos(perp) * b, topy + math.sin(perp) * b)
        p2 = (topx - math.cos(perp) * b, topy - math.sin(perp) * b)
        s1 = (topx + math.cos(a) * (length * 0.6) + math.cos(perp) * shoulder,
              topy + math.sin(a) * (length * 0.6) + math.sin(perp) * shoulder)
        s2 = (topx + math.cos(a) * (length * 0.6) - math.cos(perp) * shoulder,
              topy + math.sin(a) * (length * 0.6) - math.sin(perp) * shoulder)
        ld.polygon([p1, s1, tip, s2, p2], fill=LEAF + (255,))
    # 中央小茎
    ld.polygon([(topx - SIZE * 0.012, topy + SIZE * 0.015),
                (topx, topy - SIZE * 0.055),
                (topx + SIZE * 0.012, topy + SIZE * 0.015)], fill=LEAF_DARK + (255,))
    leaves = leaves.filter(ImageFilter.GaussianBlur(SIZE * 0.006))
    img = Image.alpha_composite(img, leaves)

    return img


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    icon = make_icon()

    png = icon.resize((256, 256), Image.LANCZOS)
    png.save(os.path.join(OUT_DIR, "tomato.png"))

    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icon.save(os.path.join(OUT_DIR, "tomato.ico"), sizes=ico_sizes)

    # 预览：一排小尺寸
    strip = Image.new("RGBA", (16 + 24 + 32 + 48 + 64 + 128 + 16 * 6, 128), (240, 240, 240, 255))
    x = 8
    for s in (16, 24, 32, 48, 64, 128):
        thumb = icon.resize((s, s), Image.LANCZOS)
        strip.alpha_composite(thumb, (x, (128 - s) // 2))
        x += s + 16
    strip.save(PREVIEW)
    print("icon written to", OUT_DIR, "| preview:", PREVIEW)


if __name__ == "__main__":
    main()
