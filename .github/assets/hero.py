"""The Agent Mesh README banner: one wordmark, built with the Darkwave logo's own recipe
(darkwave, brand/tools/logo.py, function logo), AGENT MESH in place of TRADING, in brand blue.

Needs fontTools and brotli; Michroma is in fonts/ beside this file.
Run: python3 hero.py <out dir>"""
from __future__ import annotations

import sys
from pathlib import Path
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

MICHROMA = Path(__file__).resolve().parent / 'fonts' / 'michroma-latin-400-normal.woff2'
INK = {'dark': '#E6F2FB', 'light': '#0E1A26'}
BLUE = {'dark': '#4FB3EA', 'light': '#1F6FA8'}
# The wave's colours, the palette's darkwave and darkwave-glow, as the Darkwave logo draws it.
WAVE_COLOURS = {'dark': ('#3E9FD6', '#D2EEFF'), 'light': ('#1F6FA8', '#4FB3EA')}
GLOW_OPACITY = {'dark': (0.45, 0.7, 0.16), 'light': (0.28, 0.35, 0.22)}
EMBOLDEN = {'dark': (0, 0), 'light': (2.4, 1.4)}
WAVE = 'M 64 296 C 128 168, 192 168, 256 256 S 384 344, 448 216'
ART_H, ART_CY = 181, 285.5
W, LOCKUP_W, MARGIN = 1280, 576, 32
TITLE = 'Darkwave Agent Mesh'
DESC = 'The Darkwave Agent Mesh wordmark: the wave mark, DARKWAVE, and AGENT MESH beneath it in blue.'


def number(v: float) -> str:
    return f'{v:.2f}'.rstrip('0').rstrip('.')


def text_path(tt: TTFont, text: str, size: float, x: float, baseline: float, tracking: float) -> tuple[str, float]:
    glyphs, cmap, hmtx = tt.getGlyphSet(), tt.getBestCmap(), tt['hmtx']
    scale = size / tt['head'].unitsPerEm
    pen = SVGPathPen(glyphs, ntos=number)
    cursor = 0.0
    for ch in text:
        name = cmap[ord(ch)]
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x + cursor, baseline)))
        cursor += hmtx[name][0] * scale + tracking
    return pen.getCommands(), cursor - tracking


def cap_height(tt: TTFont, size: float) -> float:
    return tt['OS/2'].sCapHeight * size / tt['head'].unitsPerEm


def outline(colour: str, width: float) -> str:
    return f' stroke="{colour}" stroke-width="{width}" stroke-linejoin="round"' if width else ''


def wave_art(ns: str, mode: str) -> str:
    lo, hi = WAVE_COLOURS[mode]
    g, h, e = GLOW_OPACITY[mode]
    box = 'x="-30%" y="-80%" width="160%" height="260%"'
    return f"""<defs>
<linearGradient id="{ns}-core" x1="64" y1="0" x2="448" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{lo}" stop-opacity="0.65"/><stop offset="0.3" stop-color="{hi}"/><stop offset="0.7" stop-color="{lo}"/><stop offset="1" stop-color="{lo}" stop-opacity="0.9"/></linearGradient>
<filter id="{ns}-glow" {box}><feGaussianBlur stdDeviation="22"/></filter>
<filter id="{ns}-haze" {box}><feGaussianBlur stdDeviation="6"/></filter>
</defs>
<path d="{WAVE}" transform="translate(0 60)" fill="none" stroke="{lo}" stroke-opacity="{e}" stroke-width="5" stroke-linecap="round"/>
<path d="{WAVE}" fill="none" stroke="{lo}" stroke-opacity="{g}" stroke-width="40" stroke-linecap="round" filter="url(#{ns}-glow)"/>
<path d="{WAVE}" fill="none" stroke="{lo}" stroke-opacity="{h}" stroke-width="20" stroke-linecap="round" filter="url(#{ns}-haze)"/>
<path d="{WAVE}" fill="none" stroke="url(#{ns}-core)" stroke-width="13" stroke-linecap="round"/>"""


def lockup(mode: str) -> tuple[str, float, float]:
    """logo.py's logo(), with AGENT MESH as the sub-line, in brand blue: its inner markup, width and height."""
    tt = TTFont(MICHROMA)
    top_text, sub_text = 'DARKWAVE', 'AGENT MESH'
    top_size = 100.0
    top_cap = cap_height(tt, top_size)
    _, top_w = text_path(tt, top_text, top_size, 0, 0, top_size * 0.06)
    sub_size = top_size * 0.44
    _, raw_w = text_path(tt, sub_text, sub_size, 0, 0, 0)
    sub_track = (top_w - raw_w) / (len(sub_text) - 1)
    sub_cap = cap_height(tt, sub_size)
    gap = top_cap * 0.42
    block_h = top_cap + gap + sub_cap
    scale = block_h * 1.3 / ART_H
    pad, between = block_h * 0.55, block_h * 0.45
    tx = pad + 384 * scale + between
    height = block_h + 2 * pad
    top_base = pad + top_cap
    sub_base = top_base + gap + sub_cap
    top_d, _ = text_path(tt, top_text, top_size, tx, top_base, top_size * 0.06)
    sub_d, _ = text_path(tt, sub_text, sub_size, tx, sub_base, sub_track)
    width = tx + top_w + pad
    ax, ay = pad - 64 * scale, height / 2 - ART_CY * scale
    top_stroke, sub_stroke = EMBOLDEN[mode]
    inner = (f'<g transform="translate({ax:.2f} {ay:.2f}) scale({scale:.4f})">\n{wave_art(f"dwam-hero-{mode}", mode)}\n</g>\n'
             f'<path d="{top_d}" fill="{INK[mode]}"{outline(INK[mode], top_stroke)}/>\n'
             f'<path d="{sub_d}" fill="{BLUE[mode]}"{outline(BLUE[mode], sub_stroke)}/>')
    return inner, width, height


def build(mode: str) -> str:
    inner, lw, lh = lockup(mode)
    h = LOCKUP_W * lh / lw
    H = h + 2 * MARGIN
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H:.2f}" viewBox="0 0 {W} {H:.2f}">\n'
            f'<title>{TITLE}</title>\n<desc>{DESC}</desc>\n'
            f'<svg x="{(W - LOCKUP_W) / 2:g}" y="{MARGIN}" width="{LOCKUP_W}" height="{h:.2f}" viewBox="0 0 {lw:.2f} {lh:.2f}">\n'
            f'{inner}\n</svg>\n</svg>\n')


if __name__ == '__main__':
    for mode in ('light', 'dark'):
        (Path(sys.argv[1]) / f'agent-mesh-hero-{mode}.svg').write_text(build(mode))
