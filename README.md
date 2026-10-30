<!-- markdownlint-disable MD025 -->
<!-- markdownlint-disable MD033 MD041 -->
<picture>

<source media="(prefers-color-scheme: dark)" srcset=".github/assets/agent-mesh-hero-dark.svg">

<img alt="The Darkwave Agent Mesh wordmark: the wave mark, DARKWAVE, and AGENT MESH beneath it in blue." src=".github/assets/agent-mesh-hero-light.svg">

</picture>
<!-- markdownlint-enable MD033 MD041 -->

An agent mesh for [Kubernetes](https://kubernetes.io/), on [NATS](https://nats.io/).

The Agent Mesh runs AI agents on Kubernetes. Each Agent is declared in a Markdown file: the messages it handles, the model, script or person that proposes its actions, and the actions it may take. An action not listed is refused; one marked `hold` waits for a person. Every step is recorded before the next is taken, and no action is performed twice on the Agent Mesh's own initiative.

Coming soon (2026).

<!-- markdownlint-disable MD007 -->
- [1. What It Is](#1-what-it-is)
    - [1.1 An Agent Definition (markdown only)](#11-an-agent-definition-markdown-only)
- [2. How It Works](#2-how-it-works)
- [3. Features](#3-features)
    - [3.1 Agent Runtime](#31-agent-runtime)
    - [3.2 At-Most-Once Actions](#32-at-most-once-actions)
    - [3.3 Audit and Observability](#33-audit-and-observability)
    - [3.4 Chains of Messages (not workflows)](#34-chains-of-messages-not-workflows)
    - [3.5 Command Line](#35-command-line)
    - [3.6 Control API](#36-control-api)
    - [3.7 Costs and Budgets](#37-costs-and-budgets)
    - [3.8 Definitions and Templates](#38-definitions-and-templates)
    - [3.9 Doc Server](#39-doc-server)
    - [3.10 Durability](#310-durability)
    - [3.11 Four-Eyes Approval](#311-four-eyes-approval)
    - [3.12 Action Gate](#312-action-gate)
    - [3.13 GitOps Configuration](#313-gitops-configuration)
    - [3.14 Identity and Security](#314-identity-and-security)
    - [3.15 MCP Server](#315-mcp-server)
    - [3.16 Operator](#316-operator)
    - [3.17 Outside Systems](#317-outside-systems)
    - [3.18 Planning and Dispatch Through a Tracker](#318-planning-and-dispatch-through-a-tracker)
    - [3.19 Portal](#319-portal)
    - [3.20 Proposers](#320-proposers)
    - [3.21 Schedules](#321-schedules)
    - [3.22 Supported Platforms](#322-supported-platforms)
    - [3.23 Verified by Specification](#323-verified-by-specification)
- [4. The Command Line](#4-the-command-line)
- [5. Extending It](#5-extending-it)
    - [5.1 Connector Catalogue](#51-connector-catalogue)
- [6. What v1.0 Holds](#6-what-v10-holds)
- [7. Who Builds It](#7-who-builds-it)
- [8. Built With](#8-built-with)
- [9. Contributing](#9-contributing)
- [10. Licence](#10-licence)
<!-- markdownlint-enable MD007 -->

# 1. What It Is

An **Agent** handles messages and acts on them. It is declared in Markdown, together with its rules, and listens to **subjects**, dotted names such as `invoice.received` that messages are sent to. The **Operator** is the one person who runs an install (not a Kubernetes operator).

The **agent runtime** is the process that runs an Agent in its own pod; one Agent's work on one message is a **handling** (Durability, below). It checks the message, asks the proposer for one action, passes that action through the **Gate**, records every step, and performs the action at most once on the Agent Mesh's own initiative. The Gate applies the Agent's rules to the action, for the Agent and for the Principal the message acts for (Identity and Security, below). The mesh is the Agents, the bus that joins them, the runtime, Gate and record around each, and the control plane that starts and stops them (How It Works, below); nothing else is shared.

What it is not: a store, since it holds nothing beyond the record and the exceptions queue (Operator, below); a model host, since it ships no model and reaches every model through an adapter and every outside system through a gateway; or a service mesh, whose proxies see traffic between services but cannot keep an action to at most once.

## 1.1 An Agent Definition (markdown only)

````markdown
---
kind: agent
name: book-keeper
listens-to: [invoice.received, bill.payable]
proposer: claude-sonnet-5-5
budget: { messages: 2000, cost: USD 20.00, period: month }
attempt-limit: 3
---

# Book-Keeper

Records supplier bills in Xero, and proposes paying them for the Operator to approve.

## Instructions

Propose one action for each message.

- On `invoice.received`, the message is one supplier invoice as the accounts mailbox received it. If it is a supplier's bill, propose `xero.create-invoice` as a bill (type `ACCPAY`), with the supplier as the contact, the invoice number as the reference, and its lines, tax and due date as the invoice states them.
- On `bill.payable`, the message names a bill in Xero and the bank account to pay it from. Propose `xero.create-payment` for the bill's amount due.
- Never propose a payment for an amount other than the amount due.
- If the invoice is not a bill, or any amount or account is unclear, refuse, and say why.

Example: an invoice from Example Supplies Ltd, number 1042, for NZD 230.00 including GST, due 20 November, becomes one bill with those values.

## Rules

| Tool                | Effect | Subjects         | On behalf of    |
|---------------------|--------|------------------|-----------------|
| xero.create-invoice | allow  | invoice.received | script-inbox    |
| xero.create-payment | hold   | bill.payable     | client-accounts |
````

This is the Book-Keeper, in the definition template's standard layer; the template gives every field, layer by layer, and what each check refuses. It reaches Xero through the agent MCP gateway, over Xero's hosted [MCP](https://modelcontextprotocol.io/) server. The install's `xero` connection, one Markdown file, declares the server's tools, the tools the rules can name, and the install declares two Principals: the script `inbox`, which publishes each supplier invoice from the accounts mailbox to `invoice.received`, and the client `accounts`, the program that sends a bill that may be paid to `bill.payable`. The Book-Keeper may create a bill for an invoice the inbox script published, and pay a bill the accounts client sent once the Operator approves. A payment proposed while handling an invoice is refused, since its rule names only `bill.payable`; so is anything for any other Principal, and everything else in Xero, because no rule lists it. An effect is one of three, fixed in the Agent Mesh: `allow`, `hold` or `refuse`.

---

# 2. How It Works

**The Book-Keeper, the Developer, the Planner and the Jira Watcher ship with the product as examples, and none is fixed: each organisation that adopts the Agent Mesh defines its own Agents. The Agent Mesh defines no workflow; work across Agents is only a chain of messages (Chains of Messages, below).**

The Operator works from the command line, which calls the control API from outside the cluster; the control API runs inside it, and the two are the control plane; schedules and expiries are NATS scheduled messages, so no process of the Agent Mesh keeps a clock for them. Each Agent is run by its own agent runtime, in its own pod: every Agent's pod runs the same two images, `darkwave/agent-runtime` and, beside it as a sidecar, `darkwave/agent-mcp-gateway`; only its definition, credentials, NATS identity and budget are its own. [NATS JetStream](https://docs.nats.io/concepts/jetstream) connects them; the control plane joins the same bus. The core is the message path and the Gate; everything else plugs in at a port.

<!-- markdownlint-disable MD033 -->
<picture>

<source media="(prefers-color-scheme: dark)" srcset=".github/assets/agent-mesh-figure-dark.svg">

<img alt="Read top down and left to right. Top left, outside a Kubernetes cluster, the Operator, at the command line; under the Operator, planned for v1.x, the Portal, the Operator&#x27;s surface in a browser, and the Approver, another person, who uses it; both reach the Portal in a browser. The Operator calls the control API&#x27;s Service, control-api, over REST, and the Portal will too; the Operator also works in Xero and in Jira, in a browser; the Portal&#x27;s own Deployment, portal, is not drawn. At the top of the cluster, the Service passes the call to the control API, the Deployment control-api. The bus, the Service nats, runs from the control API down the cluster&#x27;s left side. Below, two example Agents, the Book-Keeper and the Developer, each a Pod kept by its Deployment, agent-book-keeper and agent-developer, with two containers: agent-runtime, from darkwave/agent-runtime, which joins the bus and calls, over a Unix socket, its sidecar agent-mcp-gateway, from darkwave/agent-mcp-gateway, which alone holds the credentials of the install&#x27;s MCP connections. Each gateway calls right, out of the cluster, over MCP and HTTPS, to its Agent&#x27;s outside systems: the Book-Keeper&#x27;s to Xero, accounting, Gmail, mail, and Docusign, agreements; the Developer&#x27;s to GitHub, code, Slack, chat, and Jira, a tracker. Below them, a third example Agent, the Jira Watcher, an Agent with a script proposer, in a Pod of its own kept by its Deployment, agent-jira-watcher, with the same two containers; its gateway calls right, out of the cluster, over MCP and HTTPS, to Jira, to read Jira&#x27;s changes, and its agent runtime publishes them on the bus as ticket.* messages. Below the Agents, planned for v1.x: the MCP server, mcp-server, which joins the bus, and the doc server, doc-server; and the webhook ingress, ingress, which joins the bus and will take Jira&#x27;s webhooks. At the bottom, the config repository, a GitOps repository, is applied to the cluster on merge." src=".github/assets/agent-mesh-figure-light.svg" width="576">

</picture>
<!-- markdownlint-enable MD033 -->

The outside systems the Agents reach are examples too: the Book-Keeper defined above names only Xero's tools, and reaches Gmail and Docusign only once its rules name theirs. Jira's part is an example too, of a tracker; it is in Planning and Dispatch Through a Tracker, below. Every message an Agent handles takes these steps in order, as far as it gets, and each step it takes is recorded.

1. **Received.** The agent runtime takes the message from a sender whose identity has been proved, records it once, and counts the attempt against the Agent's attempt limit. The same message id from the same sender with different content is refused and recorded apart.
2. **Checked.** The agent runtime checks the message against its contract. A message that fails the check is refused, never repaired.
3. **Estimated.** The agent runtime estimates what handling the message will cost and checks the estimate against the Agent's budget. If it would take the Agent over its budget, the message is refused.
4. **Proposed.** The Agent's proposer, a model, a script or the Operator, proposes one action. If the proposer refuses instead, the message is refused.
5. **Gated.** The Gate applies the Agent's rules to the proposed action, for the Agent and for the Principal the message acts for. The most restrictive matching rule decides: allow, hold for the Operator, or refuse; if no rule matches, the action is refused. An approved hold is decided again before anything is performed.
6. **Intended.** Before acting, the agent runtime claims the intent in the record, with a lease longer than the gateway's timeout. Only the attempt that wins that claim performs; one that finds it already there never does.
7. **Performed.** The agent runtime performs the action, at most once: a message, on the bus; anything in an outside system, through its agent MCP gateway, the sidecar beside it; and records the outcome: succeeded, or failed. If the gateway gives no answer, nothing is recorded, the action is never performed again on the Agent Mesh's own initiative, and the Operator is asked what happened.
8. **Closed.** The agent runtime writes the closing entry last, and the handling is over.

A refusal at any step is recorded and ends the handling. Some refusals also raise a problem for the Operator.

---

# 3. Features

What the Agent Mesh is designed to do, in alphabetical order; features planned for v1.x are marked.

## 3.1 Agent Runtime

The agent runtime takes each message through the steps in How It Works, above, recording each before it takes the next.

It starts the Agent's handlings one at a time, in the subject's order, while other Agents run in parallel; a handling that waits on the Operator is parked and the next one starts, so actions are not always performed in that order. On start, including after a crash, and periodically, it reads the record for handlings with no closing entry and carries each one on from its last entry, before any new message, except one that waits on the Operator. A handling resumed before its outcome counts an attempt, and at the Agent's attempt limit it stops and the Operator is asked. Stopping an Agent lets an action under way finish; its messages wait until it starts again.

It is a static Rust binary. The time the agent runtime's own path may take is written down as a latency budget, and v1.0's code is benchmarked against it.

## 3.2 At-Most-Once Actions

The Agent Mesh never performs one handling's action twice on its own initiative. A message sent again under the same sender and id is handled once by each Agent that listens for it.

Every write has a key, and a repeat under the same key changes nothing: a publish by its sender and message id; a handling by the message and the Agent; each entry of a handling, written as a claim that one writer wins; the intent by its handling, performed only by the holder of its lease; an answer by its exception id; a retry by the problem it answers; a scheduled message by its schedule, version and fire time; a reload by its revision. A gateway passes the action id to the outside system as its idempotency key where the system takes one; where it does not, at most once rests on the lease and on the gateway answering nothing when unsure.

## 3.3 Audit and Observability

The record is the audit trail: every step of every handling, in order, with the Principal the work acted for, the Gate's decision and any answer from the Operator (Durability, below). `dwmesh message trace` lists one handling's entries in order. Telemetry goes through a port, [Prometheus](https://prometheus.io/) by default: each process logs one line per event to standard output and serves its metrics on its health port.

## 3.4 Chains of Messages (not workflows)

Agents talk only through messages, sent to subjects on the bus; no Agent calls another. The Agent Mesh is not a workflow engine: no flow is defined and none is driven.

Work that takes several steps is a chain of messages: an Agent's action sends a message, another Agent handles it, and the Principal the work acts for travels with every message in the chain. No Agent waits on another, so a cycle of requests cannot deadlock, and a chain that never ends is ended by the budgets of the Agents in it. Each link is a handling, with its own check, Gate decision and record. What a flow engine gives and this does not is a join: an Agent that must act only once several answers are in keeps that state itself.

<!-- markdownlint-disable MD033 -->
<picture>

<source media="(prefers-color-scheme: dark)" srcset=".github/assets/agent-mesh-chains-dark.svg">

<img alt="A UML sequence diagram, read top to bottom, with six lifelines: the bus, Agent A, the Gate, Agent B, the agent MCP gateway and an outside system. The bus delivers a message to Agent A, which asks the Gate to decide; the Gate allows its action, and Agent A performs it: it publishes a message on the bus. The bus delivers that message to Agent B, which, a note says, acts for the same Principal. Agent B asks the Gate to decide on its own action, the Gate allows it, and Agent B performs its action through the agent MCP gateway, which calls the outside system, at most once. A note says each link is its own handling: checked, gated and recorded. Each Agent&#x27;s handling performs one action, no Agent waits on another, and each Agent&#x27;s lifeline is its agent runtime." src=".github/assets/agent-mesh-chains-light.svg" width="576">

</picture>
<!-- markdownlint-enable MD033 -->

## 3.5 Command Line

`dwmesh` is the Operator's surface in a terminal: a client of the control API, and later of the doc server, with one subcommand per operation and no logic of its own. Its nouns are the Agent Mesh's own terms. A person signs in through the install's own identity provider; a program runs under its own Principal and is refused every Operator-only command (Identity and Security, below). Every command that changes something confirms first; a script may pass `--yes`, except on an Operator-only command, which always confirms interactively, so a hold is never answered unattended. Output is plain text, or JSON with `--json`. It needs no Portal: everything the Operator must answer is answered from it (Operator, below). Its commands are in The Command Line, below.

## 3.6 Control API

The control API is the REST service the command line calls, the Deployment `control-api` behind its Service, reached through an HTTPRoute or a port-forward. It is a controller over the Agent Mesh's use cases, with authentication: it proves the Principal of a person or a program that calls it, and accepts an Operator-only command from the Operator alone (Identity and Security, below).

## 3.7 Costs and Budgets

Before a proposer is asked, the cost of the handling is estimated and checked against the Agent's budget for the period, a count of messages and a cost. The actual cost is recorded afterwards and can exceed the estimate. Once the budget is reached, the Agent's new messages are refused until the period ends, and the Operator is told once; spending can pass the budget by the overruns of handlings already under way.

`dwmesh costs` shows each Agent's estimated and actual cost for a period, against its budget.

## 3.8 Definitions and Templates

Agents, their rules and budgets, the schedules, the subjects and their contracts, and the install's MCP connections, are declared in Markdown: plain text files under version control. An Agent's name is at most 32 characters. The **definitions** are those files at one merged revision; NATS fires the schedules (Schedules, below). The Agent Mesh ships the templates. In three layers, minimal, standard and full: an Agent's definition, with the subjects it may publish to, and the Book-Keeper and the Developer as example Agents; its instructions; a subject, with its contract and its publishers; a Principal; a schedule; the price table; and the definitions folder. Beside them: an MCP connection; the Planner's definition, with an example Planner and its rules for a tracker's tools; and the Watcher's definition, with the Jira Watcher as its example. Who may publish to a subject is declared on both sides, the subject and its publisher, so widening it takes both in one reviewed change. `dwmesh definitions check` checks the definitions offline (GitOps Configuration, below).

## 3.9 Doc Server

Planned for v1.x. The doc server indexes one folder of Markdown and answers searches. It reads the folder and never writes to it, and swaps a rebuilt index in whole. An Agent searches it only through the knowledge port, never directly; `dwmesh doc search` and the MCP server's search tool use it too. Whoever writes the folder steers every Agent that searches it, so the folder is trusted input, under the same review as the definitions. It is off by default, and listens only inside the cluster by default.

## 3.10 Durability

Each step of a handling is written to the record as an entry, in order, before the next step is taken, and the closing entry ends it. The record store outlives the Agent's pod; v1.0 ships an adapter for NATS JetStream. The entries follow the steps: the message received and the attempt, the check, the estimate, the proposal and its cost, the Gate's decision, the intent, the outcome and its cost, and the closing entry. The record is made durable before the proposer is asked and again before any action is performed, provided the store makes a write durable before acknowledging it; for JetStream that means sync on every write, on a volume that honours fsync, and, where there is more than one server, replicas in separate failure domains. Before that first durable point a message is only as safe as the bus holds it. From its first durable point a handling is never lost: if a pod crashes, the agent runtime reads the record back on restart, counts a new attempt, and carries on from the first entry not yet written. The one exception is an intent with no outcome: that action is never performed again, and the Operator is asked what happened. Each entry is written once and never changed: a second writer finds the entry already there and stops. With the intent's lease, and no retry after no answer, that is what keeps an action to one performance across crashes and restarts. The record is append-only and keeps every entry, message content included; v1.0 deletes and rotates nothing, so an install sizes the store for that and decides what may enter a message.

<!-- markdownlint-disable MD033 -->
<picture>

<source media="(prefers-color-scheme: dark)" srcset=".github/assets/agent-mesh-durability-dark.svg">

<img alt="A UML sequence diagram, read top to bottom, with two lifelines: the agent runtime and the record. The agent runtime writes each entry before the next step: received, attempt 1, then checked, the estimate and the proposal, then the Gate&#x27;s decision. The pod crashes. On restart, the agent runtime reads the record back, the record returns the entries written so far, and the runtime counts a new attempt, attempt 2, and carries on from the first entry not written, the intent. A note says an intent with no outcome is never performed again, and the Operator is asked." src=".github/assets/agent-mesh-durability-light.svg" width="576">

</picture>
<!-- markdownlint-enable MD033 -->

## 3.11 Four-Eyes Approval

Planned for v1.x. An install can declare **Approvers**, people who may approve or refuse a held action, from the command line or the Portal, and nothing else. A rule can hold an action for more than one approval, `hold 2` for two. Each approval is its own entry in the record, by a different person, and no one may approve a hold on work that acts for them, or raised by an Agent of their own. The approval that completes the count approves the action; any refusal refuses it at once. Once any Approver is declared, a reload that adds, removes or changes a role or a hold's count is itself held for an Approver who is not the Operator, so four-eyes binds the Operator too. v1.0 refuses the Approver role and any hold above one.

## 3.12 Action Gate

No action is performed unless a rule allows it, or holds it and the Operator approves and the Gate allows it again.

The Gate is plain code in the core. It reads the proposed action, the Agent's rules, the message's subject and the Principal the message acts for, which come from the record and no payload can change. It never reads the message's content. Whatever a misled proposer proposes, the most it gets is what the rules allow that Agent for that Principal; within an allowed tool, the proposer still chooses the target. The Gate does not make an allowed action right, which is why the Book-Keeper above holds paying a bill for the Operator and allows only recording one. The same proposed action, for the same Agent, on the same subject, on behalf of the same Principal, under the same definitions and the same approval, always gets the same decision, and an error refuses. The rules are rows the Gate reads through a port, and every rule-row adapter is tested for the same behaviour.

<!-- markdownlint-disable MD033 -->
<picture>

<source media="(prefers-color-scheme: dark)" srcset=".github/assets/agent-mesh-gate-dark.svg">

<img alt="A UML sequence diagram, read top to bottom, of the Book-Keeper handling a supplier invoice, with five lifelines: the agent runtime, the proposer, the Gate, the agent MCP gateway and Xero. A supplier invoice arrives at the agent runtime, which asks the proposer to propose one action; the proposer returns an action. The agent runtime asks the Gate to decide, and the Gate returns allow, hold or refuse. Then one of three alternatives. Allow, to record a bill: the agent runtime asks the agent MCP gateway to create the bill, at most once, and the gateway creates it in Xero. Hold, to pay a bill: a note says an approval waits for the Operator. Refuse, to delete a bill, which no rule matches: a note says it is refused and recorded. Every step is recorded before the next." src=".github/assets/agent-mesh-gate-light.svg" width="576">

</picture>
<!-- markdownlint-enable MD033 -->

## 3.13 GitOps Configuration

Three kinds, three paths. Settings, what a process connects to and how it runs, come from environment variables only: one named variable per setting, listed by `--help`, read once at start, and a missing or invalid value refuses the start. Secrets come by a mounted file through the secrets port; the variable names the path, never the value. Definitions, what the Agents may do, live in a repository of the install's own, where every change to what an Agent may do is a reviewed pull request: `dwmesh definitions check` checks them offline before merge, and only the Operator's reload puts a revision in force, recording its version. The template repository, `darkwave-agent-mesh-config`, holds the layout: `definitions/`, `deploy/` as kustomize, the mesh version it configures, and the check in CI. A merge applies what a revision's Agents need to run, through `kubectl apply -k` or Flux or Argo CD; only the Operator's reload then puts its rules in force, so the order is always apply, then reload. NATS comes by its own chart.

## 3.14 Identity and Security

Every input is checked against its written contract where it enters: shape, size and encoding, not meaning. Input that fails the check is refused and recorded, never repaired. A well-formed hostile instruction passes the check, which is why there is a Gate.

Every message carries two proved identities, both **Principals**: its sender's, and the one the work acts for, which is whoever started the chain of messages the work is. Each is proved where the message enters, by the connection for an Agent's own messages and by the control API, the service the command line calls, for a person's or a program's, and never read from the payload. A person signs in through the install's own identity provider, as one Principal on every surface; a program proves itself to the control API by a credential issued at its enrolment. The Gate decides for the Principal the work acts for. A program at the command line runs under its own Principal, and the control API accepts an Operator-only command from the Operator's own identity alone.

On the bus, each message's subject carries its sender, and NATS lets each connection publish only where the permissions generated from the definitions allow, so the bus itself proves who sent a message. Every connection to NATS uses mutual TLS. Each process writes the record under its own identity, and only the keys its work needs: an Agent's own handlings, and for the control API a person's proposal or a stated outcome. The record is append-only: the server is configured to refuse deletes and rewrites, and encryption at rest is the volume's. Secrets are read by adapters and the agent MCP gateway only, never by the core; the MCP connections' credentials are mounted into the gateway's container alone.

## 3.15 MCP Server

Planned for v1.x. An MCP client, such as an agent outside the mesh, connects to the MCP server, through a route when the install exposes one, to reach the mesh's Agents, messages and documents. The MCP server is a peer of the control API over the same use cases, not a client of it: it proves its caller's Principal as the control API does, adds no rule, and opens no path around the Gate. Its tools start read-only: listing Agents and their state, reading a definition, reading recent messages and searching documents. It is off until configured, and listens only inside the cluster unless configured otherwise.

## 3.16 Operator

Whatever only a person can decide reaches the Operator through one **exceptions queue**, and only the handling that asked pauses; everything else runs on, except an Agent over its budget, whose new messages are refused until the period ends. There are three kinds: an **approval**, when the Gate holds an action; a **problem**, when something went wrong, such as an action whose outcome is unknown; and a **proposal asked**, when the Operator's own Agent is asked to propose. The Operator answers from the command line: approve or refuse, acknowledge, resolve or retry, or propose. Each answer is written to the record like any other entry, the first answer in time wins, and the handling that asked resumes from the record, or for a retry a new message starts. An approval or a proposal asked that is left unanswered expires as refused. A ticket an Agent passes to the Operator in a tracker is the Operator's second wait (Planning and Dispatch Through a Tracker, below). The Operator's own Agent has no hold rules: what a person proposes is allowed or refused, never approved by the same person.

The Portal, planned for v1.x, is a second surface for the Operator (Portal, below).

<!-- markdownlint-disable MD033 -->
<picture>

<source media="(prefers-color-scheme: dark)" srcset=".github/assets/agent-mesh-operator-dark.svg">

<img alt="A UML sequence diagram, read top to bottom, with five lifelines: the agent runtime, the Gate, the exceptions queue, the control API and the Operator. The agent runtime asks the Gate to decide, and the Gate holds the action; the agent runtime puts an approval in the exceptions queue, and the handling waits. The Operator approves from the command line through the control API, which records the answer in the exceptions queue. The answer reaches the agent runtime, which asks the Gate to decide again; the Gate allows the action, and the handling resumes. A note says that, unanswered, the approval expires as refused." src=".github/assets/agent-mesh-operator-light.svg" width="576">

</picture>
<!-- markdownlint-enable MD033 -->

## 3.17 Outside Systems

Outside systems are reached through the agent MCP gateway. The Agent Mesh ships one agent MCP gateway, which runs as a sidecar container beside the agent runtime in each Agent's pod and holds the connections' credentials, and each outside system is an install's MCP connection: one Markdown file that declares the system's tools over its vendor's MCP server, documented in full and pinned to what the server serves. Its tools are the tools the rules can name, and the Gate decides each use of one.

A gateway passes the action id on where the system takes one, times out before the intent's lease runs out, and answers succeeded, failed only when the action certainly did not happen, or nothing when unsure; the at-most-once guarantee rests on that contract, and the conformance kit tests it.

## 3.18 Planning and Dispatch Through a Tracker

The Operator and the Agents hand work to each other through tickets in a tracker, Jira for example, the first the Agent Mesh fits. The Agent Mesh ships two roles for this, each a definition template with an example: the **Planner**, with its rules for the tracker's tools, and the **Watcher**, whose example is the Jira Watcher. The Planner raises, assigns and ranks tickets under those rules, which can hold an action for the Operator like any other. Assignment is the dispatch: an Agent takes up a ticket when its assignment reaches it as a message, and the Agent Mesh drives no sequence of its own.

Out, an Agent reaches the tracker through the agent MCP gateway, over the tracker's MCP server; the install declares the tracker's tools in its connection, and the Gate decides each use of a tool. In, Jira's changes reach the Agents as messages on the `ticket.*` subjects, published by the Jira Watcher, an Agent with a script proposer, in v1.0, and by the webhook ingress, planned for v1.x. On each firing of its schedule, the Jira Watcher reads what has changed in Jira through its own agent MCP gateway, and its one action publishes those changes, in order, as `ticket.*` messages. Any tracker fits the same pattern: an MCP connection out and a Watcher in.

There are two waits, each kept in its own record. An action the Gate holds waits in the exceptions queue, in the Agent Mesh's record, and is answered through the control API. A ticket passed to the Operator waits in the tracker, in the tracker's history; the Operator answers there, and the answer comes back as a new message that starts a new handling. Nothing in the tracker enters the exceptions queue.

<!-- markdownlint-disable MD033 -->
<picture>

<source media="(prefers-color-scheme: dark)" srcset=".github/assets/agent-mesh-planning-dark.svg">

<img alt="A UML sequence diagram, read top to bottom, with six lifelines: the Planner, the agent MCP gateway, Jira, the Jira Watcher, the Developer and the Operator. The Planner assigns a ticket in Jira, through the agent MCP gateway. The Jira Watcher reads the change through the agent MCP gateway and publishes it as a ticket.* message, which reaches the Developer. The Developer works the ticket and passes it to the Operator in Jira, through the agent MCP gateway, and the Operator answers there. The Jira Watcher reads that change the same way and brings the answer back to the Developer as a new message. The Planner, the Jira Watcher and the Developer are Agents, the Jira Watcher&#x27;s proposer a script; each Agent calls its own gateway, and the Jira Watcher publishes on the bus. A note says the tracker&#x27;s wait is in its own history, and nothing enters the exceptions queue." src=".github/assets/agent-mesh-planning-light.svg" width="576">

</picture>
<!-- markdownlint-enable MD033 -->

## 3.19 Portal

Planned for v1.x. The Portal is the Operator's surface in a browser, beside the command line: served by its own Deployment, `portal`, behind the same route, and a client of the control API that shows what the control API returns and answers the same exceptions. It adds no logic and reaches the record only through the control API. Every answer confirms first, showing the thing in full as the server returned it, and the control API refuses the answer if the thing has changed. A person signs in as on the command line (Identity and Security, above). Besides the Operator, a **Reader** may see the exceptions queue, the Agents and their health, read-only, without message content, traces or costs; an **Approver** may approve or refuse a held action (Four-Eyes Approval, above).

## 3.20 Proposers

Each Agent has one **proposer**, which proposes one action for each message. A proposer is a model, in the cloud or served in the cluster; a script, plain code for work that needs no model; or a person, the Operator, who is asked and answers from the command line. The Operator also has an Agent of their own, the one whose proposer is a person.

## 3.21 Schedules

A schedule, declared in the definitions, sends a message at its times, at an interval or by a cron expression in its time zone. Schedules and the expiries of unanswered approvals and proposals asked are NATS JetStream scheduled messages: the control API sets them, and NATS fires them, so the Agent Mesh keeps no clock of its own for them. Each fired message is keyed by its schedule, version and next fire time, so a repeat is acted on once (At-Most-Once Actions, above); an interval schedule fired again late can get a new key, and a reload restarts its interval.

## 3.22 Supported Platforms

v1.0 supports three platforms, each with its own guide: kind, for CI and local work; K3s, on a single server; and Amazon EKS, across three zones. A platform is supported when it meets the cluster's contract and the conformance runs pass on it. The contract: a supported Kubernetes minor version, NATS Server 2.14 or later, a network plugin that enforces network policies, volumes for NATS that honour fsync, Pod Security's restricted profile, the Gateway API or a port-forward to reach the control API, and nodes that are amd64 or arm64.

## 3.23 Verified by Specification

The message path is specified in [TLA+](https://lamport.azurewebsites.net/tla/tla.html), a language for specifying systems, and model-checked within its model's stated limits; v1.0 runs the checks in CI. A scenario suite, scripted from the specification's sequences, runs against the code. Each guarantee has an ID; a proof map names the TLA+ property, test suite or stated assumption behind it, and its limits, and a test that checks it carries the same ID where there is one.

---

# 4. The Command Line

How `dwmesh` is used; what it is, and who may run what, is in Command Line, above. Command names may change before v1.0.

```text
dwmesh definitions check definitions/            # offline, in the config repository's CI: every rule names a tool a connection declares
dwmesh agent list                                # every Agent, its state and its budget this period
dwmesh agent start book-keeper                   # Operator only; its open handlings resume first
dwmesh exception list --kind approval            # what is waiting on the Operator
dwmesh exception approve 7f3a                    # Operator only; the Gate decides the action again
dwmesh exception resolve 2c19 --outcome failed   # Operator only; states what an unknown action did
dwmesh message trigger invoice.received --id inv-42 --content - --yes < invoice.json
                                                 # a script publishes a message under its own identity
dwmesh message trace --agent book-keeper <trace id>   # one handling's entries, in order; a trace id is the sender and the message id
dwmesh handling list --open --agent book-keeper  # handlings with no closing entry
dwmesh costs --period 2026-10                    # estimated and actual cost, against each Agent's budget
dwmesh health                                    # the bus, the record store, and each Agent's last entry and open handlings
```

After v1.0, the doc server adds `dwmesh doc search`, which returns what an Agent's own search would.

---

# 5. Extending It

Models, the bus, the record store, the rule rows, telemetry and secrets plug in at **ports**: interfaces the core, the message path and the Gate, defines and an adapter implements. One conformance kit tests every adapter of a port against the same contract.

There are four ways to extend an install: two are files, and two are development, a custom MCP server of the install's own and a custom Rust adapter built into a release.

- **Add an Agent**: one Markdown file, as above. It takes effect at the next reload of the definitions.
- **Connect a system**: one Markdown file, an MCP connection; the gateway, a container of its own, needs no change (Outside Systems, above).
- **Build an MCP server**: custom development, in any language, for a system that has no MCP server of its own. The install runs it, and connects it with one Markdown file like any other; it answers as the gateway's contract needs, taking the action id where it can and reporting a failure only when the action certainly did not happen (Outside Systems, above). It is not the Agent Mesh's own MCP Server (MCP Server, above).
- **Swap a part**: custom Rust development. A model provider, the bus, the record store, the rule rows, telemetry or secrets is each an adapter of a port: a Rust crate that implements the port's trait, built into a release, which passes the conformance kit before it is trusted.

Nothing in the core changes for any of the four.

<!-- markdownlint-disable MD033 -->
<picture>

<source media="(prefers-color-scheme: dark)" srcset=".github/assets/agent-mesh-extending-dark.svg">

<img alt="Read left to right. On the left, the core: the domain and the message path, plain Rust, which depends only on its ports. In the middle, seven of its ports, the Rust traits it defines: Proposer, Bus, Record (RecordWriter and RecordReader), Gate, TelemetryWriter, SecretReader and ActionGateway; the core calls each. On the right, the adapter that implements each port and ships with the Agent Mesh: a model provider, which may instead be a script or a person; NATS JetStream for the bus and for the record; rule rows for the Gate; Prometheus for telemetry; Kubernetes Secrets for secrets; and the agent MCP gateway, a sidecar container, for actions. Above the core, an Agent definition, a Markdown file the install supplies, is loaded on reload. Below the ports, an MCP connection, a Markdown file the install supplies, is read by the gateway. Below the gateway, the two kinds of MCP server it calls over MCP: a vendor&#x27;s, outside the mesh, and the install&#x27;s own. The captions say that each adapter implements one port and passes the conformance kit; that an Agent and a connection are Markdown files read at a reload; that swapping a part is a Rust crate of the install&#x27;s own built into a release; and that an MCP server of the install&#x27;s own, in any language, is reached like a vendor&#x27;s." src=".github/assets/agent-mesh-extending-light.svg" width="576">

</picture>
<!-- markdownlint-enable MD033 -->

Three parts of v1.0 are still being designed: a proposer's reads, read-only tool calls it makes through its Agent's gateway before it proposes, each allowed by a rule and recorded, and never the handling's one action, such as the Jira Watcher's reads of Jira (Planning and Dispatch Through a Tracker, above); an action that publishes several messages, such as the Jira Watcher's; and the gateway's contract over its socket, which the conformance kit will test.

## 5.1 Connector Catalogue

Examples only: systems whose vendors provide their own MCP server, most hosted by the vendor; a row marked "run by the install" is a server the install runs itself. Any system with an MCP server connects the same way, with one MCP connection (Outside Systems, above). The table shows the reach, not a support list: none is tested by the Agent Mesh before v1.0, and each server's tools, terms and availability are its vendor's.

| System | What an Agent reaches | The vendor's MCP server |
|---|---|---|
| Asana | Tasks, projects and goals | [Asana MCP server](https://developers.asana.com/docs/using-asanas-mcp-server) |
| Atlassian | Jira work items, Confluence pages | [Atlassian Rovo MCP](https://developer.atlassian.com/cloud/rovo-mcp/) |
| AWS | AWS APIs and documentation | [AWS MCP Server](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/mcp-server.html) |
| Azure | Azure resources, under the caller's Azure roles (run by the install) | [Azure MCP Server](https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/overview) |
| Box | Files, folders and content | [Box MCP Server (remote)](https://developer.box.com/guides/box-mcp/remote/) |
| Canva | Designs, assets and exports | [Canva MCP](https://canva.dev/docs/mcp/) |
| Databricks | Data, Unity Catalog functions and Genie spaces | [MCP on Databricks](https://docs.databricks.com/aws/en/generative-ai/mcp/) |
| Docusign | Agreements, envelopes and signing | [Docusign MCP Server](https://developers.docusign.com/tools/mcp-server/) |
| Dropbox | Files and folders | [Dropbox remote MCP server](https://help.dropbox.com/integrations/connect-dropbox-mcp-server) |
| GitHub | Repositories, issues and pull requests | [GitHub MCP Server](https://github.com/github/github-mcp-server) |
| Gmail | Mail: search, read and drafts (a developer preview) | [Google Workspace MCP servers](https://developers.google.com/workspace/guides/configure-mcp-servers) |
| Google Calendar | Calendars and events (a developer preview) | [Google Workspace MCP servers](https://developers.google.com/workspace/guides/configure-mcp-servers) |
| Google Docs | Documents (a developer preview) | [Google Workspace MCP servers](https://developers.google.com/workspace/guides/configure-mcp-servers) |
| Google Drive | Files and folders (a developer preview) | [Google Workspace MCP servers](https://developers.google.com/workspace/guides/configure-mcp-servers) |
| Google Sheets | Spreadsheets (a developer preview) | [Google Workspace MCP servers](https://developers.google.com/workspace/guides/configure-mcp-servers) |
| Google Slides | Presentations (a developer preview) | [Google Workspace MCP servers](https://developers.google.com/workspace/guides/configure-mcp-servers) |
| Grafana Cloud | Dashboards, metrics, logs and alerts | [Grafana Cloud MCP servers](https://grafana.com/docs/grafana-cloud/ai-tools/mcp-servers/) |
| HubSpot | CRM records | [HubSpot MCP Server](https://developers.hubspot.com/mcp) |
| Intercom | Customer conversations and contacts | [Intercom MCP server](https://developers.intercom.com/docs/guides/mcp) |
| Linear | Issues, projects and cycles | [Linear MCP server](https://linear.app/docs/mcp) |
| Lucid | Lucidchart and Lucidspark documents and diagrams | [Lucid MCP server](https://help.lucid.co/hc/en-us/articles/42578801807508) |
| Microsoft 365 | Mail, calendar, meetings, Teams messages and documents, through Work IQ (run by the install; billed through Copilot Studio) | [Work IQ](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/work-iq/cli) |
| monday.com | Boards, items and updates | [monday.com MCP](https://developer.monday.com/api-reference/docs/mondaycom-mcp) |
| MongoDB | Databases and collections: hosted for Atlas (run by the install for any other deployment) | [MongoDB MCP Server](https://www.mongodb.com/docs/mcp-server/overview/) |
| Neon | Serverless Postgres projects and databases | [Neon MCP Server](https://neon.com/docs/ai/neon-mcp-server) |
| Notion | Pages and databases | [Notion MCP](https://developers.notion.com/docs/mcp) |
| Oracle Database | SQL and PL/SQL through SQLcl (run by the install) | [Oracle MCP Servers](https://www.oracle.com/mcp/) |
| PayPal | Orders, invoices, payments and disputes | [PayPal MCP server](https://developer.paypal.com/tools/mcp-server/) |
| Redis | Keys and data structures (run by the install) | [Redis MCP Server](https://github.com/redis/mcp-redis) |
| Salesforce | CRM records and Salesforce data | [Salesforce Hosted MCP Servers](https://developer.salesforce.com/docs/platform/hosted-mcp-servers/guide) |
| Slack | Channels, messages and search | [Slack MCP server](https://docs.slack.dev/ai/mcp-server/) |
| Snowflake | Data, Cortex Search and Cortex Analyst | [Snowflake-managed MCP server](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp) |
| Sourcegraph | Code search and navigation across an organisation's repositories, on its Sourcegraph instance | [Sourcegraph MCP Server](https://sourcegraph.com/docs/api/mcp) |
| SQL Server and Azure SQL | Tables and views through Data API builder (run by the install) | [SQL MCP Server](https://learn.microsoft.com/en-us/azure/data-api-builder/mcp) |
| Stripe | Customers, payments, invoices and subscriptions | [Stripe MCP](https://docs.stripe.com/mcp) |
| Supabase | Postgres databases, auth and storage | [Supabase MCP Server](https://github.com/supabase/mcp) |
| Xero | Accounting: contacts, invoices, bills and payments | [Xero remote MCP](https://developer.xero.com/documentation/guides/remote-mcp/overview/) |
| Zoom | Meetings, recordings and summaries | [Zoom MCP servers](https://developers.zoom.us/docs/mcp/servers/) |

A system with no MCP server of its own is reached by building one (Extending It, above).

---

# 6. What v1.0 Holds

- The message path, specified in TLA+ and model-checked in CI, with the scenario suite and the proof map
- The Gate, with rule rows as its first adapter
- The exceptions queue: approvals, problems and proposals asked, answered by the Operator
- Agents, rules, budgets and schedules declared in Markdown, with a definition template and example Agents, the Book-Keeper and the Developer
- The Planner's definition template and example, with its rules for a tracker's tools
- The Watcher's definition template, with the Jira Watcher as its example, which publishes Jira's changes as `ticket.*` messages
- One agent MCP gateway, with a template for an install's connections, run as a sidecar container in each Agent's pod
- The agent runtime: one process per Agent, in its own pod on Kubernetes, beside its agent MCP gateway, with recovery from the record and an attempt limit
- A REST control API and the command line, `dwmesh`, with authentication
- The config repository template, `darkwave-agent-mesh-config`, with the offline definitions check in its CI
- One model provider adapter, for a model in the cloud or served in the cluster; a script proposer; and the Operator as proposer
- Bus and record store adapters on NATS JetStream
- Telemetry through a port, Prometheus by default, and secrets read by adapters and the agent MCP gateway only
- An adapter conformance kit and a benchmark harness
- kind, K3s and Amazon EKS as supported platforms, each with its guide

v1.0 is built from source: the install builds the three images, `darkwave/agent-runtime`, `darkwave/agent-control-api` and `darkwave/agent-mcp-gateway`, into its own registry. After v1.0: a web portal, four-eyes approval (another person, an Approver, approves a held action), a webhook ingress, an MCP server, a doc server that lets Agents search a folder of Markdown, checking of the runtime's own recorded traces against its specification, a Helm chart and published container images.

---

# 7. Who Builds It

Darkwave Trading Limited, a proprietary trading firm in New Zealand. Darkwave Trading builds the Agent Mesh to run its own agentic business.

---

# 8. Built With

The agent runtime, the control API and `dwmesh` are written in Rust, as static binaries with no interpreter or virtual machine beneath them.

<!-- markdownlint-disable MD033 -->
<picture>

<source media="(prefers-color-scheme: dark)" srcset=".github/assets/rust-logo-dark.svg">

<img alt="The Rust logo" src=".github/assets/rust-logo-light.svg" width="64" height="64">

</picture>
<!-- markdownlint-enable MD033 -->

---

# 9. Contributing

Contributions are not taken before v1.0. How they are taken from then on is in `CONTRIBUTING.md`, published with it; GitHub receives releases, and nothing is merged there.

---

# 10. Licence

Licensed under the Apache License 2.0; see [LICENSE](LICENSE).

Xero, Gmail, Google Workspace, Google Calendar, Google Docs, Google Drive, Google Sheets, Google Slides, Microsoft 365, Work IQ, Azure, Teams, Copilot Studio, Docusign, GitHub, Slack, Claude, Atlassian, Rovo, Jira, Confluence, AWS, Grafana, HubSpot, Lucid, Lucidchart, Lucidspark, Asana, Canva, Linear, Notion, Salesforce, Sourcegraph, Stripe, Box, Databricks, Unity Catalog, Dropbox, Intercom, monday.com, MongoDB, Atlas, Neon, Oracle, PayPal, Redis, Snowflake, Cortex, PostgreSQL, Postgres, SQL Server, Supabase, Zoom, Kubernetes, K3s, Amazon EKS, NATS, Prometheus, Flux and Argo CD are trademarks of their owners; the Agent Mesh is not affiliated with or endorsed by them. The Rust logo is a trademark of the Rust Foundation, shown under CC BY 4.0 to say what the Agent Mesh is written in; the Rust project endorses nothing here. The figures' Kubernetes icons are from the Kubernetes Icons Set, under the Apache License 2.0.

© 2026 Darkwave Trading Limited
