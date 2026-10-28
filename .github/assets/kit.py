"""Darkwave Schematic drawing kit: the fixed rules in code."""
import os
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
from outline import text

# The Kubernetes Icons Set (kubernetes/community, icons/svg/resources/unlabeled, Apache-2.0), unmodified in kubernetes-icons/
ICONS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kubernetes-icons')
SVG_NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG_NS)
_icons = {}

def icon_svg(name):
    """The icon's viewBox and drawing, with the editor's metadata, namespaced attributes and ids left out."""
    if name not in _icons:
        root = ET.parse(f'{ICONS}/{name}.svg').getroot()
        groups = [el for el in root if el.tag == f'{{{SVG_NS}}}g']
        for g in groups:
            for el in g.iter():
                for k in [k for k in el.attrib if k.startswith('{') or k == 'id']:
                    del el.attrib[k]
        _icons[name] = (root.get('viewBox'), ''.join(ET.tostring(g, encoding='unicode') for g in groups))
    return _icons[name]

THEMES = {
    'light': {'role': {'product': ('#1F6FA8', '#DCEBF6'), 'install': ('#145D4C', '#E3F0EC'), 'outside': ('#5E6878', '#F2F4F7')},
              'canvas': '#FFFFFF', 'title': '#0E1A26', 'sub': '#556274', 'frame_stroke': '#D3DAE3', 'dash': '#AEB9C6', 'conn': '#5E6878'},
    'dark': {'role': {'product': ('#58A6E0', '#12293D'), 'install': ('#4FB89A', '#10302A'), 'outside': ('#8B98A8', '#1B222B')},
             'canvas': '#0D1117', 'title': '#E6EDF3', 'sub': '#9AA7B5', 'frame_stroke': '#2D3746', 'dash': '#4B5668', 'conn': '#8B98A8'},
}
S = 0.6
LEGEND = [('product', 'Ships in the product'), ('install', 'Supplied by the install'), ('outside', 'Outside the mesh'),
          ('planned', 'Planned, v1.x')]
CREDIT = 'Icons from the Kubernetes Icons Set, Apache-2.0.'

class Fig:
    """One figure at 960 wide; its height is set by foot(), from the last thing drawn."""
    def __init__(self, title, desc, mode):
        self.w, self.h, self.head = 960, None, (title, desc)
        th = THEMES[mode]
        self.role, self.canvas, self.title, self.sub = th['role'], th['canvas'], th['title'], th['sub']
        self.frame_stroke, self.dash, self.conn = th['frame_stroke'], th['dash'], th['conn']
        self.o = []
    def t(self, font, s, size, x, y, fill, anchor='start'):
        d, adv = text(font, s, size, x, y, anchor=anchor); self.o.append(f'<path d="{d}" fill="{fill}"/>'); return adv
    def icon(self, name, x, y, size):
        vb, body = icon_svg(name)
        self.o.append(f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="{vb}">{body}</svg>')
    def node(self, x, y, w, role, title, sub=None, icon=None, code=False, planned=False, tag=None):
        """A node 72 high: its title in Inter SemiBold 18 and its subtitle in Inter 16, or IBM Plex Mono 16 where it is a
        code name (code). icon: a Kubernetes object's, 32 px left of the title. planned: dashed and unfilled. tag: one
        lower-case word naming its Kubernetes pattern, in Inter 16, 16 from the right edge of the title row."""
        st, fl, h = *self.role[role], 72
        if planned:
            self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{self.canvas}" stroke="{st}" stroke-width="1" stroke-dasharray="4 4"/>')
        else:
            self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fl}" stroke="{st}" stroke-width="1"/>')
        top = y + (h - (42 if sub else 22)) / 2
        tx = x + 16
        if icon:
            self.icon(icon, tx, y + 20, 32); tx += 44
        self.t('inter-semibold', title, 18, tx, top + 17, self.title)
        if tag: self.t('inter-regular', tag, 16, x + w - 16, top + 17, self.sub, 'end')
        if sub: self.t('mono' if code else 'inter-regular', sub, 16, tx, top + 38, self.sub)
    def label(self, label, x, y, icon=None, code=None):
        """A zone's or bus's label at baseline y, in Inter SemiBold 16, after its 24 px icon if it has one, then its
        code name in IBM Plex Mono 16."""
        if icon:
            self.icon(icon, x, y - 19, 24); x += 32
        if label: x += self.t('inter-semibold', label, 16, x, y, self.sub) + 8
        if code: self.t('mono', code, 16, x, y, self.sub)
    def zone(self, x, y, w, h, label, icon=None, code=None):
        """A zone: label at 24 in, baseline 32 down; its contents start 56 down."""
        self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{self.canvas}" stroke="{self.frame_stroke}" stroke-width="1"/>')
        self.label(label, x + 24, y + 32, icon, code)
    def pod(self, x, y, w, name, deployment):
        """An Agent's Pod frame, titled by its role beside the Pod icon, its Deployment's name under it in code, around
        its two containers: the agent runtime, which calls down to its sidecar, the agent MCP gateway, over a Unix
        socket. 280 high; the runtime's box starts 80 down."""
        self.zone(x, y, w, 280, name, 'pod')
        self.t('mono', deployment, 16, x + 24, y + 58, self.sub)
        self.node(x + 24, y + 80, w - 48, 'product', 'Agent Runtime', 'darkwave/agent-runtime', code=True)
        self.node(x + 24, y + 184, w - 48, 'product', 'Agent MCP Gateway', 'darkwave/agent-mcp-gateway', code=True, tag='sidecar')
        self.arrow([(x + w / 2, y + 152), (x + w / 2, y + 184)])
        self.vlabel(x + w / 2, y + 152, y + 184, 'Unix socket')
    def link(self, x0, y0, x1, y1, planned=False):
        dash = ' stroke-dasharray="4 4"' if planned else ''
        self.o.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" stroke="{self.conn}" stroke-width="1"{dash}/>')
    def container(self, x, y, w, h, label):
        self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="none" stroke="{self.dash}" stroke-width="1" stroke-dasharray="4 4"/>')
        self.t('inter-semibold', label, 16, x + 24, y + 32, self.sub)
    def arrow(self, pts, planned=False, r=4):
        """An orthogonal connector with rounded elbows; planned: dashed, to a part not yet built."""
        d = f'M {pts[0][0]} {pts[0][1]}'
        for i in range(1, len(pts) - 1):
            (x0, y0), (x1, y1), (x2, y2) = pts[i-1], pts[i], pts[i+1]
            sx = (x1 > x0) - (x1 < x0); sy = (y1 > y0) - (y1 < y0)
            tx = (x2 > x1) - (x2 < x1); ty = (y2 > y1) - (y2 < y1)
            d += f' L {x1 - sx*r} {y1 - sy*r} Q {x1} {y1} {x1 + tx*r} {y1 + ty*r}'
        d += f' L {pts[-1][0]} {pts[-1][1]}'
        dash = ' stroke-dasharray="4 4"' if planned else ''
        self.o.append(f'<path d="{d}" fill="none" stroke="{self.conn}" stroke-width="1" marker-end="url(#dw-arrow)"{dash}/>')
    def vlabel(self, x, y0, y1, s):
        """An arrow label on a vertical run at x from y0 to y1: 14 to its right, centred on the run."""
        self.t('inter-regular', s, 16, x + 14, (y0 + y1) / 2 + 6, self.sub)
    def hlabel(self, x0, x1, y, s):
        """An arrow label on a horizontal run at y from x0 to x1: 10 above it, centred on the run."""
        self.t('inter-regular', s, 16, (x0 + x1) / 2, y - 10, self.sub, 'middle')
    def join(self, x, y, role):
        st, _ = self.role[role]
        self.o.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{self.canvas}" stroke="{st}" stroke-width="1.5"/>')
    def foot(self, y, items, captions, credit=False):
        """The legend 48 below y, listing the items it names in LEGEND's order, then the captions and the credit
        line, all in Inter 16 at the margin; the legend and a long caption wrap where they would pass the right margin,
        and the canvas ends 40 below the last line."""
        x, base = 40, y + 61
        for key, words in LEGEND:
            if key not in items: continue
            if x + 30 + text('inter-regular', words, 16, 0, 0)[1] > self.w - 40:
                x, base = 40, base + 28
            if key == 'planned':
                self.o.append(f'<rect x="{x}" y="{base-13}" width="16" height="16" rx="4" fill="none" stroke="{self.conn}" stroke-width="1" stroke-dasharray="3 3"/>')
            else:
                st, fl = self.role[key]
                self.o.append(f'<rect x="{x}" y="{base-13}" width="16" height="16" rx="4" fill="{fl}" stroke="{st}" stroke-width="1"/>')
            x += 24 + self.t('inter-regular', words, 16, x + 24, base, self.sub) + 32
        for caption in captions:
            line = ''
            for word in caption.split(' '):
                if line and text('inter-regular', f'{line} {word}', 16, 0, 0)[1] > self.w - 80:
                    base += 28
                    self.t('inter-regular', line, 16, 40, base, self.sub)
                    line = word
                else:
                    line = f'{line} {word}' if line else word
            base += 28
            self.t('inter-regular', line, 16, 40, base, self.sub)
        if credit:
            base += 28
            self.t('inter-regular', CREDIT, 16, 40, base, self.sub)
        self.h = -(-(base + 40) // 8) * 8
    def svg(self):
        w, h = self.w, self.h
        title, desc = self.head
        head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*S:g}" height="{h*S:g}" viewBox="0 0 {w} {h}">',
                f'<title>{escape(title)}</title>', f'<desc>{escape(desc)}</desc>',
                f'<defs><marker id="dw-arrow" markerUnits="userSpaceOnUse" viewBox="0 0 7 7" refX="6.5" refY="3.5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                f'<path d="M0.5 0.5L6.5 3.5L0.5 6.5" fill="none" stroke="{self.conn}" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>',
                f'<rect width="{w}" height="{h}" fill="{self.canvas}"/>']
        return '\n'.join(head + self.o + ['</svg>'])
