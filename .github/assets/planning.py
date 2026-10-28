"""The README figure, Planning and Dispatch Through a Tracker: a ticket assigned in Jira reaches an Agent as a
message, and the Operator's answer comes back the same way. Run: DARKWAVE_BRAND_DIR=<brand dir> python3 planning.py <out dir>"""
from __future__ import annotations

import sys
from pathlib import Path
from seq import Seq

def build(mode: str) -> str:
    s = Seq('Planning and Dispatch Through a Tracker',
            "A UML sequence diagram, read top to bottom, with six lifelines: the Planner, the agent MCP gateway, Jira, the publisher, the Developer and the Operator. The Planner assigns a ticket in Jira, through the agent MCP gateway. The publisher reads the change and publishes it, through the control API, as a ticket.* message, which reaches the Developer. The Developer works the ticket and passes it to the Operator in Jira, through the agent MCP gateway, and the Operator answers there. The publisher reads that change and brings the answer back to the Developer as a new message. Each Agent calls its own gateway, and the publisher sends each message through the control API. A note says the tracker's wait is in its own history, and nothing enters the exceptions queue.", mode,
            [('Planner', 'product'), ('Agent MCP Gateway', 'product'), ('Jira', 'outside'), ('Publisher', 'install'), ('Developer', 'product'), ('Operator', 'outside')])
    s.msg('Planner', 'Agent MCP Gateway', 'assigns a ticket')
    s.msg('Agent MCP Gateway', 'Jira', 'assigns it')
    s.msg('Publisher', 'Jira', 'reads changes')
    s.msg('Publisher', 'Developer', 'ticket.* message')
    s.msg('Developer', 'Agent MCP Gateway', 'passes it to the Operator')
    s.msg('Agent MCP Gateway', 'Jira', 'passes it')
    s.note('Jira', "the tracker's wait is in its own history; nothing enters the exceptions queue")
    s.msg('Operator', 'Jira', 'answers')
    s.msg('Publisher', 'Jira', 'reads changes')
    s.msg('Publisher', 'Developer', 'a new message')
    return s.end(('product', 'install', 'outside'), ('Planner and Developer are Agents; the publisher is a script.', 'Each Agent calls its own gateway; the publisher sends each message through the control API.'))

if __name__ == '__main__':
    for mode in ('light', 'dark'):
        (Path(sys.argv[1]) / f'agent-mesh-planning-{mode}.svg').write_text(build(mode))
