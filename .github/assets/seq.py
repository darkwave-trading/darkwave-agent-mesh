"""A high-level UML sequence diagram in the Darkwave Schematic style: lifelines named by boxes in the flow's order,
one labelled arrow per message read top to bottom, a step inside one participant as a note on its lifeline."""
from __future__ import annotations

from kit import Fig
from outline import text

class Seq:
    """Lifeline heads, (title, role) left to right, each as wide as its title and 32 to 240 apart, from `left`; then
    found(), msg(), note() and an alt frame, one row at a time, and end() for the lifelines and the foot."""
    def __init__(self, title: str, desc: str, mode: str, heads: list[tuple[str, str]], left: int = 40):
        self.f = f = Fig(title, desc, mode)
        widths = [-(-(text('inter-semibold', t, 18, 0, 0)[1] + 32) // 8) * 8 for t, _ in heads]
        gap = min(240, (920 - left - sum(widths)) // max(1, len(heads) - 1) // 8 * 8)
        x, self.mid = left, {}
        for (t, role), w in zip(heads, widths):
            f.node(x, 40, w, role, t)
            self.mid[t] = x + w / 2
            x += w + gap
        self.heads, self.under, self.y, self.frame, self.closed = len(f.o), [], 160, None, False

    def back(self, x: float, y: float, words: str) -> None:
        """A canvas-coloured backing under a label left-aligned at x on baseline y, so no lifeline runs through it."""
        w = text('inter-regular', words, 16, 0, 0)[1]
        self.under.append(f'<rect x="{x - 4:.1f}" y="{y - 18}" width="{w + 8:.1f}" height="24" fill="{self.f.canvas}"/>')

    def msg(self, a: str, b: str, words: str) -> None:
        """One message from lifeline a to lifeline b, labelled 10 above, centred on the run."""
        xa, xb = self.mid[a], self.mid[b]
        self.f.arrow([(xa + (4 if xb > xa else -4), self.y), (xb + (-4 if xb > xa else 4), self.y)])
        w = text('inter-regular', words, 16, 0, 0)[1]
        self.back((xa + xb) / 2 - w / 2, self.y - 10, words)
        self.f.hlabel(min(xa, xb), max(xa, xb), self.y, words)
        self.y += 48

    def found(self, b: str, words: str) -> None:
        """A found message: from a filled dot at the diagram's left edge to lifeline b."""
        xb = self.mid[b]
        self.f.o.append(f'<circle cx="44" cy="{self.y}" r="4" fill="{self.f.conn}"/>')
        self.f.arrow([(48, self.y), (xb - 4, self.y)])
        self.f.hlabel(48, xb, self.y, words)
        self.y += 48

    def alt(self, guard: str) -> None:
        """Opens the alt frame, or divides it with a dotted line, and writes the operand's guard."""
        if self.frame is None:
            self.left = next(iter(self.mid.values())) - 48
            self.frame = (self.y - 16, [])
            self.f.t('inter-semibold', 'alt', 16, self.left + 12, self.y + 4, self.f.sub)
            self.y += 28
        else:
            self.frame[1].append(self.y - 16)
            self.y += 8
        w = text('inter-semibold', guard, 16, 0, 0)[1]
        self.under.append(f'<rect x="{self.left + 8}" y="{self.y - 14}" width="{w + 8:.1f}" height="24" fill="{self.f.canvas}"/>')
        self.f.t('inter-semibold', guard, 16, self.left + 12, self.y + 4, self.f.sub)
        self.y += 48

    def end_alt(self) -> None:
        top, dividers = self.frame
        self.closed = True
        bottom = self.y - 24
        left, right = self.left, 920
        tab = f'M {left} {top + 28} H {left + 44} L {left + 52} {top + 20} V {top}'
        self.under[:0] = [f'<rect x="{left}" y="{top}" width="{right - left}" height="{bottom - top}" fill="none" stroke="{self.f.conn}" stroke-width="1"/>',
                          f'<path d="{tab}" fill="none" stroke="{self.f.conn}" stroke-width="1"/>']
        self.under[2:2] = [f'<line x1="{left}" y1="{d}" x2="{right}" y2="{d}" stroke="{self.f.conn}" stroke-width="1" stroke-dasharray="2 4"/>' for d in dividers]
        self.y += 16

    def note(self, on: str, words: str) -> None:
        """A UML note, its corner folded, on lifeline `on`, kept inside the margins."""
        w = text('inter-regular', words, 16, 0, 0)[1] + 32
        lo = self.left + 16 if self.frame is not None and self.closed is False else 40  # inside an open alt frame
        x0 = max(lo, min(self.mid[on] - w / 2, 920 - w))
        y = self.y - 24
        self.under.append(f'<path d="M {x0:.1f} {y} H {x0 + w - 12:.1f} L {x0 + w:.1f} {y + 12} V {y + 40} H {x0:.1f} Z" fill="{self.f.canvas}" stroke="{self.f.conn}" stroke-width="1"/>')
        self.f.t('inter-regular', words, 16, x0 + 16, y + 26, self.f.sub)
        self.y += 56

    def end(self, items: tuple[str, ...], captions: tuple[str, ...]) -> str:
        bottom = self.y - 24
        lines = [f'<line x1="{m}" y1="112" x2="{m}" y2="{bottom}" stroke="{self.f.frame_stroke}" stroke-width="1"/>' for m in self.mid.values()]
        self.f.o[self.heads:self.heads] = lines + self.under
        self.f.foot(bottom, items, ('Read top to bottom: each arrow is one message.',) + captions)
        return self.f.svg()
