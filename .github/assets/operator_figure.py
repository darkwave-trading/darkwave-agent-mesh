"""The README figure, The Operator: a held action waits in the exceptions queue until the Operator answers.
Run: DARKWAVE_BRAND_DIR=<brand dir> python3 operator_figure.py <out dir>"""
from __future__ import annotations

import sys
from pathlib import Path
from seq import Seq

def build(mode: str) -> str:
    s = Seq('The Operator: A Held Action and Its Answer',
            "A UML sequence diagram, read top to bottom, with five lifelines: the agent runtime, the Gate, the exceptions queue, the control API and the Operator. The agent runtime asks the Gate to decide, and the Gate holds the action; the agent runtime puts an approval in the exceptions queue, and the handling waits. The Operator approves from the command line through the control API, which records the answer in the exceptions queue. The answer reaches the agent runtime, which asks the Gate to decide again; the Gate allows the action, and the handling resumes. A note says that, unanswered, the approval expires as refused.", mode,
            [('Agent Runtime', 'product'), ('Gate', 'product'), ('Exceptions Queue', 'product'), ('Control API', 'product'), ('Operator', 'outside')])
    s.msg('Agent Runtime', 'Gate', 'decide')
    s.msg('Gate', 'Agent Runtime', 'hold')
    s.msg('Agent Runtime', 'Exceptions Queue', 'approval')
    s.note('Exceptions Queue', 'unanswered, it expires as refused')
    s.msg('Operator', 'Control API', 'approve')
    s.msg('Control API', 'Exceptions Queue', 'the answer, recorded')
    s.msg('Exceptions Queue', 'Agent Runtime', 'approved')
    s.msg('Agent Runtime', 'Gate', 'decide again')
    s.msg('Gate', 'Agent Runtime', 'allow')
    return s.end(('product', 'outside'), ('The Operator answers from the command line; the handling resumes from the record.',))

if __name__ == '__main__':
    for mode in ('light', 'dark'):
        (Path(sys.argv[1]) / f'agent-mesh-operator-{mode}.svg').write_text(build(mode))
