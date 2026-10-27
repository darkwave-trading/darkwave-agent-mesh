"""The README figure, The Operator: the exceptions queue, drawn to the Darkwave Schematic rules.

Run: DARKWAVE_BRAND_DIR=<brand dir> python3 exceptions_queue.py <out dir>"""
import sys
from kit import Fig

W, H = 960, 568
QX, QW = 336, 224
ROWS = (88, 184, 280)
# (kind, the Operator's answers), one per row of the queue
KINDS = [('Approval', 'Approve or refuse'),
         ('Problem', 'Acknowledge, resolve or retry'),
         ('Proposal Asked', 'Propose')]

def build(mode):
    f = Fig(W, H, 'The Operator: one exceptions queue',
            'Left, the Agent pods, whose paused handlings raise an approval, a problem or a proposal asked into one queue; middle, the queue with those three kinds; right, the Operator at the command line, who answers: approve or refuse, acknowledge, resolve or retry, or propose. Answers are written to the record, and the handling that asked resumes from it. Arrows show who calls whom.', mode)
    f.zone(312, 40, 272, 328, 'Exceptions Queue')
    for y, (kind, answers) in zip(ROWS, KINDS):
        f.node(QX, y, QW, 64, 'install', kind, answers)
    f.node(64, 184, 160, 64, 'product', 'Agent Pods', 'One per Agent', stack=True)
    f.node(736, 184, 160, 64, 'outside', 'Operator', 'At the command line')
    for y in ROWS:
        m = y + 32
        f.arrow([(224, 216), (336, 216)] if m == 216 else [(224, 216), (240, 216), (240, m), (336, m)])
        f.arrow([(736, 216), (560, 216)] if m == 216 else [(736, 216), (720, 216), (720, m), (560, m)])
    f.t('inter-regular', 'raise', 12, 248, 210, f.sub)
    f.t('inter-regular', 'answers', 12, 640, 210, f.sub, 'middle')
    f.node(QX, 416, QW, 64, 'install', 'Record', 'Answers written as entries')
    f.arrow([(448, 368), (448, 416)])
    f.t('inter-regular', 'answers are written to it', 12, 460, 396, f.sub)
    f.arrow([(144, 248), (144, 448), (336, 448)])
    f.t('inter-regular', 'the handling resumes from it', 12, 160, 442, f.sub)
    f.legend(40, 528, stack=True)
    return f.svg()

if __name__ == '__main__':
    for mode in ('light', 'dark'):
        open(f'{sys.argv[1]}/agent-mesh-operator-{mode}.svg', 'w').write(build(mode))
