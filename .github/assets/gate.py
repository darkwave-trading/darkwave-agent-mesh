"""The README figure, The Gate: how the Gate decides one proposed action, as a UML sequence diagram read top to
bottom, with the Gate's three outcomes as the operands of one alt frame. Run: DARKWAVE_BRAND_DIR=<brand dir> python3 gate.py <out dir>"""
from __future__ import annotations

import sys
from pathlib import Path
from seq import Seq

def build(mode: str) -> str:
    s = Seq('The Gate: How It Decides One Action',
            "A UML sequence diagram, read top to bottom, of the Book-Keeper handling a supplier invoice, with five lifelines: the agent runtime, the proposer, the Gate, the agent MCP gateway and Xero. A supplier invoice arrives at the agent runtime, which asks the proposer to propose one action; the proposer returns an action. The agent runtime asks the Gate to decide, and the Gate returns allow, hold or refuse. Then one of three alternatives. Allow, to record a bill: the agent runtime asks the agent MCP gateway to create the bill, at most once, and the gateway creates it in Xero. Hold, to pay a bill: a note says an approval waits for the Operator. Refuse, to delete a bill, which no rule matches: a note says it is refused and recorded. Every step is recorded before the next.", mode,
            [('Agent Runtime', 'product'), ('Proposer', 'outside'), ('Gate', 'product'), ('Agent MCP Gateway', 'product'), ('Xero', 'outside')], left=120)
    s.found('Agent Runtime', 'a supplier invoice')
    s.msg('Agent Runtime', 'Proposer', 'propose one action')
    s.msg('Proposer', 'Agent Runtime', 'an action')
    s.msg('Agent Runtime', 'Gate', 'decide')
    s.msg('Gate', 'Agent Runtime', 'allow, hold or refuse')
    s.alt('[allow] record a bill')
    s.msg('Agent Runtime', 'Agent MCP Gateway', 'create the bill, at most once')
    s.msg('Agent MCP Gateway', 'Xero', 'create the bill')
    s.alt('[hold] pay a bill')
    s.note('Agent Runtime', 'an approval waits for the Operator')
    s.alt('[refuse] delete a bill, no rule matches')
    s.note('Agent Runtime', 'refused and recorded')
    s.end_alt()
    return s.end(('product', 'outside'), ('One branch of the frame happens; dotted lines divide them.', 'Every step is recorded before the next.'))

if __name__ == '__main__':
    for mode in ('light', 'dark'):
        (Path(sys.argv[1]) / f'agent-mesh-gate-{mode}.svg').write_text(build(mode))
