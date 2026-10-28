"""The README figure, How it works: one install's Agents on the bus, and how work comes in and actions go out.
It flows as a Western reader reads, top down and left to right: the people top left, calling the control API at the
top of the cluster below them; the bus down the cluster's left; the Agents' Pods below, each calling right to its
outside system; the planned servers and the inbound path from Jira lower down; the config repository at the bottom.
Drawn to the Darkwave Schematic rules.

Run: DARKWAVE_BRAND_DIR=<brand dir> python3 mesh.py <out dir>"""
from __future__ import annotations

import sys
from pathlib import Path
from kit import Fig

L, LW = 40, 224  # the people, top left, above the cluster
LM = L + LW / 2
PL, OL = 288, 352  # the Portal's and the Operator's runs down into the control API's Service
K, CR = 40, 696  # the cluster's sides
R, RW = 744, 176  # the outside systems, right of the cluster
CT = 368  # the cluster's top, 48 below the people
CP = CT + 56  # the control plane's row
SVC, SW, API, AW = K + 24, 296, K + 344, 232
UP = K + 32  # the publisher's call back up to the Service, left of the bus
BX = K + 56  # the bus, down the cluster's left side
BUS = CP + 104  # where it turns down from the control API
X, XW = BX + 32, 464  # the Pods and everything else that joins the bus
P1, P2 = BUS + 32, BUS + 344  # the Pods' tops, 32 apart; each is 280 high
SRV = P2 + 312  # the planned servers
ING = SRV + 104
PUB = ING + 104
CB = PUB + 96  # the cluster's bottom
CFG = CB + 48

def build(mode: str) -> str:
    f = Fig('The Agent Mesh on Kubernetes: How Work Comes In and Actions Go Out',
            "Read top down and left to right. Top left, outside a Kubernetes cluster, the Operator, at the command line; under the Operator, planned for v1.x, the Portal, the Operator's surface in a browser, and the Approver, another person, who uses it; both reach the Portal in a browser. The Operator calls the control API's Service, control-api, over REST, and the Portal will too; the Portal's own Deployment, portal, is not drawn. At the top of the cluster, the Service passes the call to the control API, the Deployment control-api. The bus, the Service nats, runs from the control API down the cluster's left side. Below, two example Agents, the Book-Keeper and the Developer, each a Pod kept by its Deployment, agent-book-keeper and agent-developer, with two containers: agent-runtime, from darkwave/agent-runtime, which joins the bus and calls, over a Unix socket, its sidecar agent-mcp-gateway, from darkwave/agent-mcp-gateway, which alone holds the credentials of the install's MCP connections. Each gateway calls right, out of the cluster, over MCP and HTTPS: the Book-Keeper's to Xero, accounting, the Developer's to Jira, a tracker. Below the Agents, planned for v1.x: the MCP server, mcp-server, which joins the bus, and the doc server, doc-server; and the webhook ingress, ingress, which joins the bus and will take Jira's webhooks. Lower right, a publisher, a script, reads Jira's changes and sends them to the control API's Service as ticket.* messages. At the bottom, the config repository, a GitOps repository, is applied to the cluster on merge.", mode)
    f.node(L, 40, LW, 'outside', 'Operator', 'Command line')
    f.node(L, 144, LW, 'product', 'Portal', 'Planned, browser', planned=True)
    f.node(L, 248, LW, 'outside', 'Approver', 'Planned, another person', planned=True)
    f.arrow([(LM, 112), (LM, 144)], planned=True)
    f.vlabel(LM, 112, 144, 'browser')
    f.arrow([(LM, 248), (LM, 216)], planned=True)
    f.vlabel(LM, 216, 248, 'browser')
    f.arrow([(L + LW, 76), (OL, 76), (OL, CP)])
    f.vlabel(OL, 76, CT, 'REST')
    f.arrow([(L + LW, 180), (PL, 180), (PL, CP)], planned=True)
    f.vlabel(PL, 180, CT, 'REST')
    f.container(K, CT, CR - K, CB - CT, 'Kubernetes Cluster')
    f.node(SVC, CP, SW, 'product', 'Service', 'control-api', icon='svc', code=True)
    f.node(API, CP, AW, 'product', 'Control API', 'control-api', icon='deploy', code=True)
    f.arrow([(SVC + SW, CP + 36), (API, CP + 36)])
    st, _ = f.role['install']
    f.o.append(f'<path d="M {API + AW / 2} {CP + 72} V {BUS} H {BX} V {ING + 36}" fill="none" stroke="{st}" stroke-width="2"/>')
    f.label('Service', BX + 16, BUS - 10, icon='svc', code='nats')
    for y, name, system, kind in ((P1, 'Book-Keeper', 'Xero', 'Accounting'), (P2, 'Developer', 'Jira', 'Tracker')):
        deployment = 'agent-' + name.lower()
        f.pod(X, y, XW, name, deployment)
        f.link(BX + 4, y + 116, X + 24, y + 116)
        f.join(BX, y + 116, 'install')
        f.node(R, y + 184, RW, 'outside', system, kind)
        f.arrow([(X + XW - 24, y + 220), (R, y + 220)])
        f.hlabel(X + XW - 24, CR, y + 220, 'MCP, HTTPS')  # centred on the run inside the cluster
    f.node(X, SRV, 220, 'product', 'MCP Server', 'mcp-server', icon='deploy', code=True, planned=True)
    f.node(X + 244, SRV, 220, 'product', 'Doc Server', 'doc-server', icon='deploy', code=True, planned=True)
    f.link(BX + 4, SRV + 36, X, SRV + 36, planned=True); f.join(BX, SRV + 36, 'install')
    f.node(X, ING, XW, 'product', 'Webhook Ingress', 'ingress', icon='deploy', code=True, planned=True)
    f.link(BX + 4, ING + 36, X, ING + 36, planned=True); f.join(BX, ING + 36, 'install')
    f.node(R, PUB, RW, 'install', 'Publisher', 'A script')
    f.arrow([(R + 24, P2 + 256), (R + 24, ING + 36), (X + XW, ING + 36)], planned=True)
    f.hlabel(X + XW, CR, ING + 36, 'webhooks')
    f.arrow([(R + 56, PUB), (R + 56, P2 + 256)])  # the publisher reads Jira: up, as the call goes
    f.vlabel(R + 56, P2 + 256, PUB, 'reads changes')
    f.arrow([(R, PUB + 36), (UP, PUB + 36), (UP, CP + 72)])  # and calls back up to the Service
    f.hlabel(UP, CR, PUB + 36, 'ticket.* messages')
    f.node(K + (CR - K) / 2 - 128, CFG, 256, 'install', 'Config Repository', 'GitOps repository')
    f.arrow([(K + (CR - K) / 2, CFG), (K + (CR - K) / 2, CB)])
    f.vlabel(K + (CR - K) / 2, CB, CFG, 'applied on merge')
    f.foot(CFG + 72, ('product', 'install', 'outside', 'planned'),
           ('Plain lines join the bus; arrows show who calls whom.',
            "The agent MCP gateway runs as a sidecar container beside the agent runtime, and only it holds the credentials of the install's MCP connections.",
            'The dashed boundary is the cluster; a dashed box or arrow is planned for v1.x.'), credit=True)
    return f.svg()

if __name__ == '__main__':
    for mode in ('light', 'dark'):
        (Path(sys.argv[1]) / f'agent-mesh-figure-{mode}.svg').write_text(build(mode))
