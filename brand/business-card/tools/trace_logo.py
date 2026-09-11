#!/usr/bin/env python3
"""Trace the NeonSky mark from a bitmap into logo.svg.

The card is an all-vector, CMYK-only file; placing a PNG in it would cost both.
So the supplied artwork is traced to Bezier outlines once, here, and the card
build consumes the resulting SVG path.

    python3 tools/trace_logo.py path/to/mark.png

Accuracy is checked by rendering the traced path back to a bitmap and
comparing it against the source mask -- the script refuses to write a trace
that does not agree with the original.

Supplying a real vector logo instead makes this step unnecessary: drop the SVG
in as logo.svg and the card build will use it directly.
"""

import math
import os
import sys

import numpy as np
import potrace
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "logo.svg")
BRAND = "#29ABE2"
UP = 8               # supersample before tracing, for sub-pixel smooth edges
MIN_IOU = 0.97


def points(curve):
    pts = [(curve.start_point.x, curve.start_point.y)]
    for seg in curve:
        pts.append((seg.end_point.x, seg.end_point.y))
        pts += [(seg.c.x, seg.c.y)] if seg.is_corner else \
               [(seg.c1.x, seg.c1.y), (seg.c2.x, seg.c2.y)]
    return pts


def is_frame(curve, w, h):
    """potracer emits the bitmap's own border as a subpath. That is the canvas,
    not the artwork."""
    xs, ys = zip(*points(curve))
    return ((max(xs) - min(xs)) / UP > w * 0.98
            and (max(ys) - min(ys)) / UP > h * 0.98
            and len(list(curve)) < 8)


def trace(src):
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    mask = np.array(im.split()[3].resize((w * UP, h * UP), Image.LANCZOS)) > 128
    if not mask.any():
        sys.exit("no opaque pixels -- is the artwork on a transparent ground?")

    curves = [c for c in potrace.Bitmap(mask).trace(
        turdsize=4, alphamax=1.0, opticurve=True, opttolerance=0.2)
        if not is_frame(c, w, h)]
    if not curves:
        sys.exit("nothing traced")

    # Crop to the artwork's own bounds so the asset carries no dead padding.
    # The origin is snapped to whole source pixels: a fractional offset would
    # misregister the verification crop below, and on strokes this thin a
    # sub-pixel shift costs several points of IoU.
    xs, ys = zip(*[p for c in curves for p in points(c)])
    x0, y0 = float(math.floor(min(xs))), float(math.floor(min(ys)))
    vw = (math.ceil(max(xs)) - x0) / UP
    vh = (math.ceil(max(ys)) - y0) / UP

    def n(v):
        return f"{v:.3f}".rstrip("0").rstrip(".")

    def P(p):
        return f"{n((p.x - x0) / UP)} {n((p.y - y0) / UP)}"

    d = []
    for c in curves:
        d.append("M" + P(c.start_point))
        for s in c:
            d.append("L" + P(s.c) + "L" + P(s.end_point) if s.is_corner
                     else "C" + P(s.c1) + " " + P(s.c2) + " " + P(s.end_point))
        d.append("Z")
    return "".join(d), vw, vh, mask, (x0, y0)


def check(d, vw, vh, mask, origin):
    """Render the trace back and compare it to the source, so a bad trace fails
    here rather than on a printed card."""
    sys.path.insert(0, HERE)
    import pymupdf
    from reportlab.lib.colors import CMYKColor
    from reportlab.pdfgen import canvas
    from reportlab.pdfgen.canvas import FILL_EVEN_ODD
    from make_card import svg_path

    scale = 8.0
    c = canvas.Canvas("/tmp/_trace_check.pdf", pagesize=(vw * scale, vh * scale))
    c.setFillColor(CMYKColor(0, 0, 0, 0))
    c.rect(0, 0, vw * scale, vh * scale, stroke=0, fill=1)
    c.setFillColor(CMYKColor(0, 0, 0, 1))
    c.drawPath(svg_path(c, d, 0, 0, vw * scale, (vw, vh)),
               stroke=0, fill=1, fillMode=FILL_EVEN_ODD)
    c.save()
    px = pymupdf.open("/tmp/_trace_check.pdf")[0].get_pixmap(
        matrix=pymupdf.Matrix(UP / scale, UP / scale), alpha=False)
    got = np.frombuffer(px.samples, np.uint8).reshape(px.height, px.width, 3)[..., 0] < 128

    x0, y0 = int(origin[0]), int(origin[1])
    crop = mask[y0:y0 + got.shape[0], x0:x0 + got.shape[1]]
    got = got[:crop.shape[0], :crop.shape[1]]
    iou = (got & crop).sum() / float((got | crop).sum())
    return iou


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    d, vw, vh, mask, origin = trace(sys.argv[1])
    iou = check(d, vw, vh, mask, origin)
    print(f"traced {vw:.2f} x {vh:.2f} units, {len(d)} chars, IoU {100*iou:.2f}%")
    if iou < MIN_IOU:
        sys.exit(f"trace disagrees with the source (IoU below {100*MIN_IOU:.0f}%)")

    def n(v):
        return f"{v:.3f}".rstrip("0").rstrip(".")

    with open(OUT, "w") as fh:
        fh.write(
            f"<!-- NeonSky AI mark, traced from {os.path.basename(sys.argv[1])}.\n"
            f"     Even-odd fill. Regenerate with tools/trace_logo.py. -->\n"
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n(vw)} {n(vh)}" '
            f'width="{n(vw)}" height="{n(vh)}">\n'
            f'  <path fill="{BRAND}" fill-rule="evenodd" d="{d}"/>\n</svg>\n')
    print(f"wrote {os.path.relpath(OUT, HERE)}")


if __name__ == "__main__":
    main()
