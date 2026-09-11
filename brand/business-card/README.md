# NeonSky AI — business card artwork

Print-ready PDFs for the 3.5 × 2 in card, plus the script that generates them.
Re-run the script any time a phone number, title, or URL changes; the layout
re-flows and re-checks itself rather than being re-drawn by hand.

## Send these to the printer

| File | Use |
| --- | --- |
| `dist/FRONT.pdf` | Front, single page, bleed included |
| `dist/BACK.pdf` | Back, single page, bleed included |
| `dist/NeonSky-BusinessCard-PRINT.pdf` | Both sides, page 1 front / page 2 back |
| `dist/NeonSky-BusinessCard-PRINT-crop-marks.pdf` | Same, with visible crop marks, for shops that ask for them |

Most shops want `FRONT.pdf` and `BACK.pdf`. Send the crop-marks version only if
they specifically ask for marks — it is the same artwork on a larger sheet.

`dist/clean-front.png` / `dist/clean-back.png` are 300 dpi on-screen proofs.
`dist/proof-*.png` are the same with trim and safe lines drawn on top.

## Specification

- **Trim** 3.5 × 2 in (landscape), 252 × 144 pt
- **Artwork** 3.75 × 2.25 in — 0.125 in of bleed on every edge
- **Safe area** 3.25 × 1.75 in — all live copy sits inside it, verified on every build
- **Boxes** MediaBox and BleedBox = the full bleed; TrimBox and ArtBox = the cut line, so imposition is automatic
- **Colour** DeviceCMYK only. No RGB, no spot colours, no ICC profile attached — the shop applies its own press profile
- **Ink** peaks at 277% total area coverage, inside the usual 300% limit
- **Transparency** none. Every knockout sits on flat colour, so nothing needs flattening
- **Fonts** Inter, subset and embedded. No non-embedded font references
- **Vector** fully. Zero raster images, including the QR code — it stays crisp at any size

### Colour build

| Role | CMYK | Approx. |
| --- | --- | --- |
| Navy, deep | 95 / 78 / 38 / 66 | `#041336` |
| Navy, mid | 96 / 80 / 36 / 54 | `#05174B` |
| Navy, lift | 95 / 78 / 32 / 42 | `#072164` |
| Accent blue | 70 / 28 / 0 / 0 | `#3D9BE4` |
| Accent blue, light | 44 / 13 / 0 / 0 | `#8AC2F0` |
| Secondary copy | 22 / 10 / 3 / 0 | `#C4D6E9` |

The background is a three-stop linear gradient across the navies, corner to
corner. On an uncoated stock the navy will dry back a little; ask for a coated
or soft-touch stock if you want it to sit as dark as the proof.

### QR code

Encodes `https://neonskyai.com/your-app.html`, version 4, error correction
level Q, drawn as vector rectangles in K-only black on white with a quiet zone
wider than the required four modules. Change the destination by editing
`QR_URL` in `make_card.py` and re-running.

## Rebuilding

```bash
pip install reportlab segno pypdf pymupdf pillow
python3 make_card.py            # writes dist/*.pdf
python3 make_card.py --proof    # also writes the 300 dpi PNG proofs
```

The build fails loudly if any text run lands outside the safe area, so a longer
job title or a new phone number cannot quietly push copy into the trim.

## Icons

The contact icons are drawn as vector paths, not placed as images. The phone
is Material Symbols "call" (Apache 2.0) — the standard handset — parsed from
its SVG path at build time by `svg_path()` in `make_card.py`. That parser
handles any SVG path made of move/line/cubic/quadratic commands, so a supplied
logo SVG can be dropped in the same way: paste its `d` attribute and viewBox
size. Arcs (`A`/`a`) are rejected rather than approximated.

Inter is used under the SIL Open Font License 1.1 — see `fonts/OFL.txt`.
