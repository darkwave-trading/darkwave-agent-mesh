"""The README schematic: one install of the Agent Mesh, drawn to the Darkwave Schematic rules.

Run: DARKWAVE_BRAND_DIR=<brand dir> python3 schematic.py <out dir>"""
import sys
from kit import Fig

W, H = 960, 576

def build(mode):
    f = Fig(W, H, 'The Darkwave Agent Mesh: one install on a Kubernetes cluster',
            'Outside a Kubernetes cluster: the Operator, who calls the control API through the command line, and the cloud AI models and external systems, reached through ports and adapters. Inside: the control plane and the Agent pods, one per Agent, which the Agent Mesh provides; a model server, NATS JetStream (the bus stream, and the record and exceptions buckets) and the definitions, which the install supplies. The control plane and the Agent pods use NATS and read the definitions. Arrows show who calls whom.', mode)
    C1, C2, C3 = (64, 256), (344, 272), (640, 256)
    mid = lambda c: c[0] + c[1] / 2
    f.node(C1[0], 40, C1[1], 64, 'outside', 'Operator', 'Through the command line')
    f.node(C2[0], 40, C2[1], 64, 'outside', 'Cloud AI Models', 'e.g. Claude, Gemini')
    f.node(C3[0], 40, C3[1], 64, 'outside', 'External Systems', 'e.g. GitHub, Jira, Slack, Binance')
    f.container(40, 144, 880, 368, 'Kubernetes Cluster')
    f.node(C1[0], 200, C1[1], 80, 'product', 'Control Plane', 'Control API and timer')
    f.node(C2[0], 200, C2[1] - 8, 80, 'product', 'Agent Pods', 'One per Agent', stack=True)
    f.node(C3[0], 200, C3[1], 80, 'install', 'Model Server', 'On-premise, e.g. Gemma, DeepSeek')
    f.zone(64, 320, 552, 152, 'NATS JetStream')
    f.node(88, 368, 252, 80, 'install', 'Bus Stream', 'Every message, until acknowledged')
    f.node(356, 368, 236, 80, 'install', 'Record Buckets', 'Every step, and the exceptions')
    f.node(C3[0], 368, C3[1], 80, 'install', 'Definitions', 'Agents, rules and budgets')
    f.arrow([(mid(C1), 104), (mid(C1), 200)])
    f.arrow([(472, 192), (472, 104)])
    f.arrow([(576, 192), (576, 128), (mid(C3), 128), (mid(C3), 104)])
    f.t('inter-regular', 'Reached through ports and adapters', 12, 756, 122, f.sub, 'end')
    f.arrow([(616, 240), (640, 240)])
    f.arrow([(600, 280), (600, 304), (mid(C3), 304), (mid(C3), 368)])
    f.arrow([(mid(C1), 280), (mid(C1), 320)])
    f.arrow([(472, 280), (472, 320)])
    f.arrow([(64, 240), (52, 240), (52, 496), (mid(C3), 496), (mid(C3), 448)])
    f.legend(40, 548, stack=True)
    return f.svg()

if __name__ == '__main__':
    for mode in ('light', 'dark'):
        open(f'{sys.argv[1]}/agent-mesh-schematic-{mode}.svg', 'w').write(build(mode))
