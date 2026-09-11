#!/usr/bin/env python3
"""
NeonSky AI business card -- print-ready PDF generator.

Trim 3.5 x 2 in. Artwork is built at 3.75 x 2.25 in so 0.125 in of bleed sits
outside the cut on every edge. Output is vector, DeviceCMYK, fonts embedded,
with TrimBox / BleedBox / ArtBox set so the printer's imposition is automatic.

    python3 make_card.py            # writes dist/
    python3 make_card.py --proof    # also writes 300 dpi PNG proofs with guides

Everything below is measured in PostScript points (72 pt = 1 in).
"""

import argparse
import math
import os
import sys

import re

import pypdf
import segno
from pypdf.generic import DecodedStreamObject
from reportlab.lib.colors import CMYKColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
DIST = os.path.join(HERE, "dist")

# ---------------------------------------------------------------- geometry --
IN = 72.0
BLEED = 0.125 * IN                      # 9 pt of bleed on every edge
TRIM_W, TRIM_H = 3.5 * IN, 2.0 * IN     # 252 x 144
PAGE_W, PAGE_H = TRIM_W + 2 * BLEED, TRIM_H + 2 * BLEED   # 270 x 162
SAFE = BLEED                            # keep live matter 0.125 in inside trim
# live area in page coordinates
L, R = BLEED + SAFE, PAGE_W - BLEED - SAFE      # 18 .. 252
B, T = BLEED + SAFE, PAGE_H - BLEED - SAFE      # 18 .. 144

# ----------------------------------------------------------------- content --
NAME = "David Holoboff"
ROLE = ("Database Architect &", "Business Automation Specialist")
PHONE = "(587) 209-0457"
EMAIL = "david@neonskyai.com"
WEB = "neonskyai.com"
PLACE = "Camrose, Alberta  |  Remote Worldwide"
TAGLINE = "LOYALTY APPS FOR LOCAL BUSINESSES"
PILLARS = ("LOCAL", "BUSINESSES.", "REAL", "RESULTS.")
HEADLINE = (("YOUR OWN", "white"), ("LOYALTY APP.", "blue"),
            ("BUILT FOR", "white"), ("YOUR BUSINESS.", "white"))
SUBLINE = ("MORE CUSTOMERS. MORE REVENUE.", "LESS WORK.")
QR_CAPTION = ("SCAN TO SEE", "A DEMO")
QR_URL = "https://neonskyai.com/your-app.html"

# ------------------------------------------------------------------ colour --
# DeviceCMYK throughout -- no RGB, no spot colours, no transparency.
# Total area coverage peaks at 277%, inside the 300% most sheet-fed shops want.
NAVY_DEEP = CMYKColor(0.95, 0.78, 0.38, 0.66)   # ~ #041336
NAVY_MID = CMYKColor(0.96, 0.80, 0.36, 0.54)    # ~ #05174B
NAVY_LIFT = CMYKColor(0.95, 0.78, 0.32, 0.42)   # ~ #072164
BLUE = CMYKColor(0.70, 0.28, 0.00, 0.00)        # ~ #3D9BE4  brand accent
BLUE_LT = CMYKColor(0.44, 0.13, 0.00, 0.00)     # ~ #8AC2F0
WHITE = CMYKColor(0, 0, 0, 0)
MIST = CMYKColor(0.22, 0.10, 0.03, 0.00)        # ~ #C4D6E9  secondary copy
RULE = CMYKColor(0.55, 0.30, 0.10, 0.05)        # hairline dividers
BLACK = CMYKColor(0, 0, 0, 1.0)                 # QR: K-only, best for scanning

FONTS = {
    "regular": ("Inter", "Inter-Regular.ttf"),
    "medium": ("Inter-Medium", "Inter-Medium.ttf"),
    "semibold": ("Inter-SemiBold", "Inter-SemiBold.ttf"),
    "bold": ("Inter-Bold", "Inter-Bold.ttf"),
    "black": ("Inter-ExtraBold", "Inter-ExtraBold.ttf"),
}


def register_fonts():
    for key, (name, filename) in FONTS.items():
        path = os.path.join(FONT_DIR, filename)
        if not os.path.exists(path):
            sys.exit(f"missing font: {path}")
        pdfmetrics.registerFont(TTFont(name, path))
    return {k: v[0] for k, v in FONTS.items()}


F = None  # filled in by main()


# ------------------------------------------------------------------- text --
def width_of(text, font, size, tracking=0.0):
    w = pdfmetrics.stringWidth(text, font, size)
    return w + tracking * max(0, len(text) - 1)


def fit(text, font, size, max_w, tracking=0.0, floor=4.0):
    """Shrink until the line fits the column. Guards against a reflow ever
    pushing live copy past the safe area."""
    while size > floor and width_of(text, font, size, tracking) > max_w:
        size -= 0.1
    return round(size, 2)


INK = []   # every drawn run, for the safe-area check in verify()


def draw_text(c, x, y, text, font, size, color, tracking=0.0, align="left"):
    w = width_of(text, font, size, tracking)
    if align == "center":
        x -= w / 2.0
    elif align == "right":
        x -= w
    t = c.beginText(x, y)
    t.setFillColor(color)
    t.setFont(font, size)
    if tracking:
        t.setCharSpace(tracking)
    t.textOut(text)
    c.drawText(t)
    asc, desc = pdfmetrics.getAscentDescent(font, size)
    INK.append((text, x, y + desc, x + w, y + asc))
    return w


# ------------------------------------------------------------ backgrounds --
def background(c):
    """Diagonal three-stop navy. Runs to the page edge, so it covers the full
    bleed and the cut can drift without exposing white."""
    c.saveState()
    p = c.beginPath()
    p.rect(0, 0, PAGE_W, PAGE_H)
    c.clipPath(p, stroke=0, fill=0)
    c.linearGradient(0, PAGE_H, PAGE_W, 0,
                     [NAVY_DEEP, NAVY_MID, NAVY_LIFT],
                     positions=[0.0, 0.58, 1.0], extend=True)
    c.restoreState()


# -------------------------------------------------------------- svg paths --
PATH_TOKEN = re.compile(r"[MmLlHhVvCcSsQqTtZz]|-?\d*\.?\d+(?:[eE][-+]?\d+)?")


def svg_path(c, d, x, y, size, viewbox):
    """Turn an SVG path's `d` attribute into a ReportLab path, scaled so the
    viewBox spans `size` and anchored with its top-left corner at (x, y).

    SVG counts Y downwards and PDF counts it upwards, so the Y axis is
    flipped. Arcs ("A"/"a") are not handled -- no icon here uses one, and a
    silent wrong curve on a printed card is worse than a loud failure.
    """
    k = size / float(viewbox)
    X = lambda u: x + u * k
    Y = lambda v: y + size - v * k

    tokens = PATH_TOKEN.findall(d)
    path = c.beginPath()
    i, cmd = 0, None
    cur = start = (0.0, 0.0)
    prev_ctrl = None

    def num():
        nonlocal i
        i += 1
        return float(tokens[i - 1])

    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            if cmd in "Zz":
                path.close()
                cur = start
                continue
        rel = cmd.islower()
        ox, oy = cur if rel else (0.0, 0.0)

        if cmd in "Mm":
            cur = (ox + num(), oy + num())
            path.moveTo(X(cur[0]), Y(cur[1]))
            start = cur
            cmd = "l" if rel else "L"          # extra pairs are implicit lineto
            prev_ctrl = None
        elif cmd in "Ll":
            cur = (ox + num(), oy + num())
            path.lineTo(X(cur[0]), Y(cur[1]))
            prev_ctrl = None
        elif cmd in "Hh":
            cur = (ox + num(), cur[1])
            path.lineTo(X(cur[0]), Y(cur[1]))
            prev_ctrl = None
        elif cmd in "Vv":
            cur = (cur[0], oy + num())
            path.lineTo(X(cur[0]), Y(cur[1]))
            prev_ctrl = None
        elif cmd in "CcSs":
            if cmd in "Cc":
                c1 = (ox + num(), oy + num())
            else:                               # smooth: mirror the last control
                c1 = (2 * cur[0] - prev_ctrl[0], 2 * cur[1] - prev_ctrl[1]) \
                     if prev_ctrl else cur
            c2 = (ox + num(), oy + num())
            end = (ox + num(), oy + num())
            path.curveTo(X(c1[0]), Y(c1[1]), X(c2[0]), Y(c2[1]), X(end[0]), Y(end[1]))
            cur, prev_ctrl = end, c2
        elif cmd in "QqTt":
            if cmd in "Qq":
                q = (ox + num(), oy + num())
            else:
                q = (2 * cur[0] - prev_ctrl[0], 2 * cur[1] - prev_ctrl[1]) \
                    if prev_ctrl else cur
            end = (ox + num(), oy + num())
            c1 = (cur[0] + 2.0 / 3 * (q[0] - cur[0]), cur[1] + 2.0 / 3 * (q[1] - cur[1]))
            c2 = (end[0] + 2.0 / 3 * (q[0] - end[0]), end[1] + 2.0 / 3 * (q[1] - end[1]))
            path.curveTo(X(c1[0]), Y(c1[1]), X(c2[0]), Y(c2[1]), X(end[0]), Y(end[1]))
            cur, prev_ctrl = end, q
        else:
            raise ValueError(f"unsupported SVG path command: {cmd!r}")
    return path


# ------------------------------------------------------------- cloud mark --
def _circle_pt(cx, cy, r, ang):
    return cx + r * math.cos(ang), cy + r * math.sin(ang)


def _intersect_upper(c1, c2):
    """Upper intersection point of two circles, as (x, y)."""
    (x1, y1, r1), (x2, y2, r2) = c1, c2
    dx, dy = x2 - x1, y2 - y1
    d = math.hypot(dx, dy)
    a = (d * d + r1 * r1 - r2 * r2) / (2 * d)
    h = math.sqrt(max(0.0, r1 * r1 - a * a))
    mx, my = x1 + a * dx / d, y1 + a * dy / d
    p = (mx + h * dy / d, my - h * dx / d)
    q = (mx - h * dy / d, my + h * dx / d)
    return p if p[1] > q[1] else q


def cloud_path(c, x, y, w, circles, baseline):
    """Trace the union outline of three disks sitting on a flat base, as a
    polyline fine enough that the facets vanish at any print resolution."""
    cl = [(x + cx * w, y + cy * w, r * w) for cx, cy, r in circles]
    by = y + baseline * w
    left, mid, right = cl

    def foot(circ, direction):
        cx, cy, r = circ
        dx = math.sqrt(max(0.0, r * r - (by - cy) ** 2))
        return (cx + direction * dx, by)

    p0 = foot(left, -1)
    p1 = foot(right, +1)
    i_lm = _intersect_upper(left, mid)
    i_mr = _intersect_upper(mid, right)

    def ang(circ, pt):
        return math.atan2(pt[1] - circ[1], pt[0] - circ[0])

    arcs = [(right, ang(right, p1), ang(right, i_mr)),
            (mid, ang(mid, i_mr), ang(mid, i_lm)),
            (left, ang(left, i_lm), ang(left, p0))]

    path = c.beginPath()
    path.moveTo(*p0)
    path.lineTo(*p1)
    for (cx, cy, r), a0, a1 in arcs:
        sweep = (a1 - a0) % (2 * math.pi)          # always counter-clockwise
        steps = max(8, int(math.degrees(sweep) / 2))
        for i in range(1, steps + 1):
            path.lineTo(*_circle_pt(cx, cy, r, a0 + sweep * i / steps))
    path.close()
    return path


FRONT_CLOUD = [(0.22, 0.28, 0.20), (0.48, 0.38, 0.27), (0.76, 0.26, 0.19)]

# Material Symbols "call" (Apache 2.0) -- the tilted handset everyone reads as
# a phone. 24 x 24 viewBox.
PHONE_D = ("M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 "
           "1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 "
           "1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 "
           "2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z")


def logo_mark(c, x, y, w):
    """Two interlocking cloud outlines -- the smaller one trailing up and left,
    the way it reads on the proof."""
    c.saveState()
    c.setLineJoin(1)
    c.setLineCap(1)

    back = cloud_path(c, x - 0.04 * w, y + 0.33 * w, w * 0.55, FRONT_CLOUD, 0.10)
    c.setStrokeColor(BLUE_LT)
    c.setLineWidth(w * 0.050)
    c.drawPath(back, stroke=1, fill=0)

    front = cloud_path(c, x + 0.14 * w, y, w * 0.86, FRONT_CLOUD, 0.10)
    c.setStrokeColor(BLUE)
    c.setLineWidth(w * 0.062)
    c.drawPath(front, stroke=1, fill=0)
    c.restoreState()


# ------------------------------------------------------------ icon chips ---
def chip(c, cx, cy, r, kind):
    """Solid blue disc with a knocked-out white glyph. Every knockout sits on
    flat colour, so there is no transparency anywhere in the file."""
    c.setFillColor(BLUE)
    c.circle(cx, cy, r, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setStrokeColor(WHITE)
    s = r  # glyph half-size

    if kind == "phone":
        g = s * 1.50
        c.drawPath(svg_path(c, PHONE_D, cx - g / 2, cy - g / 2, g, 24.0),
                   stroke=0, fill=1)

    elif kind == "mail":
        w, h = s * 1.20, s * 0.86
        c.setLineWidth(s * 0.20)
        c.roundRect(cx - w / 2, cy - h / 2, w, h, s * 0.16, stroke=1, fill=0)
        p = c.beginPath()
        p.moveTo(cx - w / 2 + s * 0.10, cy + h / 2 - s * 0.10)
        p.lineTo(cx, cy - s * 0.10)
        p.lineTo(cx + w / 2 - s * 0.10, cy + h / 2 - s * 0.10)
        c.setLineJoin(1)
        c.drawPath(p, stroke=1, fill=0)

    elif kind == "web":
        c.setLineWidth(s * 0.18)
        c.circle(cx, cy, s * 0.62, stroke=1, fill=0)
        c.line(cx - s * 0.62, cy, cx + s * 0.62, cy)
        p = c.beginPath()   # meridian
        p.moveTo(cx, cy + s * 0.62)
        p.curveTo(cx - s * 0.46, cy + s * 0.22, cx - s * 0.46, cy - s * 0.22,
                  cx, cy - s * 0.62)
        p.curveTo(cx + s * 0.46, cy - s * 0.22, cx + s * 0.46, cy + s * 0.22,
                  cx, cy + s * 0.62)
        c.drawPath(p, stroke=1, fill=0)

    elif kind == "pin":
        rr = s * 0.50
        top = cy + s * 0.22
        p = c.beginPath()
        p.moveTo(cx, cy - s * 0.74)                       # point
        p.lineTo(cx - rr * 0.80, top - rr * 0.52)
        p.curveTo(cx - rr * 1.34, top - rr * 0.10, cx - rr * 0.92, top + rr * 0.96,
                  cx, top + rr * 0.96)
        p.curveTo(cx + rr * 0.92, top + rr * 0.96, cx + rr * 1.34, top - rr * 0.10,
                  cx + rr * 0.80, top - rr * 0.52)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
        c.setFillColor(BLUE)                              # knockout hole
        c.circle(cx, top + rr * 0.18, rr * 0.34, stroke=0, fill=1)
        c.setFillColor(WHITE)


# -------------------------------------------------------------------- QR ---
def draw_qr(c, x, y, size, url):
    """QR drawn as vector rectangles -- resolution independent, K-only ink.
    Horizontal runs are merged and overlapped a hair so no RIP can open a
    hairline seam between modules."""
    qr = segno.make(url, error="q")
    matrix = [list(row) for row in qr.matrix]
    n = len(matrix)
    m = size / float(n)
    c.setFillColor(BLACK)
    for r, row in enumerate(matrix):
        col = 0
        while col < n:
            if row[col]:
                run = col
                while run < n and row[run]:
                    run += 1
                c.rect(x + col * m, y + (n - r - 1) * m,
                       (run - col) * m + m * 0.004, m * 1.004, stroke=0, fill=1)
                col = run
            else:
                col += 1
    return qr.version


# ----------------------------------------------------------------- front ---
def draw_front(c):
    background(c)

    divider_x = 187.0
    col_r = divider_x - 9.0          # left column runs to here

    # --- logo lockup -------------------------------------------------------
    logo_mark(c, L, 127.0, 23.0)
    draw_text(c, L + 26.0, 128.5, "NeonSky", F["bold"], 15.0, WHITE)
    w = width_of("NeonSky ", F["bold"], 15.0)
    draw_text(c, L + 26.0 + w, 128.5, "AI", F["bold"], 15.0, BLUE)

    size = fit(TAGLINE, F["medium"], 5.3, col_r - L, tracking=0.92)
    draw_text(c, L, 119.5, TAGLINE, F["medium"], size, MIST, tracking=0.92)

    # --- name and role -----------------------------------------------------
    draw_text(c, L, 100.0, NAME, F["bold"], fit(NAME, F["bold"], 12.2, col_r - L),
              WHITE)
    role_size = min(fit(line, F["regular"], 6.2, col_r - L) for line in ROLE)
    for i, line in enumerate(ROLE):
        draw_text(c, L, 89.0 - i * 7.6, line, F["regular"], role_size, MIST)

    # --- contact rows ------------------------------------------------------
    rows = [("phone", PHONE), ("mail", EMAIL), ("web", WEB), ("pin", PLACE)]
    icon_r = 4.0
    icon_x, text_x = L + icon_r, L + 2 * icon_r + 7.0
    top, step = 65.0, 13.2
    contact_size = min(fit(text, F["regular"], 6.6, col_r - text_x)
                       for _, text in rows)
    for i, (kind, text) in enumerate(rows):
        y = top - i * step
        chip(c, icon_x, y + 2.1, icon_r, kind)
        draw_text(c, text_x, y, text, F["regular"], contact_size, WHITE)

    # --- divider + pillar copy --------------------------------------------
    c.setStrokeColor(RULE)
    c.setLineWidth(0.7)
    c.line(divider_x, 49.0, divider_x, 115.0)

    px = divider_x + 6.0
    size = min(fit(line, F["semibold"], 7.4, R - px - 6.0, tracking=0.45)
               for line in PILLARS)
    for i, line in enumerate(PILLARS):
        draw_text(c, px, 109.0 - i * 10.8, line, F["semibold"], size, WHITE,
                  tracking=0.45)


# ------------------------------------------------------------------ back ---
def draw_back(c):
    background(c)

    divider_x = 171.0
    col_r = divider_x - 10.0

    size = min(fit(line, F["black"], 16.0, col_r - L) for line, _ in HEADLINE)
    for i, (line, tone) in enumerate(HEADLINE):
        draw_text(c, L, 117.0 - i * 17.4, line, F["black"], size,
                  BLUE if tone == "blue" else WHITE)

    c.setFillColor(BLUE)
    c.rect(L, 54.5, 52.0, 2.1, stroke=0, fill=1)

    for i, line in enumerate(SUBLINE):
        s = fit(line, F["semibold"], 6.5, col_r - L, tracking=0.55)
        draw_text(c, L, 41.0 - i * 9.4, line, F["semibold"], s, MIST,
                  tracking=0.55)

    c.setStrokeColor(RULE)
    c.setLineWidth(0.7)
    c.line(divider_x, 29.0, divider_x, 121.0)

    # --- QR panel ----------------------------------------------------------
    panel = 62.0
    cx = (divider_x + 11.0 + R) / 2.0
    px, py = cx - panel / 2.0, 57.0
    c.setFillColor(WHITE)
    c.roundRect(px, py, panel, panel, 5.0, stroke=0, fill=1)
    quiet = panel * 0.105              # >= 4 modules of quiet zone
    version = draw_qr(c, px + quiet, py + quiet, panel - 2 * quiet, QR_URL)

    for i, line in enumerate(QR_CAPTION):
        s = fit(line, F["semibold"], 6.5, R - (divider_x + 8.0), tracking=0.5)
        draw_text(c, cx, 43.0 - i * 9.0, line, F["semibold"], s, WHITE,
                  tracking=0.5, align="center")
    return version


# ----------------------------------------------------------------- output --
def verify():
    """Nothing that must survive the cut may sit outside the safe area. A
    trimmer can drift; this is the check that says it will not matter."""
    bad = [(t, x0, y0, x1, y1) for t, x0, y0, x1, y1 in INK
           if x0 < L - 0.01 or x1 > R + 0.01 or y0 < B - 0.01 or y1 > T + 0.01]
    for t, x0, y0, x1, y1 in bad:
        print(f"  SAFE-AREA BREACH  {t!r}  x {x0:.1f}..{x1:.1f}  y {y0:.1f}..{y1:.1f}",
              file=sys.stderr)
    if bad:
        sys.exit(f"{len(bad)} element(s) outside the safe area "
                 f"(x {L:.0f}..{R:.0f}, y {B:.0f}..{T:.0f})")
    print(f"safe   {len(INK)} text runs, all inside "
          f"{(R-L)/IN:.2f} x {(T-B)/IN:.2f} in live area")


# ReportLab opens every page with "BT /F1 12 Tf 14.4 TL ET" -- a font set with
# no glyph behind it. It is what keeps Helvetica in the resource dictionary.
NOOP_FONT_RE = re.compile(rb"BT\s+/F\d+\s+[\d.]+\s+Tf\s+[\d.]+\s+TL\s+ET\s*")


def strip_unused_fonts(path):
    """ReportLab always declares Helvetica as the start-up font, whether or not
    a glyph of it is ever set. Left in place it shows up in preflight as a
    non-embedded font. Nothing references it, so drop it."""
    reader = pypdf.PdfReader(path)
    writer = pypdf.PdfWriter()
    removed = 0
    for page in reader.pages:
        stream = page.get_contents().get_data()
        trimmed = NOOP_FONT_RE.sub(b"", stream, count=1)
        if trimmed != stream:
            obj = DecodedStreamObject()
            obj.set_data(trimmed)
            page.replace_contents(obj)
            stream = trimmed
        resources = page.get("/Resources")
        fonts = resources.get_object().get("/Font") if resources else None
        if fonts is not None:
            fonts = fonts.get_object()
            for key in [k for k in list(fonts) if f"{k} ".encode() not in stream]:
                del fonts[key]
                removed += 1
        writer.add_page(page)
    with open(path, "wb") as fh:
        writer.write(fh)
    return removed


MARK_LEN = 14.0      # crop mark length
MARK_GAP = 4.0       # gap between the bleed edge and the start of a mark
MARK_MARGIN = MARK_LEN + MARK_GAP


def build_with_marks(path, title, painters):
    """Same artwork on a larger sheet with crop marks outside the bleed, for
    shops that would rather see marks than read a TrimBox."""
    w = PAGE_W + 2 * MARK_MARGIN
    h = PAGE_H + 2 * MARK_MARGIN
    c = canvas.Canvas(path, pagesize=(w, h), pageCompression=1)
    c.setTitle(title)
    c.setAuthor(NAME)
    c.setSubject("Business card artwork with crop marks -- trim 3.5 x 2 in")
    for painter in painters:
        c.setPageSize((w, h))
        c.setTrimBox((MARK_MARGIN + BLEED, MARK_MARGIN + BLEED,
                      MARK_MARGIN + BLEED + TRIM_W, MARK_MARGIN + BLEED + TRIM_H))
        c.setBleedBox((MARK_MARGIN, MARK_MARGIN, MARK_MARGIN + PAGE_W,
                       MARK_MARGIN + PAGE_H))
        c.saveState()
        c.translate(MARK_MARGIN, MARK_MARGIN)
        painter(c)
        c.restoreState()

        c.setStrokeColor(BLACK)
        c.setLineWidth(0.25)
        tx0, tx1 = MARK_MARGIN + BLEED, MARK_MARGIN + BLEED + TRIM_W
        ty0, ty1 = MARK_MARGIN + BLEED, MARK_MARGIN + BLEED + TRIM_H
        for ty in (ty0, ty1):
            c.line(0, ty, MARK_MARGIN - MARK_GAP, ty)
            c.line(w - MARK_MARGIN + MARK_GAP, ty, w, ty)
        for tx in (tx0, tx1):
            c.line(tx, 0, tx, MARK_MARGIN - MARK_GAP)
            c.line(tx, h - MARK_MARGIN + MARK_GAP, tx, h)
        c.showPage()
    c.save()


def set_boxes(c):
    """MediaBox is the bleed. TrimBox is the cut. Printers impose off these."""
    c.setPageSize((PAGE_W, PAGE_H))
    c.setCropBox((0, 0, PAGE_W, PAGE_H))
    c.setBleedBox((0, 0, PAGE_W, PAGE_H))
    c.setTrimBox((BLEED, BLEED, BLEED + TRIM_W, BLEED + TRIM_H))
    c.setArtBox((BLEED, BLEED, BLEED + TRIM_W, BLEED + TRIM_H))


def new_canvas(path, title):
    c = canvas.Canvas(path, pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    c.setTitle(title)
    c.setAuthor(NAME)
    c.setSubject("Business card artwork -- 3.5 x 2 in trim, 0.125 in bleed")
    c.setCreator("NeonSky AI")
    return c


def build(path, title, painters):
    c = new_canvas(path, title)
    version = None
    for painter in painters:
        set_boxes(c)
        version = painter(c) or version
        c.showPage()
    c.save()
    return version


def main():
    global F
    ap = argparse.ArgumentParser()
    ap.add_argument("--proof", action="store_true",
                    help="also render 300 dpi PNG proofs with trim/safe guides")
    args = ap.parse_args()

    F = register_fonts()
    os.makedirs(DIST, exist_ok=True)

    front = os.path.join(DIST, "FRONT.pdf")
    back = os.path.join(DIST, "BACK.pdf")
    both = os.path.join(DIST, "NeonSky-BusinessCard-PRINT.pdf")

    marks = os.path.join(DIST, "NeonSky-BusinessCard-PRINT-crop-marks.pdf")

    build(front, "NeonSky AI business card -- front", [draw_front])
    version = build(back, "NeonSky AI business card -- back", [draw_back])
    build(both, "NeonSky AI business card", [draw_front, draw_back])
    build_with_marks(marks, "NeonSky AI business card -- crop marks",
                     [draw_front, draw_back])

    print(f"trim   {TRIM_W/IN:.2f} x {TRIM_H/IN:.2f} in")
    print(f"bleed  {PAGE_W/IN:.2f} x {PAGE_H/IN:.2f} in ({BLEED/IN:.3f} in per edge)")
    print(f"QR     {QR_URL}  (version {version}, ECC Q)")
    verify()
    dropped = sum(strip_unused_fonts(p) for p in (front, back, both, marks))
    print(f"clean  {dropped} unused non-embedded font reference(s) removed")
    for p in (front, back, both, marks):
        print(f"wrote  {os.path.relpath(p, HERE)}  {os.path.getsize(p)/1024:.0f} KB")

    if args.proof:
        import proof
        proof.render_all()


if __name__ == "__main__":
    main()
