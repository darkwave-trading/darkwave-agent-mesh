"""Darkwave Schematic drawing kit: the fixed rules in code."""
from outline import text

THEMES = {
    'light': {'role': {'product': ('#1F6FA8', '#DCEBF6'), 'install': ('#145D4C', '#E3F0EC'), 'outside': ('#5E6878', '#F2F4F7')},
              'canvas': '#FFFFFF', 'title': '#0E1A26', 'sub': '#556274', 'frame_stroke': '#D3DAE3', 'dash': '#AEB9C6', 'conn': '#5E6878'},
    'dark': {'role': {'product': ('#58A6E0', '#12293D'), 'install': ('#4FB89A', '#10302A'), 'outside': ('#8B98A8', '#1B222B')},
             'canvas': '#0D1117', 'title': '#E6EDF3', 'sub': '#9AA7B5', 'frame_stroke': '#2D3746', 'dash': '#4B5668', 'conn': '#8B98A8'},
}
S = 2

class Fig:
    def __init__(self, w, h, title, desc, mode):
        self.w, self.h = w, h
        th = THEMES[mode]
        self.role, self.canvas, self.title, self.sub = th['role'], th['canvas'], th['title'], th['sub']
        self.frame_stroke, self.dash, self.conn = th['frame_stroke'], th['dash'], th['conn']
        self.o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*S}" height="{h*S}" viewBox="0 0 {w} {h}">',
                  f'<title>{title}</title>', f'<desc>{desc}</desc>',
                  f'<defs><marker id="dw-arrow" markerUnits="userSpaceOnUse" viewBox="0 0 7 7" refX="6.5" refY="3.5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                  f'<path d="M0.5 0.5L6.5 3.5L0.5 6.5" fill="none" stroke="{self.conn}" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>',
                  f'<rect width="{w}" height="{h}" fill="{self.canvas}"/>']
    def t(self, font, s, size, x, y, fill, anchor='start'):
        d, adv = text(font, s, size, x, y, anchor=anchor); self.o.append(f'<path d="{d}" fill="{fill}"/>'); return adv
    def node(self, x, y, w, h, role, title, sub=None, stack=False):
        st, fl = self.role[role]
        if stack:
            for d in (6, 3):
                self.o.append(f'<rect x="{x+d}" y="{y-d}" width="{w}" height="{h}" rx="8" fill="{fl}" stroke="{st}" stroke-width="1"/>')
        self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fl}" stroke="{st}" stroke-width="1"/>')
        block = 18 + (16 if sub else 0)
        top = y + (h - block) / 2
        self.t('inter-semibold', title, 14, x + 16, top + 13.5, self.title)
        if sub: self.t('inter-regular', sub, 12, x + 16, top + 18 + 12, self.sub)
    def entry(self, x, y, w, role, label, pending=False):
        st, fl = self.role[role]
        dash = ' stroke-dasharray="4 4"' if pending else ''
        self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="32" rx="8" fill="{"none" if pending else fl}" stroke="{st}" stroke-width="1"{dash}/>')
        self.t('mono', label, 11, x + 16, y + 20, self.title)
    def zone(self, x, y, w, h, label, line=None):
        self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{self.canvas}" stroke="{self.frame_stroke}" stroke-width="1"/>')
        self.t('inter-semibold', label, 12, x + 24, y + 28, self.sub)
        if line: self.t('inter-regular', line, 12, x + 24, y + 44, self.sub)
    def frame(self, x, y, w, h, label):
        self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{self.canvas}" stroke="{self.frame_stroke}" stroke-width="1"/>')
        self.t('inter-semibold', label, 12, x + 16, y + 21, self.sub)
    def link(self, x0, y0, x1, y1):
        self.o.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" stroke="{self.conn}" stroke-width="1"/>')
    def container(self, x, y, w, h, label):
        self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="none" stroke="{self.dash}" stroke-width="1" stroke-dasharray="4 4"/>')
        self.t('inter-semibold', label, 12, x + 24, y + 28, self.sub)
    def arrow(self, pts, r=4):
        d = f'M {pts[0][0]} {pts[0][1]}'
        for i in range(1, len(pts) - 1):
            (x0, y0), (x1, y1), (x2, y2) = pts[i-1], pts[i], pts[i+1]
            sx = (x1 > x0) - (x1 < x0); sy = (y1 > y0) - (y1 < y0)
            tx = (x2 > x1) - (x2 < x1); ty = (y2 > y1) - (y2 < y1)
            d += f' L {x1 - sx*r} {y1 - sy*r} Q {x1} {y1} {x1 + tx*r} {y1 + ty*r}'
        d += f' L {pts[-1][0]} {pts[-1][1]}'
        self.o.append(f'<path d="{d}" fill="none" stroke="{self.conn}" stroke-width="1" marker-end="url(#dw-arrow)"/>')
    def bus(self, x0, x1, y, role, label, sub):
        st, _ = self.role[role]
        self.o.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{st}" stroke-width="2"/>')
        self.t('inter-semibold', label, 12, x0, y + 24, self.sub)
        for i, line in enumerate(sub):
            self.t('inter-regular', line, 12, x0, y + 40 + i * 16, self.sub)
    def join(self, x, y, role):
        st, _ = self.role[role]
        self.o.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{self.canvas}" stroke="{st}" stroke-width="1.5"/>')
    def legend(self, x, y, caption='Arrows show who calls whom.', bus=False, stack=False):
        items = [('product', 'Ships in the product'), ('install', 'Supplied by the install'), ('outside', 'Outside the mesh')]
        for cx, (role, label) in zip((x, x + 168, x + 344), items):
            st, fl = self.role[role]
            if bus and role == 'install':
                self.o.append(f'<line x1="{cx}" y1="{y-4}" x2="{cx+16}" y2="{y-4}" stroke="{st}" stroke-width="2"/>')
                self.o.append(f'<circle cx="{cx+8}" cy="{y-4}" r="4" fill="{self.canvas}" stroke="{st}" stroke-width="1.5"/>')
                self.t('inter-regular', label, 12, cx + 24, y, self.sub)
            else:
                self.o.append(f'<rect x="{cx}" y="{y-10}" width="12" height="12" rx="3" fill="{fl}" stroke="{st}" stroke-width="1"/>')
                self.t('inter-regular', label, 12, cx + 20, y, self.sub)
        if stack:
            st, fl = self.role['product']
            for d in (4, 2, 0):  # the node stack's 3 px steps, scaled to the 12 px icon
                self.o.append(f'<rect x="{x + 520 + d}" y="{y - 10 - d}" width="12" height="12" rx="3" fill="{fl}" stroke="{st}" stroke-width="1"/>')
            self.t('inter-regular', 'Many of one kind', 12, x + 544, y, self.sub)
        if caption: self.t('inter-regular', caption, 12, self.w - 40, y, self.sub, 'end')
    def svg(self):
        return '\n'.join(self.o + ['</svg>'])
