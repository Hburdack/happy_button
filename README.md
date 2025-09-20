# Happy Buttons – Agentic Simulation Starter

This folder contains production-ready configuration files and templates for the Happy Buttons simulation.

## Structure
- config/company.yaml — global company configuration (culture, SLAs, mailboxes, sites, systems)
- config/units/*.yaml — one UnitConfig per business unit/agent (info, sales, production, logistics, finance, quality, support, purchasing, hr, mgmt)
- config/usecases/info_mail_handling.yaml — rules and simulation script for the info@ use case
- templates/replies/*.txt — Royal Courtesy reply templates
- generators/pdf_generator.py — PDF generator for Order/Invoice attachments (uses reportlab)

## Quick Start
1) Edit company and unit configs as needed.
2) Generate sample PDFs:
   ```
   python generators/pdf_generator.py --type order --seed 123 --out samples/order_123.pdf
   python generators/pdf_generator.py --type invoice --seed 456 --out samples/invoice_456.pdf
   ```
3) Plug IMAP/SMTP credentials into your runtime and point the system to these configs.

## KPIs / Targets
- Auto-handled share ≥ 70%
- Average response ≤ 1h
- On-time ship ≥ 90% (sim)
