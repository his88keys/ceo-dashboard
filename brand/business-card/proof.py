#!/usr/bin/env python3
"""Render on-screen proofs of the card PDFs at 300 dpi, with the trim and safe
lines drawn on top so the layout can be checked before it goes to the shop."""

import os

import fitz
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "dist")
DPI = 300
SCALE = DPI / 72.0
BLEED, TRIM_W, TRIM_H = 9.0, 252.0, 144.0
SAFE = 9.0

TRIM_RGB = (226, 96, 116)
SAFE_RGB = (86, 196, 176)


def dashed(draw, box, color, dash=9, gap=7, width=2):
    x0, y0, x1, y1 = box
    for a, b, horiz in ((x0, x1, True), (x0, x1, False)):
        y = y0 if horiz else y1
        x = a
        while x < b:
            draw.line([(x, y), (min(x + dash, b), y)], fill=color, width=width)
            x += dash + gap
    for a, b, left in ((y0, y1, True), (y0, y1, False)):
        x = x0 if left else x1
        y = a
        while y < b:
            draw.line([(x, y), (x, min(y + dash, b))], fill=color, width=width)
            y += dash + gap


def render(pdf_path, png_path, guides=True):
    doc = fitz.open(pdf_path)
    out = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        if guides:
            d = ImageDraw.Draw(img)
            t = BLEED * SCALE
            dashed(d, (t, t, t + TRIM_W * SCALE, t + TRIM_H * SCALE), TRIM_RGB)
            s = (BLEED + SAFE) * SCALE
            dashed(d, (s, s, s + (TRIM_W - 2 * SAFE) * SCALE,
                       s + (TRIM_H - 2 * SAFE) * SCALE), SAFE_RGB)
        target = png_path if len(doc) == 1 else png_path.replace(".png", f"-{i+1}.png")
        img.save(target, dpi=(DPI, DPI))
        out.append(target)
    doc.close()
    return out


def render_all():
    made = []
    for name, png in (("FRONT.pdf", "proof-front.png"), ("BACK.pdf", "proof-back.png")):
        made += render(os.path.join(DIST, name), os.path.join(DIST, png))
        made += render(os.path.join(DIST, name),
                       os.path.join(DIST, png.replace("proof-", "clean-")), guides=False)
    for p in made:
        print(f"wrote  dist/{os.path.basename(p)}")
    return made


if __name__ == "__main__":
    render_all()
