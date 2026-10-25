# Darkwave Agent Runtime

![Status: in development](https://img.shields.io/badge/status-in%20development-1F6FA8)

A runtime for event-driven AI agents, for Kubernetes, in development. It is designed so that each step is checked, gated and recorded, and each action is performed at most once.

> [!NOTE]
> **Not yet released.** v1.0 is in development and will be published here once Darkwave's own Agents run on it. No date is set. Watch this repository's releases to be notified.

## What it is

The Darkwave Agent Runtime runs AI agents that handle messages and act on them. Agents and their rules are declared in Markdown. Each Agent has one proposer (a model, a script or a person), which proposes an action. The runtime checks it, gates it, records it and performs it at most once. The Operator, the person who runs an install, answers whatever only a person can, from one queue.

## Design

What v1.0 is designed to do:

- **Declared in Markdown.** Agents, rules, budgets and schedules are plain files you can read, review and version.
- **Input is checked.** Every input is checked where it enters. Input that fails is refused and recorded, never repaired.
- **Every action passes the Gate.** A rule allows it, holds it for the Operator, or refuses it.
- **At most once.** The runtime never performs an action twice on its own initiative, and a repeated message is handled once.
- **Everything is recorded.** Each step is an entry in the record, in order. Once a handling has reached its first durable entry, a crash resumes it from the record.
- **Cost before calls.** Every handling's cost is estimated and checked against its Agent's budget before a model is asked.
- **Specified before it is built.** The message path and the exceptions queue are specified in TLA+ and model-checked; the specifications are in [`specs/`](specs/). Each guarantee carries an ID that names what proves it (a TLA+ property, a conformance suite or a stated assumption) and the test of the same name.
- **No vendor in the core.** Models, transports, stores, telemetry and outside systems plug in at ports. One conformance kit holds every adapter of a port to the same contract.
- **Latency budget.** The runtime's own path has a written latency budget, and v1.0's code is benchmarked against it.

## How it works

The Operator works from the command line, through the control API. Inside the cluster, each Agent runs in its own pod, and everything outside the core plugs in at a port.

Each message an Agent handles goes through the same eight steps, each one recorded:

1. **Received** from a proved sender, once. A copy with different content is refused.
2. **Checked.** Input that fails is refused, never repaired.
3. **Estimated.** The cost is checked against the Agent's budget, or the message is refused.
4. **Proposed** by a model, a script or a person, or refused.
5. **Gated.** A rule allows the action, holds it for the Operator's answer, or refuses it.
6. **Intended.** The intent is recorded before acting.
7. **Performed** at most once. The outcome is succeeded or failed.
8. **Closed.** The closing entry is written last.

A refusal is recorded and ends the handling; some refusals also raise a problem for the Operator.

## What v1.0 holds

- The message path, specified in TLA+ and model-checked in CI
- The exceptions queue (approvals, problems and proposals, answered by the Operator), also specified in TLA+
- Agents, rules, budgets and schedules declared in Markdown, with one pod per Agent on Kubernetes
- A REST control API and a CLI, `agent-cli`, with authentication
- A model provider adapter, a script proposer, and a person as proposer
- Telemetry through a port, Prometheus by default, and secrets that never enter the core
- An adapter conformance kit and a benchmark harness

After v1.0: a web portal, a webhook ingress, an MCP server, trace validation of the code against its specification, a Helm chart and published container images.

## Who builds it

Darkwave Trading Limited, a New Zealand proprietary trading firm. The runtime is built for and used by Darkwave's own Agents.

## Contributing

Contributions open with the first release, together with a `CONTRIBUTING.md`.

## Licence

The licence will be published with the first release. Until then, all rights are reserved.

---

© 2026 Darkwave Trading Limited
