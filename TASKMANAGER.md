# Taskmanager — Happy Buttons Simulation (Releases 2–5)

## Struktur
- **R2** Classic Company Simulation (no Zetify)
- **R3** Weakness Injection (classic org)
- **R4** Zetify Observe & DDT
- **R5** Zetify Automation on info@ + KPI Uplift

---

## R2 — Classic Company Simulation
**Goals:** Email → Order → Production → Logistics → Delivery → Invoice; Dashboard + History.

**Tasks**
- [ ] IMAP/SMTP Ingest (info@, finance@) → extend to 10 mailboxes  
- [ ] PDF Parser (order/invoice) → JSON schema + tests  
- [ ] Order state machine service + events  
- [ ] Unit agents wired (Info, Sales, Production, Logistics, Finance, Quality, Support, Purchasing, HR, Mgmt)  
- [ ] Dashboard MVP (flows + KPI tiles)  
- [ ] History seeder + repeatable day script  

**Acceptance**
- [ ] E2E happy path visible; replay deterministic

---

## R3 — Weakness Injection
**Scenarios**
- [ ] Late triage (info@)  
- [ ] Missed expedite (24h for 10× profit)  
- [ ] VIP Royal Blue request ignored  
- [ ] Global disruption (Suez)  

**Acceptance**
- [ ] KPI degradation visible + incident notes

---

## R4 — Zetify Observe & DDT
**Tasks**
- [ ] Graph adapter + KG schema  
- [ ] Event→Graph ingestion  
- [ ] DDT coverage tile + pattern mining  

**Acceptance**
- [ ] ≥95% coverage after 1 replayed day

---

## R5 — Zetify Automation on info@ 
**Tasks**
- [ ] Zetify Agent Creator runtime for info@  
- [ ] Policy-as-Code (courtesy, priority, escalation, SLA)  
- [ ] Scoreboard “Before/After Zetify”  

**Acceptance**
- [ ] Auto-handled ≥70%, Avg resp ≤1h; scenarios resolved

---

## Anhänge & Artefakte
- PRD v2: `docs/HappyButtons_Agentic_Simulation_PRD_v2.md`  
- Configs & Templates: `sim/config`, `sim/templates`  
- Generators & Samples: `sim/generators`, `sim/samples`
