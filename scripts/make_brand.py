"""Render the brand images of the integration from the project mark and the Sora typeface.

Usage, from the repository root:
    uv run --with resvg-py --with fonttools --with brotli python scripts/make_brand.py . custom_components/csnet_home/brand

Home Assistant 2026.3 and later show the images of this folder instead of the
ones of the home-assistant/brands repository.
"""
import sys
from pathlib import Path
import resvg_py
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

repo = Path(sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
mark = (repo / "docs/images/mark.svg").read_text()
inner = mark[mark.index(">") + 1 : mark.rindex("</svg>")]

def font(weight):
    f = TTFont(repo / "docs/videos/engine/fonts/sora-latin.woff2")
    if "fvar" in f:
        f = instancer.instantiateVariableFont(f, {"wght": weight})
    return f

def text_path(f, text, size, x, baseline, tracking=0.0):
    gs, cmap, hmtx = f.getGlyphSet(), f.getBestCmap(), f["hmtx"]
    scale = size / f["head"].unitsPerEm
    d, cx = [], x
    for ch in text:
        name = cmap[ord(ch)]
        pen = SVGPathPen(gs)
        gs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, cx, baseline)))
        d.append(pen.getCommands())
        cx += hmtx[name][0] * scale + tracking
    return " ".join(d), cx - tracking

def logo(ink, sub):
    H = 256
    bold, medium = font(700), font(500)
    x0 = H + 44
    title, end1 = text_path(bold, "CSNet Home", 112, x0, 138)
    tag, end2 = text_path(medium, "UNOFFICIAL INTEGRATION", 34, x0 + 4, 204, tracking=5)
    W = int(max(end1, end2)) + 1
    return W, f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<g transform="scale({H/48})">{inner}</g>
<path d="{title}" fill="{ink}"/><path d="{tag}" fill="{sub}"/></svg>'''

def png(svg, name, width):
    (out / name).write_bytes(bytes(resvg_py.svg_to_bytes(svg_string=svg, width=width)))

icon = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">{inner}</svg>'
png(icon, "icon.png", 256); png(icon, "icon@2x.png", 512)
for prefix, ink, sub in (("", "#0b0712", "#6b5a78"), ("dark_", "#fff6d6", "#c9b8d6")):
    W, svg = logo(ink, sub)
    png(svg, f"{prefix}logo.png", W); png(svg, f"{prefix}logo@2x.png", W * 2)
print("ok", W)
