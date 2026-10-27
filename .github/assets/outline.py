"""Outlined text for the Agent Mesh README images: Inter and IBM Plex Mono shaped by HarfBuzz and drawn as SVG paths.

The Darkwave brand assets (palette.json, logos/, fonts/) are not in this repository: name their
directory in DARKWAVE_BRAND_DIR."""
import io, os, re
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
import uharfbuzz as hb

BRAND = os.environ['DARKWAVE_BRAND_DIR']
INTER = '/usr/share/fonts/opentype/inter/Inter-{}.otf'
FONTS = {
    'inter-semibold': INTER.format('SemiBold'),
    'inter-regular': INTER.format('Regular'),
    'inter-medium': INTER.format('Medium'),
    'mono': f'{BRAND}/fonts/ibm-plex-mono-latin-500-normal.woff2',
}
_cache = {}

def font(name):
    if name not in _cache:
        tt = TTFont(FONTS[name])
        tt.flavor = None
        buf = io.BytesIO(); tt.save(buf); data = buf.getvalue()
        tt = TTFont(io.BytesIO(data))
        face = hb.Face(hb.Blob(data)); f = hb.Font(face)
        _cache[name] = (tt, f, tt['head'].unitsPerEm)
    return _cache[name]

def text(name, s, size, x, y, anchor='start', track=0.0):
    """Return (path d, width). track is extra spacing in em."""
    tt, f, upem = font(name)
    buf = hb.Buffer(); buf.add_str(s); buf.guess_segment_properties()
    hb.shape(f, buf, {'kern': True, 'liga': True})
    sc = size / upem
    order = tt.getGlyphOrder(); gs = tt.getGlyphSet()
    adv = sum(p.x_advance for p in buf.glyph_positions) * sc + track * size * (len(s) - 1)
    ox = x - (adv if anchor == 'end' else adv / 2 if anchor == 'middle' else 0)
    pen = SVGPathPen(gs)
    cx = 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        g = order[info.codepoint]
        tp = TransformPen(pen, (sc, 0, 0, -sc, ox + cx + pos.x_offset * sc, y - pos.y_offset * sc))
        gs[g].draw(tp)
        cx += pos.x_advance * sc + track * size
    d = pen.getCommands()
    d = re.sub(r'(\d+\.\d{2})\d+', r'\1', d)
    return d, adv
