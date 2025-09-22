# **🧾 Product Requirements Document (PRD)**

**Project:** Happy Buttons – Agentic Simulation System (Company \+ Use Case)

**Version:** v1.0

**Date:** 2025‑09‑20

**Owner:** Zetify Product (Enterprise Architect & AI-Product Strategy)

---

## **0\) Executive Summary**

We build a **fully agentic, configurable simulation** of the company *Happy Buttons (h-bu.de)*. Das System besteht aus einer **Unternehmenskonfiguration (CompanyConfig)** und **Use-Case-Konfigurationen (UseCaseConfig)**, wird über einen **Order‑gesteuerten End‑to‑End‑Prozess** orchestriert und ist **live beobachtbar** via Dashboard. Es nutzt den bestehenden **Mailserver** (IMAP/SMTP) und erzeugt/ verarbeitet **realistische, fehlerfreie englische E‑Mails mit PDF‑Anhängen** (Orders/Invoices) gemäß der **Royal English Courtesy** Unternehmenskultur. Ziel ist ein belastbarer Proof für Zetify: *Observe → Pattern Recognition → Dynamic Digital Twin (Knowledge Graph) → Agent Creator Runtime → KPI‑Value Nachweis*.

---

## **1\) Goals & Non‑Goals**

### **1.1 Goals**

* **G1:** Simulierbares, konfigurierbares **Unternehmensabbild** (Happy Buttons) mit 10 Mailboxen und externen Beziehungen.

* **G2:** **Use Case „info@“**: Automatisches Triage, Parsing, Routing, höfische Auto‑Replies, KPI‑Erfassung.

* **G3:** **Order‑to‑Delivery End‑to‑End‑Fluss** (Order → Production → DC/Logistics → Shipment → Invoice) mit Events/States.

* **G4:** **Dynamic Digital Twin (DDT)** im **Knowledge Graph** aus Live‑Events (Observe‑Proof).

* **G5:** **Dashboard (MVP)** mit Live‑Flows (Swimlane) und KPIs (Auto‑Handled %, Avg Response, etc.).

* **G6:** **Historie** (30 Tage) \+ **wiederholbarer Tagesablauf** \+ optionaler **Dynamikmodus**.

* **G7:** **Policy‑as‑Code** (Royal Courtesy, Prioritäten OEM\>B2C, Eskalationen, SLAs).

* **G8:** **Auditability** & **Replay** für Demos/Tests.

  ### **1.2 Non‑Goals (v1)**

* Keine reale Anbindung an ERP/CRM/WMS – Stubs/Adapters genügen.

* Keine Bezahlabwicklung; Finance simuliert Rechnungen/Zahlungsstatus.

* Keine komplexe Produktionsoptimierung; einfache Heuristiken reichen.

  ---

  ## **2\) Personas & Primary Users**

* **CEO / Investor:** Versteht Business Value & Kultur‑Differenzierung (Royal Courtesy), sieht KPI‑Impact.

* **CIO:** Sieht Integration, Agenten‑Orchestrierung, Governance, Audit Trails.

* **BPO (Business Process Owner):** Erkennt Prozessverbesserung (Triage Quote, Response Time).

* **Engineer / Claude Code:** Kann aus PRD direkt Services/Agenten/Configs implementieren.

  ---

  ## **3\) Success Metrics (KPIs)**

* **KM1:** Auto‑Handled Share (info@): **≥ 70%**

* **KM2:** Average Response Time (info@): **≤ 1h**

* **KM3:** End‑to‑End On‑Time‑Ship Rate (E2E‑Sim): **≥ 90%** (bei nicht‑expeditierten Orders)

* **KM4:** Policy Compliance (Royal Courtesy, Priorities): **100%**

* **KM5:** DDT Coverage: **≥ 95%** der relevanten Entitäten/Beziehungen im Graph erfasst

  ---

  ## **4\) System Capabilities**

1. **Mail Ingestion:** IMAP/POP3 lesen, SMTP senden; Multi‑Mailbox, Entitätserkennung.

2. **Attachment Parsing:** PDF (Orders/Invoices) zu JSON Schema (deterministisch, fehlerfrei Englisch).

3. **Triage & Routing:** Klassifikation (Endcustomer/OEM/Supplier/Finance/Support/Quality) → Weiterleitung.

4. **Auto Reply:** Royal‑Courtsy‑Vorlagen, Signatur, SLA‑Hinweise.

5. **Order Engine:** Order als zentrale State Machine; Events treiben Agents an.

6. **Policy Engine:** Prioritäten, Eskalation, SLAs, Kultur; versionierbar (Policy‑as‑Code).

7. **Knowledge Graph (DDT):** Live‑Graph aus Events (Nodes/Edges), Query‑fähig.

8. **Observability:** Live‑Flow‑Visualisierung, KPIs, Audit Trails, Replay.

9. **Simulation & History:** Generatoren für 30 Tage Historie \+ Day Script.

   ---

   ## **5\) Architecture Overview**

**Layered Architecture:**

* **Interface Layer:** MailIngest, Webhooks, File Drop

* **Agent Layer:** InfoAgent, SalesAgent, ProductionAgent, LogisticsAgent, FinanceAgent, QualityAgent, SupportAgent, PurchasingAgent, HRAgent, MgmtAgent, Orchestrator, KPIAgent, Historian, SLA/ExpediteAgent, AttachmentParserAgent, Classifier/TriageAgent, RoutingAgent

* **Process & Policy Layer:** CompanyConfig, UnitConfig, UseCaseConfig, Policy Engine

* **Data Layer:** Event Bus (Queue), Knowledge Graph (DDT), Metrics Store, Object Store (attachments)

* **Observability Layer:** FlowViz Dashboard, KPI Tiles, Audit Log & Replay

**Reference Tech (suggested, replaceable):**

* Queue: Kafka/RabbitMQ; Graph: Neo4j/JanusGraph; Metrics: Prometheus \+ Grafana; Object Store: S3‑compatible; PDF: pdfplumber/PyPDF2 \+ rules; Runtime: Python/TypeScript services; UI: React \+ WebSocket streams; Containers: Docker/K8s.

  ---

  ## **6\) Agents & Responsibilities (per Business Unit)**

*Pro Einheit ein eigenständiger Agent, zentral konfigurierbar via UnitConfig.*

| Agent | Inputs | Core Actions | Outputs | KPIs |
| ----- | ----- | ----- | ----- | ----- |
| **InfoAgent** | info@, Events | Triage Kickoff, dedup, spam‑filter | RouteCmd, AutoReply | triage\_accuracy |
| **SalesAgent** | orders@, oem1@, Order.Created | Validate, create/merge order, confirm | Order.Confirmed, Reply | order\_intake\_time |
| **ProductionAgent** | Order.Confirmed | Capacity check, schedule | Order.Planned, Production.WIP/Produced | plan\_latency |
| **LogisticsAgent** | Production.Produced, logistics@ | DC select, pack, ship | Logistics.Packed, Shipment.TrackingUpdated | on\_time\_ship\_rate |
| **FinanceAgent** | finance@, Delivered | Generate/validate invoice | Finance.Invoiced, Finance.Paid (sim) | invoicing\_cycle\_time |
| **QualityAgent** | quality@, Production.WIP | Inspect, block/release | Quality.IssueRaised/Released | defect\_rate |
| **SupportAgent** | support@ | FAQ, clarifications | Reply, Escalation | fcr\_rate |
| **PurchasingAgent** | supplier@ | Material PO, confirmations | Supply.Confirmed | supply\_lead\_time |
| **MgmtAgent** | escalations | Resolve, override | Decision.Log | escalation\_resolution\_time |
| **Classifier/TriageAgent** | info@ | classify sender/intent | Classification.Result | triage\_precision |
| **AttachmentParserAgent** | attachments | parse PDF (order/invoice) | AttachmentParsed | parse\_success\_rate |
| **RoutingAgent** | Classification.Result | route to mailbox/queue | RouteApplied | routing\_accuracy |
| **SLA/ExpediteAgent** | text intents | detect expedite offers | PrioritySet, Alerts | expedite\_response\_time |
| **KPIAgent** | all events | aggregate metrics | KPI snapshots | kpi\_freshness |
| **HistorianAgent** | all events | event sourcing, replay | History snapshots | coverage |
| **Orchestrator** | all | coordination, retries, idempotency | Process state | e2e\_reliability |

---

## **7\) Configuration Model**

### **7.1 CompanyConfig (global)**

```
company:
  name: Happy Buttons GmbH
  domain: h-bu.de
  culture:
    royal_english_courtesy: true
    greeting: "We are most delighted to serve you."
    signature: |
      With the greatest pleasure,
      Happy Buttons Service
  sla:
    default_response_hours: 12
    expedite_window_hours: 24
priority:
  oem_over_b2c: true
escalation:
  ambiguous_to: management@h-bu.de
mailboxes:
  - info@h-bu.de
  - orders@h-bu.de
  - oem1@h-bu.de
  - supplier@h-bu.de
  - logistics@h-bu.de
  - support@h-bu.de
  - hr@h-bu.de
  - finance@h-bu.de
  - quality@h-bu.de
  - management@h-bu.de
sites:
  production: [CN, PL, MX, MD]
  distribution: [NY, MD]
systems:
  erp: stub
  crm: stub
  wms: stub
```

### **7.2 UnitConfig (template)**

```
unit: <sales|production|logistics|finance|quality|support|purchasing|hr|mgmt|info>
inputs:
  mailbox: <unit@h-bu.de|null>
  events: [<EventTypes>]
policies:
  ruleset_ref: default
  thresholds:
    max_retry: 3
    confirm_window_mins: 30
actions:
  - <action1>
  - <action2>
kpis:
  - name: <kpi_name>
    target: <value>
```

### **7.3 UseCaseConfig (info@ v1)**

```
use_case:
  name: info_mail_handling
  sources: [info@h-bu.de]
  rules:
    triage:
      order_pdf: orders@h-bu.de
      invoice_pdf: finance@h-bu.de
      supplier_keywords: supplier@h-bu.de
      complaint_keywords: quality@h-bu.de
      else: support@h-bu.de
    priority:
      oem_domain_list: [oem1.com]
    escalation:
      ambiguous: management@h-bu.de
  autoreply:
    enabled: true
    style: royal
    templates:
      order_received: "We are most delighted to confirm receipt of your order…"
      generic_ack: "Kindly note we have received your message and shall revert most promptly."
  kpi_targets:
    auto_handled_share: 0.70
    avg_response_hours: 1
  sim:
    history_days: 30
    day_script:
      morning: [endcustomer_order_pdf, oem_bulk_order_pdf, supplier_delivery_conf]
      afternoon: [invoice_pdf, customer_question]
      evening: [urgent_oem_order]
```

---

## **8\) Data & Events**

### **8.1 Email Event (ingest)**

```
{
  "id": "eml_20250920_001",
  "timestamp": "2025-09-20T08:05:22Z",
  "source_mailbox": "info@h-bu.de",
  "from": "alice@example.com",
  "to": ["info@h-bu.de"],
  "subject": "Order Inquiry",
  "body": "Please find attached our purchase order.",
  "attachments": [{"id":"att_01","filename":"PO_1001.pdf","mimetype":"application/pdf"}],
  "headers": {"Message-Id":"<...>"}
}
```

### **8.2 AttachmentParsed (order PDF → JSON)**

```
{
  "attachment_id": "att_01",
  "type": "order",
  "order": {
    "order_id": "HB-PO-1001",
    "channel": "B2C",
    "customer": {"name": "Alice Co.", "email": "alice@example.com"},
    "items": [
      {"sku":"BTN-4H-FASH-RED-S","qty":200},
      {"sku":"BTN-2H-OEM-WHITE-15","qty":10000}
    ],
    "notes": "please ship asap"
  }
}
```

### **8.3 Classification.Result**

```
{"email_id":"eml_20250920_001","intent":"order","party":"endcustomer|oem|supplier|finance|support|quality"}
```

### **8.4 Routing Decision**

```
{"email_id":"eml_20250920_001","route_to":"orders@h-bu.de"}
```

### **8.5 Order Aggregate (source of truth)**

```
{
  "id":"HB-2025-000123",
  "channel":"B2C",
  "priority":"NORMAL|HIGH|EXPEDITE",
  "items":[{"sku":"BTN-4H-FASH-RED-S","qty":200}],
  "sla":{"promised_ship_by":"2025-09-22T16:00:00Z"},
  "status":"CREATED",
  "history":[{"event":"Order.Created","ts":"2025-09-20T08:10:00Z"}]
}
```

### **8.6 Events (selection)**

* Order.Created, Order.Confirmed, Order.Planned, Production.WIP, Production.Produced, Logistics.Packed, Shipment.TrackingUpdated, Delivered, Finance.Invoiced, Finance.Paid, Quality.IssueRaised, Escalation.Raised.

  ---

  ## **9\) State Machines**

  ### **9.1 Order State**

CREATED → CONFIRMED → PLANNED → IN\_PRODUCTION → PRODUCED → PACKED → SHIPPED → DELIVERED → INVOICED → CLOSED

**Side paths:** ON\_HOLD, ESCALATED, CANCELLED, RETURNED.

### **9.2 Email Handling State**

INGESTED → CLASSIFIED → PARSED → ROUTED → REPLIED → CLOSED (or ESCALATED)

---

## **10\) Policy‑as‑Code (Royal, Priority, Escalation, SLA)**

* **Royal Courtesy:** All outbound replies: royal templates \+ signature; block send if style not matched.

* **Priority:** if sender\_domain in oem\_domain\_list → priority=HIGH; if body contains "deliver in 24h" AND "pay 4x" → priority=EXPEDITE.

* **Escalation:** if classification=ambiguous OR parse\_failed → route management@.

* **SLA:** Response deadline from CompanyConfig; alerts on breach; expedite window 24h.

**Example (Rego‑like pseudo):**

```
priority := "EXPEDITE" {
  contains(lower(input.body), "deliver in 24h")
  contains(lower(input.body), "pay 4x")
}
priority := "HIGH" {
  input.sender_domain == "oem1.com"
}
```

---

## **11\) Simulation Design**

### **11.1 Generators**

* endcustomer\_order\_pdf, oem\_bulk\_order\_pdf, supplier\_delivery\_conf, invoice\_pdf, customer\_question, complaint\_pdf.

  ### **11.2 Day Script (repeatable)**

* **Morning (08‑11):** 3× Endcustomer Orders, 1× OEM bulk, 1× Supplier conf

* **Afternoon (12‑15):** 2× Invoices, 1× Question, 1× Quality case

* **Evening (16‑18):** 1× Urgent OEM expedite (24h offer)

  ### **11.3 History Seeder**

* 30 Tage, konfigurierbare Verteilungen; deterministische Seeds; PII‑Scrubber.

  ---

  ## **12\) Email & PDF Specs**

  ### **12.1 Email Requirements**

* Sprache: **Englisch**, fehlerfrei; klare Betreffzeilen; strukturierte Inhalte.

* Royal Courtesy in **outbound replies**.

  ### **12.2 PDF – Order (minimal)**

* Order ID, Customer, Lines\[sku, description, qty\], Requested Date, Destination.

  ### **12.3 PDF – Invoice (minimal)**

* Invoice ID, Order ID, Bill To, Amount, Due Date.

**Parsing:** Regex/rule‑based; fallback: deterministic templates; output: JSON per 8.2.

---

## **13\) External Integrations**

* **Mail Server:** IMAP read (poll/IDLE), SMTP send; credentials per env vars.

* **ERP/CRM/WMS:** v1 Stubs; later REST adapters.

* **Logistics API:** stub endpoints for label/tracking.

  ---

  ## **14\) Observability & Dashboard**

* **FlowViz:** Web UI, per email & per order; status chips; WebSocket live stream.

* **KPI Tiles:** Auto‑Handled %, Avg Response Time, Exceptions, OEM vs B2C Mix, On‑Time‑Ship.

* **Audit Trail:** full decision path (agent, rule hits, payload excerpts).

* **Replay:** pick a day/order/email → replay with same seeds.

  ---

  ## **15\) Security & Compliance**

* PII scrubbing for synthetic data generation; never use real customer PII.

* Secrets via env/secret manager; role‑based access to dashboards.

* Full audit log; signed event hashes (optional).

  ---

  ## **16\) Non‑Functional Requirements**

* **Reliability:** ≥ 99% processing success in demo runs; idempotent handlers.

* **Performance:** ingest ≥ 60 emails/min; end‑to‑end order cycle simulated in \< 5s wall time (non‑expedite).

* **Scalability:** horizontal scale of agents via queues; stateless services.

* **Testability:** unit \+ integration \+ end‑to‑end (replayable).

  ---

  ## **17\) Development & Deployment**

* **Repo Layout**

```
/agents
  /info /sales /production /logistics /finance /quality /support /purchasing /hr /mgmt
/services
  /mail-ingest /attachment-parser /policy-engine /orchestrator /history /kpi /dashboard
/config
  company.yaml
  usecases/info_mail_handling.yaml
  units/*.yaml
/sim
  /generators /history-seeder /day-script
/tests
  /unit /integration /e2e
```

*   
  **Runtime:** Docker; docker‑compose for local; K8s optional.

* **Env Vars:** MAIL\_IMAP\_HOST/PORT/USER/PASS, SMTP\_HOST/PORT/USER/PASS, GRAPH\_URI, QUEUE\_URI, METRICS\_URI.

  ---

  ## **18\) Testing & Acceptance Criteria**

  ### **18.1 Test Scenarios (selection)**

1. **Basic Triage:** order PDF → routed to orders@; invoice → finance@; unknown → support@.

2. **OEM Priority:** sender oem1.com → HIGH priority; planning before B2C.

3. **Expedite Offer:** email text “pay 4x” \+ “deliver in 24h” → priority=EXPEDITE; shipment scheduled within expedite window.

4. **Royal Replies:** all outbound replies contain greeting & signature.

5. **DDT Build:** after 1 day, Graph contains Mailboxes, Parties, Orders, Rules, Edges ≥ 95%.

6. **KPI Targets:** Auto‑Handled ≥ 70%, Avg Response ≤ 1h (sim time), On‑Time‑Ship ≥ 90%.

7. **Replay:** selected day replays identisch (same seeds).

   ### **18.2 Acceptance Criteria**

* All 18.1 pass; Dashboard live updates; Audit Trail shows decisions; Config changes hot‑reload or rolling restart.

  ---

  ## **19\) Risks & Mitigations**

* **MAS failure modes (role drift, weak verification):** enforce unit‑scoped roles, termination conditions, rule checks, audits.

* **Parsing fragility:** constrain PDF templates; include schema validation & friendly fallbacks.

* **Overfitting to script:** add controlled randomness toggles for more robust Observe‑proof.

  ---

  ## **20\) Roadmap**

* **v1 (this PRD):** info@, triage, E2E order happy path, dashboard MVP, history+replay.

* **v1.1:** DC optimization heuristics, production split, richer exceptions.

* **v1.2:** Cross‑Use‑Case comms; second UC (Distribution Center Optimization).

* **v2:** Replace stubs with real adapters; advanced verification agents.

  ---

  ## **21\) Appendix**

  ### **21.1 Royal Courtesy – Reply Template**

```
Subject: Most Gracious Acknowledgement of Your Message

Dear Sir or Madam,

We are most delighted to acknowledge receipt of your correspondence. Kindly note we shall attend to your request with the utmost care and expedience.

With the greatest pleasure,
Happy Buttons Service
```

  ### **21.2 Sample OEM Expedite Email (input)**

```
From: buyer@oem1.com
To: info@h-bu.de
Subject: URGENT – Delivery within 24h

We confirm we shall pay 4x the fee should you deliver within 24 hours. Please prioritise 10,000 white OEM buttons.
```

  ### **21.3 Sample Invoice PDF (fields)**

```
Invoice ID, Order ID, Bill To, Amount, VAT, Due Date, Payment Terms
```

  ### **21.4 Example Graph Nodes (min set)**

* Person/Party, Mailbox, Email, Attachment, Order, Invoice, Agent, Rule, Site, Event, Policy

  ### **21.5 Example Dashboard Tiles**

* Auto‑Handled %, Avg Response (h), Exceptions Today, OEM Share %, On‑Time‑Ship %

* 

