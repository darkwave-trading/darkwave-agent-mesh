"""The Agent Mesh README banner: the Darkwave logo unchanged, the product name beside it, the tagline. Flat, text outlined.

Run: DARKWAVE_BRAND_DIR=<brand dir> python3 hero.py <out dir>"""
import json, re, sys
from outline import text, BRAND

def logo_parts(mode):
    src = open(f'{BRAND}/logos/darkwave-logo-{mode}.svg').read()
    vb = re.search(r'viewBox="([^"]+)"', src).group(1)
    w0, h0 = map(float, vb.split()[2:])
    inner = src[src.index('>') + 1: src.rindex('</svg>')]
    # prefix ids so a lockup never collides with the logo it embeds elsewhere
    inner = inner.replace('dw-logo-', 'dwam-logo-')
    return vb, w0, h0, inner

def lockup(mode, name='Agent Mesh'):
    pal = json.load(open(f'{BRAND}/palette.json'))[mode]
    vb, w0, h0, inner = logo_parts(mode)
    gap = 64
    size = 150
    d, tw = text('inter-medium', name, size, 0, 0)
    W = w0 + gap * 2 + tw + 16
    H = h0
    x_div = w0 + gap
    base = H / 2 + size * 0.727 / 2          # Inter's cap height is 0.727 em: centre the caps
    d, _ = text('inter-medium', name, size, x_div + gap, base)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.2f} {H:.2f}">'
            f'<title>Darkwave Agent Mesh</title>'
            f'<svg x="0" y="0" width="{w0}" height="{h0}" viewBox="{vb}">{inner}</svg>'
            f'<line x1="{x_div:.1f}" y1="{H*0.2:.1f}" x2="{x_div:.1f}" y2="{H*0.8:.1f}" stroke="{pal["surface"]["border-strong"]}" stroke-width="4"/>'
            f'<path d="{d}" fill="{pal["text"]["heading"]}"/></svg>'), W, H

def build(mode='light'):
    pal = json.load(open(f'{BRAND}/palette.json'))[mode]
    s, t = pal['surface'], pal['text']
    W, H = 1280, 360
    lk, lw, lh = lockup(mode)
    inner = lk[lk.index('>') + 1: lk.rindex('</svg>')]
    sh = 88; sw = sh * lw / lh
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         '<title>Darkwave Agent Mesh</title>',
         f'<rect width="{W}" height="{H}" rx="16" fill="{s["bg"]}"/>',
         f'<svg x="96" y="96" width="{sw:.1f}" height="{sh}" viewBox="0 0 {lw:.2f} {lh:.2f}">{inner}</svg>']
    d, _ = text('inter-medium', 'An agent mesh for Kubernetes, on NATS.', 28, 96, 240, track=-0.01)
    o.append(f'<path d="{d}" fill="{t["primary"]}"/>')
    d, _ = text('inter-regular', 'Every message checked and recorded. Every action gated, performed at most once.', 20, 96, 276)
    o.append(f'<path d="{d}" fill="{t["secondary"]}"/>')
    o.append('</svg>')
    return '\n'.join(o)

if __name__ == '__main__':
    for mode in ('light', 'dark'):
        open(f'{sys.argv[1]}/agent-mesh-hero-{mode}.svg', 'w').write(build(mode))
