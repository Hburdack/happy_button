# Happy Buttons — PRD: Agentic Simulation System (v2)

**Date:** 2025-09-24
**Owner:** Zetify Product
**Scope:** Four-step staged rollout (Releases 2–5) to first simulate a classic company (no Zetify), then inject weaknesses, then enable Zetify Observe/DDT, and finally hand over the info@ mailbox to Zetify and prove KPI uplift.

---

## 0) Executive Summary
We deliver a live, agent-friendly simulation of *Happy Buttons (h-bu.de)*. Step 1 runs as a **classic company** without Zetify; Step 2 injects **organizational weaknesses**; Step 3 introduces **Zetify Observe + Dynamic Digital Twin (DDT)**; Step 4 **switches info@** to Zetify automation and demonstrates **KPI improvements**.

---

## 1) Goals & Non-Goals
### Goals
- G1: Realistic classic company simulation (email-driven Order-to-Delivery) with visible processes.
- G2: Scenario injection to expose typical failure modes (late triage, missed expedite, VIP request, global disruption).
- G3: Zetify Observe builds a Dynamic Digital Twin (Knowledge Graph) from history + live events.
- G4: Zetify takes over info@ processing and improves KPIs, demonstrated on a web scoreboard.
### Non-Goals (v2)
- No real ERP/WMS/CRM integration (stubs ok).
- No payment processing; invoices simulated.

---

## 2) Personas
- CEO/Investor: See business value & culture.
- CIO: See operations, integration & auditability.
- BPO: See process KPIs & improvements.
- Engineer: Implement agents/services from this PRD.

---

## 3) Success Metrics
- Auto-handled share (info@) ≥ 70% (post Zetify)
- Avg response time (info@) ≤ 1h (post Zetify)
- DDT coverage ≥ 95% relevant entities/edges
- On-time ship (baseline classic) ≥ 90% in happy path

---

## 4) Architecture Overview
Layers: Interface (Mail), Agent, Process/Policy (YAML configs), Data (Event Bus, Graph, Metrics, ObjectStore), Observability (Dashboard).

Agents per business unit (Info, Sales, Production, Logistics, Finance, Quality, Support, Purchasing, HR, Mgmt). Order is the single source of truth with a defined state machine.

---

## 5) Data Contracts
### EmailEvent
- id, ts, source_mailbox, from, to, subject, body, attachments[]
### AttachmentParsed (order|invoice)
- attachment_id, type, payload{{order|invoice}}
### RoutingDecision
- email_id, route_to, reason
### OrderAggregate
- id, channel, items[], priority, sla, status, history[]

---

## 6) Policies (as Code)
- Royal courtesy enforcement for outbound mails
- Priority rules: OEM > B2C; expedite intent detection
- Escalation (ambiguous → management@), SLA alerts

---

## 7) Simulation
- 30 days history + repeatable day script
- Generators: endcustomer_order_pdf, oem_bulk_order_pdf, supplier_conf, invoice_pdf, customer_question, complaint, global_disruption

---

# Releases

## Release 2 — **Classic Company Simulation (no Zetify)**
**Objective:** Show Happy Buttons running like a normal company with visible process steps and an email-driven Order-to-Delivery flow.

**Deliverables**
- Email ingest (IMAP/SMTP) for 10 mailboxes (or start with 2 and scale to 10).
- Order engine with state machine: CREATED→CONFIRMED→PLANNED→IN_PRODUCTION→PRODUCED→PACKED→SHIPPED→DELIVERED→INVOICED→CLOSED.
- Unit agents wired (Info/Sales/Production/Logistics/Finance/Quality/Support/Purchasing/HR/Mgmt) with stubs where needed.
- PDF parser (order/invoice → JSON), deterministic templates.
- Dashboard (MVP): live flow for emails & orders, KPI tiles (Response time, Exceptions, On-time ship).
- History seeder (30 days) + repeatable day script.

**Acceptance Criteria**
- E2E: An emailed order flows through to “Delivered” and “Invoiced” with all intermediate events visible.
- Dashboard shows live steps + KPIs.
- Sample history replay works deterministically (seeded).

---

## Release 3 — **Weakness Injection (classic org)**
**Objective:** Demonstrate typical failure modes of a non-Zetify org by injecting scenarios on top of Release 2.

**Scenarios to inject**
1) **Late triage**: email to info@ is processed too late → customer issue → KPI hit (response time > SLA).
2) **Missed expedite**: email offers “10× profit if 24h delivery” → not processed in time → lost opportunity.
3) **VIP (Royal Blue)**: priority request from royal household ignored → reputational risk.
4) **Global disruption**: Suez canal blockage → supply delays → orders slip; KPIs go red.

**Mechanics**
- Scenario toggles in `usecases/classic_org_scenarios.yaml`.
- For each scenario: scripted emails/events + KPI expectations.
- Dashboard marks incidents and shows impact.

**Acceptance Criteria**
- Each scenario visibly degrades KPIs on the dashboard.
- Postmortem logs show when/why the org failed (no Zetify).

---

## Release 4 — **Zetify Observe & DDT**
**Objective:** Enable Zetify’s Observe phase, ingest history + live events to construct a Dynamic Digital Twin (Knowledge Graph).

**Deliverables**
- Graph adapter (Neo4j or JanusGraph) + event-to-graph mapping.
- KG schema: Party, Mailbox, Email, Attachment, Order, Invoice, Agent, Rule, Site, Event, Policy.
- DDT coverage tile on dashboard; pattern extraction (triage rules, priority behavior).

**Acceptance Criteria**
- DDT coverage ≥ 95% after 1 replayed day.
- Graph queries return correct relationships (e.g., info@ → routing patterns; OEM priority).

---

## Release 5 — **Zetify Automation on info@ + KPI Uplift**
**Objective:** Switch info@ handling to Zetify agents and demonstrate KPI improvements vs. Release 3 baseline.

**Deliverables**
- Zetify Agent Creator deploys runtime agents for info@ (classification, parsing, routing, royal replies, SLA/expedite).
- Policy-as-Code v1 for courtesy/priority/escalation.
- Web scoreboard page showing “Before/After Zetify” KPIs.

**Acceptance Criteria**
- Auto-handled share ≥ 70%; avg response ≤ 1h for info@.
- Scenarios from Release 3 now resolved automatically (expedite handled, VIP handled, late triage prevented).
- Scoreboard reflects improvements with time range selector.

---

## Roadmap Snapshot
- R2: classic E2E + dashboard
- R3: weakness scenarios
- R4: Observe + DDT build
- R5: Automate info@ + show KPI uplift
