"""The README figure, Chains of Messages: one Agent's action publishes a message that another Agent handles, each
link its own handling, each handling performing one action. Run: DARKWAVE_BRAND_DIR=<brand dir> python3 chains.py <out dir>"""
from __future__ import annotations

import sys
from pathlib import Path
from seq import Seq

def build(mode: str) -> str:
    s = Seq('Chains of Messages: Each Link Its Own Handling',
            "A UML sequence diagram, read top to bottom, with six lifelines: the bus, Agent A, the Gate, Agent B, the agent MCP gateway and an outside system. The bus delivers a message to Agent A, which asks the Gate to decide; the Gate allows its action, and Agent A performs it: it publishes a message on the bus. The bus delivers that message to Agent B, which, a note says, acts for the same Principal. Agent B asks the Gate to decide on its own action, the Gate allows it, and Agent B performs its action through the agent MCP gateway, which calls the outside system, at most once. A note says each link is its own handling: checked, gated and recorded. Each Agent's handling performs one action, no Agent waits on another, and each Agent's lifeline is its agent runtime.", mode,
            [('Bus', 'install'), ('Agent A', 'product'), ('Gate', 'product'), ('Agent B', 'product'), ('Agent MCP Gateway', 'product'), ('Outside System', 'outside')])
    s.msg('Bus', 'Agent A', 'a message')
    s.msg('Agent A', 'Gate', 'decide')
    s.msg('Gate', 'Agent A', 'allow')
    s.msg('Agent A', 'Bus', 'publishes a message')
    s.msg('Bus', 'Agent B', 'delivers it')
    s.note('Agent B', 'acts for the same Principal')
    s.msg('Agent B', 'Gate', 'decide')
    s.msg('Gate', 'Agent B', 'allow')
    s.msg('Agent B', 'Agent MCP Gateway', 'performs its action')
    s.msg('Agent MCP Gateway', 'Outside System', 'calls it, at most once')
    s.note('Gate', 'each link is its own handling: checked, gated and recorded')
    return s.end(('product', 'install', 'outside'),
                 ("Each Agent's handling performs one action: Agent A's publishes a message, Agent B's calls an outside system.",
                  "No Agent waits on another; each Agent's lifeline is its agent runtime."))

if __name__ == '__main__':
    for mode in ('light', 'dark'):
        (Path(sys.argv[1]) / f'agent-mesh-chains-{mode}.svg').write_text(build(mode))
