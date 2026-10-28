"""The README figure, Extending It: the core and its ports, the adapters that implement them, and the four ways an
install extends the Agent Mesh. It reads left to right, from the core to its ports to their adapters, with the
Markdown an install supplies above and below, and the MCP servers the gateway reaches at the bottom right.
Drawn to the Darkwave Schematic rules.

Run: DARKWAVE_BRAND_DIR=<brand dir> python3 extending.py <out dir>"""
from __future__ import annotations

import sys
from pathlib import Path
from kit import Fig

CX, CW = 40, 232  # the core
PX, PW = 312, 288  # the ports
AX, AW = 640, 280  # the adapters
TOP = 152  # the core's top, 40 below the definition file
ROW = 200  # the first port's top; each row is 88 down
PORTS = (('Proposer', None, 'Model Provider', 'or a script, or a person'),
         ('Bus', None, 'NATS JetStream', None),
         ('Record', 'RecordWriter, RecordReader', 'NATS JetStream', None),
         ('Gate', None, 'Rule Rows', None),
         ('TelemetryWriter', None, 'Prometheus', None),
         ('SecretReader', None, 'Kubernetes Secrets', None),
         ('ActionGateway', None, 'Agent MCP Gateway', 'sidecar container'))
GW = ROW + 88 * (len(PORTS) - 1)  # the gateway's row
SRV = GW + 152  # the MCP servers and the connection

def build(mode: str) -> str:
    f = Fig('Extending the Agent Mesh: Ports and Adapters',
            "Read left to right. On the left, the core: the domain and the message path, plain Rust, which depends only on its ports. In the middle, seven of its ports, the Rust traits it defines: Proposer, Bus, Record (RecordWriter and RecordReader), Gate, TelemetryWriter, SecretReader and ActionGateway; the core calls each. On the right, the adapter that implements each port and ships with the Agent Mesh: a model provider, which may instead be a script or a person; NATS JetStream for the bus and for the record; rule rows for the Gate; Prometheus for telemetry; Kubernetes Secrets for secrets; and the agent MCP gateway, a sidecar container, for actions. Above the core, an Agent definition, a Markdown file the install supplies, is loaded on reload. Below the ports, an MCP connection, a Markdown file the install supplies, is read by the gateway. Below the gateway, the two kinds of MCP server it calls over MCP: a vendor's, outside the mesh, and the install's own. The captions say that each adapter implements one port and passes the conformance kit; that an Agent and a connection are Markdown files read at a reload; that swapping a part is a Rust crate of the install's own built into a release; and that an MCP server of the install's own, in any language, is reached like a vendor's.", mode)
    f.node(CX, 40, CW, 'install', 'Agent Definition', 'Markdown file')
    f.arrow([(CX + CW / 2, 112), (CX + CW / 2, TOP)])
    f.vlabel(CX + CW / 2, 112, TOP, 'loaded on reload')
    f.zone(CX, TOP, CW, GW + 72 + 24 - TOP, 'The Core')
    f.node(CX + 16, ROW, CW - 32, 'product', 'Domain', 'agent-domain', code=True)
    f.node(CX + 16, ROW + 88, CW - 32, 'product', 'Message Path', 'use cases')
    f.label('Ports: Rust traits', PX, ROW - 16)
    f.label('Adapters: Rust crates', AX, ROW - 16)
    for i, (port, sub, adapter, asub) in enumerate(PORTS):
        y = ROW + 88 * i
        f.node(PX, y, PW, 'product', port, sub, code=sub is not None)
        f.node(AX, y, AW, 'product', adapter, asub)
        f.arrow([(CX + CW, y + 36), (PX, y + 36)])  # the core calls the port
        f.arrow([(AX, y + 36), (PX + PW, y + 36)])  # the adapter implements it
    f.node(PX, SRV, PW, 'install', 'MCP Connection', 'Markdown file')
    f.arrow([(PX + PW / 2, SRV), (PX + PW / 2, SRV - 40), (AX - 20, SRV - 40), (AX - 20, GW + 56), (AX, GW + 56)])
    f.hlabel(PX + PW / 2, AX - 20, SRV - 40, 'read by the gateway')
    for x, role, title in ((AX, 'outside', "Vendor's"), (AX + 144, 'install', 'Your Own')):
        f.node(x, SRV, 136, role, title, 'MCP server')
        f.arrow([(x + 68, GW + 72), (x + 68, SRV)])
    f.vlabel(AX + 68, GW + 72, SRV, 'MCP')
    f.foot(SRV + 72, ('product', 'install', 'outside'),
           ('The core depends only on its ports; each adapter implements one, and passes the conformance kit before it is trusted.',
            'Add an Agent and Connect a system are Markdown files, read at a reload; Swap a part is a Rust crate of your own in place of an adapter, built into a release.',
            "Build an MCP server is a server of your own, in any language, which the gateway reaches like a vendor's."))
    return f.svg()

if __name__ == '__main__':
    for mode in ('light', 'dark'):
        (Path(sys.argv[1]) / f'agent-mesh-extending-{mode}.svg').write_text(build(mode))
