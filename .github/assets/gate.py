"""The README figure, The Gate: a bookkeeping example, drawn to the Darkwave Schematic rules.

Run: DARKWAVE_BRAND_DIR=<brand dir> python3 gate.py <out dir>"""
import sys
from kit import Fig

W, H = 960, 592
COLS = (64, 352, 640)
NW = 256
# (rule node, its subtitle, outcome node, its subtitle), one per column
RULES = [('Record a bill', 'Allow rule', 'Performed at most once', 'Through its gateway'),
         ('Pay a bill', 'Hold rule', 'Approval queued', 'For the Operator'),
         ('Delete a bill', 'No rule matches it', 'Refused', 'And recorded')]

def build(mode):
    f = Fig(W, H, "The Gate: the Book-Keeper's rules decide each proposed action",
            "A supplier invoice arrives; the Book-Keeper's proposer, a model, proposes one action; the Gate matches it against the Book-Keeper's rules. Three possible proposals are shown. Record a bill: an allow rule, so it is performed at most once. Pay a bill: a hold rule, so an approval is queued for the Operator. Delete a bill: no rule matches it, so it is refused and recorded. Arrows show who calls whom.", mode)
    cx = COLS[1] + NW / 2
    f.node(COLS[1], 40, NW, 64, 'outside', 'Supplier invoice arrives', 'A message to the Book-Keeper')
    f.arrow([(cx, 104), (cx, 152)])
    f.node(COLS[1], 152, NW, 64, 'product', 'Proposer: a model', 'Proposes one action')
    f.arrow([(cx, 216), (cx, 264)])
    f.t('inter-regular', 'Three possible proposals', 12, cx + 12, 244, f.sub)
    f.zone(40, 264, 880, 136, "Gate: the Book-Keeper's rules")
    for x, (rule, rsub, out, osub) in zip(COLS, RULES):
        f.node(x, 312, NW, 64, 'product', rule, rsub)
        f.arrow([(x + NW / 2, 376), (x + NW / 2, 448)])
        f.node(x, 448, NW, 64, 'product', out, osub)
    f.legend(40, 552)
    return f.svg()

if __name__ == '__main__':
    for mode in ('light', 'dark'):
        open(f'{sys.argv[1]}/agent-mesh-gate-{mode}.svg', 'w').write(build(mode))
