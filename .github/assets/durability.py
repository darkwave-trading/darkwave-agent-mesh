"""The README figure, Durability: a handling survives its pod's crash, read back from the record.
Run: DARKWAVE_BRAND_DIR=<brand dir> python3 durability.py <out dir>"""
from __future__ import annotations

import sys
from pathlib import Path
from seq import Seq

def build(mode: str) -> str:
    s = Seq('Durability: A Handling Survives a Crash of Its Pod',
            "A UML sequence diagram, read top to bottom, with two lifelines: the agent runtime and the record. The agent runtime writes each entry before the next step: received, attempt 1, then checked, the estimate and the proposal, then the Gate's decision. The pod crashes. On restart, the agent runtime reads the record back, the record returns the entries written so far, and the runtime counts a new attempt, attempt 2, and carries on from the first entry not written, the intent. A note says an intent with no outcome is never performed again, and the Operator is asked.", mode,
            [('Agent Runtime', 'product'), ('Record', 'install')])
    s.msg('Agent Runtime', 'Record', 'received')
    s.msg('Agent Runtime', 'Record', 'attempt 1')
    s.msg('Agent Runtime', 'Record', 'checked, estimate, proposal')
    s.msg('Agent Runtime', 'Record', 'decision: allow')
    s.note('Agent Runtime', 'the pod crashes, and restarts')
    s.msg('Agent Runtime', 'Record', 'read back')
    s.msg('Record', 'Agent Runtime', 'the entries so far')
    s.msg('Agent Runtime', 'Record', 'attempt 2')
    s.msg('Agent Runtime', 'Record', 'intent')
    s.note('Record', 'an intent with no outcome is never performed again; the Operator is asked')
    return s.end(('product', 'install'), ('Each entry is written before the next step, once, and never changed.',))

if __name__ == '__main__':
    for mode in ('light', 'dark'):
        (Path(sys.argv[1]) / f'agent-mesh-durability-{mode}.svg').write_text(build(mode))
