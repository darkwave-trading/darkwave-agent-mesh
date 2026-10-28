"""The README figure, Planning and Dispatch Through a Tracker: a ticket assigned in Jira reaches an Agent as a
message, and the Operator's answer comes back the same way. Run: DARKWAVE_BRAND_DIR=<brand dir> python3 planning.py <out dir>"""
from __future__ import annotations

import sys
from pathlib import Path
from seq import Seq

def build(mode: str) -> str:
    s = Seq('Planning and Dispatch Through a Tracker',
            "A UML sequence diagram, read top to bottom, with six lifelines: the Planner, the agent MCP gateway, Jira, the Jira Watcher, the Developer and the Operator. The Planner assigns a ticket in Jira, through the agent MCP gateway. The Jira Watcher reads the change through the agent MCP gateway and publishes it as a ticket.* message, which reaches the Developer. The Developer works the ticket and passes it to the Operator in Jira, through the agent MCP gateway, and the Operator answers there. The Jira Watcher reads that change the same way and brings the answer back to the Developer as a new message. The Planner, the Jira Watcher and the Developer are Agents, the Jira Watcher's proposer a script; each Agent calls its own gateway, and the Jira Watcher publishes on the bus. A note says the tracker's wait is in its own history, and nothing enters the exceptions queue.", mode,
            [('Planner', 'product'), ('Agent MCP Gateway', 'product'), ('Jira', 'outside'), ('Jira Watcher', 'product'), ('Developer', 'product'), ('Operator', 'outside')])
    s.msg('Planner', 'Agent MCP Gateway', 'assigns a ticket')
    s.msg('Agent MCP Gateway', 'Jira', 'assigns it')
    s.msg('Jira Watcher', 'Agent MCP Gateway', 'reads changes')
    s.msg('Agent MCP Gateway', 'Jira', 'reads them')
    s.msg('Jira Watcher', 'Developer', 'ticket.* message')
    s.msg('Developer', 'Agent MCP Gateway', 'passes it to the Operator')
    s.msg('Agent MCP Gateway', 'Jira', 'passes it')
    s.note('Jira', "the tracker's wait is in its own history; nothing enters the exceptions queue")
    s.msg('Operator', 'Jira', 'answers')
    s.msg('Jira Watcher', 'Agent MCP Gateway', 'reads changes')
    s.msg('Agent MCP Gateway', 'Jira', 'reads them')
    s.msg('Jira Watcher', 'Developer', 'a new message')
    return s.end(('product', 'outside'), ("Planner, Jira Watcher and Developer are Agents; the Jira Watcher's proposer is a script.", 'Each Agent calls its own gateway; the Jira Watcher publishes on the bus.'))

if __name__ == '__main__':
    for mode in ('light', 'dark'):
        (Path(sys.argv[1]) / f'agent-mesh-planning-{mode}.svg').write_text(build(mode))
