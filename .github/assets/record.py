"""The README figure, Durability: one handling's entries in the record, drawn to the Darkwave Schematic rules.

Run: DARKWAVE_BRAND_DIR=<brand dir> python3 record.py <out dir>"""
import sys
from kit import Fig

W, H = 960, 664
WRITTEN = ['received', 'attempt 1', 'checked', 'estimate', 'proposal: record a bill', 'usage', 'decision: allow']
PENDING = ['attempt 2', 'intent', 'outcome', 'closing']

def build(mode):
    f = Fig(W, H, 'The record: a handling survives a crash of its pod',
            "Left, an Agent pod running the agent runtime, which writes each entry before taking the next step, crashes just after the Gate's decision, restarts and reads the record back. Right, NATS JetStream, supplied by the install, holding the handling's entries in order: received, attempt 1, checked, estimate, proposal: record a bill, usage and decision: allow are written; attempt 2, intent, outcome and closing are not yet written. Each entry is written once and never changed.", mode)
    f.zone(40, 40, 376, 520, 'Agent pod', 'The agent runtime')
    f.node(64, 104, 328, 64, 'product', 'Writes each entry', 'Before taking the next step')
    f.node(64, 328, 328, 64, 'product', 'Pod crashes', "Just after the Gate's decision")
    f.node(64, 472, 328, 64, 'product', 'Pod restarts', 'Reads the record back')
    f.zone(512, 40, 408, 520, 'NATS JetStream', 'Supplied by the install')
    for i, name in enumerate(WRITTEN + PENDING):
        f.entry(536, 104 + i * 40, 360, 'install', name, pending=name in PENDING)
    f.arrow([(392, 136), (512, 136)])
    f.t('inter-regular', 'writes', 12, 452, 130, f.sub, 'middle')
    f.arrow([(512, 504), (392, 504)])
    f.t('inter-regular', 'reads', 12, 452, 498, f.sub, 'middle')
    f.legend(40, 600, None)
    f.t('inter-regular', 'Each entry is written once and never changed. Dashed: not yet written.', 12, W - 40, 624, f.sub, 'end')
    return f.svg()

if __name__ == '__main__':
    for mode in ('light', 'dark'):
        open(f'{sys.argv[1]}/agent-mesh-record-{mode}.svg', 'w').write(build(mode))
