"""The README figure, How it works: Agent pods on the NATS bus, drawn to the Darkwave Schematic rules.

Run: DARKWAVE_BRAND_DIR=<brand dir> python3 mesh.py <out dir>"""
import sys
from kit import Fig

W, H = 960, 744
COLS = (64, 352, 640)
# (name, subtitle, column, row): three pods above the bus, two below it beside the control plane
AGENTS = [('Trading Assistant', 'Read-only, informs the Operator', 0, 0),
          ('Research Assistant', None, 1, 0),
          ('Risk Monitor', None, 2, 0),
          ('Book-Keeper', None, 0, 1),
          ('Software Engineer', None, 2, 1)]

def build(mode):
    f = Fig(W, H, 'The Agent Mesh: Agent pods on the NATS bus',
            'Five example Agents, Trading Assistant (read-only: it informs the Operator), Research Assistant, Risk Monitor, Book-Keeper and Software Engineer, each run by its own agent runtime in its own pod, joined to one NATS JetStream bus inside a Kubernetes cluster. The agent runtime checks each message, applies the Gate, keeps the Agent to its budget and writes the record. The control plane joins the same bus; the Operator calls the control API from outside, through the command line. Plain lines join the bus; arrows show who calls whom.', mode)
    f.container(40, 40, 880, 488, 'Kubernetes Cluster')
    fw = 256
    bus_y = 240
    f.bus(64, 896, bus_y, 'install', 'NATS JetStream', ('every message,', 'until acknowledged'))
    for name, sub, col, row in AGENTS:
        x = COLS[col]; cx = x + fw / 2
        fy = 88 if row == 0 else 336
        f.frame(x, fy, fw, 104, 'Pod')
        f.node(x + 8, fy + 32, fw - 16, 64, 'product', name, sub)
        if row == 0:
            f.link(cx, fy + 96, cx, bus_y - 4)
        else:
            f.link(cx, bus_y + 4, cx, fy + 32)
        f.join(cx, bus_y, 'install')
    cpx, cpw = COLS[1] + 8, fw - 16
    f.node(cpx, 368, cpw, 64, 'product', 'Control Plane', 'Control API and timer')
    f.link(cpx + cpw / 2, 368, cpx + cpw / 2, bus_y + 4); f.join(cpx + cpw / 2, bus_y, 'install')
    for i, line in enumerate(['Each Agent is run by its own agent runtime, in its own pod.', 'The agent runtime checks each message, applies the Gate,', 'keeps the Agent to its budget and writes the record.']):
        f.t('inter-regular', line, 12, 64, 472 + i * 16, f.sub)
    f.node(cpx, 592, cpw, 64, 'outside', 'Operator', 'Through the command line')
    f.arrow([(cpx + cpw / 2, 592), (cpx + cpw / 2, 432)])
    f.legend(40, 704, 'Plain lines join the bus; arrows show who calls whom.', bus=True)
    return f.svg()

if __name__ == '__main__':
    for mode in ('light', 'dark'):
        open(f'{sys.argv[1]}/agent-mesh-figure-{mode}.svg', 'w').write(build(mode))
