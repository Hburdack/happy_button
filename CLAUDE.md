# Happy Buttons Agentic Simulation System - Claude Code Configuration

## Project Overview

This project implements an **Agentic Simulation System** for Happy Buttons GmbH, enabling automated email processing, customer service, and business process simulation through AI agents.

### Business Context
- **Company**: Happy Buttons GmbH (h-bu.de)
- **Culture**: Royal English courtesy style
- **Core Business**: Button manufacturing with global supply chain
- **Target KPIs**:
  - Auto-handled share ≥ 70%
  - Average response ≤ 1h
  - On-time ship ≥ 90%

## Architecture

### Business Units & Mailboxes
```yaml
Mailboxes:
- info@h-bu.de (main entry point)
- orders@h-bu.de (order processing)
- oem1@h-bu.de (OEM customers)
- supplier@h-bu.de (supply chain)
- logistics@h-bu.de (shipping/receiving)
- support@h-bu.de (customer support)
- hr@h-bu.de (human resources)
- finance@h-bu.de (invoicing/payments)
- quality@h-bu.de (quality control)
- management@h-bu.de (escalations)
```

### Production & Distribution Sites
- **Production**: CN, PL, MX, MD
- **Distribution**: NY, MD

### Systems Integration
- **ERP**: Stub implementation
- **CRM**: Stub implementation
- **WMS**: Stub implementation

## Email Processing Rules

### Triage Rules (info@h-bu.de)
```yaml
- order_pdf → orders@h-bu.de
- invoice_pdf → finance@h-bu.de
- supplier_keywords → supplier@h-bu.de
- complaint_keywords → quality@h-bu.de
- else → support@h-bu.de
```

### Priority System
- **OEM customers** (oem1.com) get priority
- **Escalation**: Ambiguous cases → management@h-bu.de
- **SLA**: Default response within 12 hours, expedite within 24 hours

### Autoreply Templates (Royal Style)
- Order received: "We are most delighted to confirm receipt of your order..."
- Generic ack: "Kindly note we have received your message and shall revert most promptly."
- Invoice received: "We gratefully acknowledge your invoice and shall process it forthwith."
- Expedite ack: "We are honoured to prioritise your request and shall strive for delivery within 24 hours."

## Development Commands

### Core Development
```bash
# Start development
npm run dev

# Build project
npm run build

# Run tests
npm run test

# Generate sample documents
python pdf_generator.py --type order --seed 123 --out samples/order_123.pdf
python pdf_generator.py --type invoice --seed 456 --out samples/invoice_456.pdf
```

### Claude Flow Commands
```bash
# Initialize swarm for email processing
npx claude-flow@alpha swarm "email processing simulation" --claude

# Initialize business unit agents
npx claude-flow@alpha hive-mind spawn "business units coordination" --claude

# SPARC development workflow
npx claude-flow sparc tdd "email automation feature"
```

## Agent Configuration

### Business Unit Agents
- **Info Agent**: Main email triage and routing
- **Orders Agent**: Order processing and confirmation
- **OEM Agent**: Premium customer handling
- **Supplier Agent**: Supply chain coordination
- **Logistics Agent**: Shipping and receiving
- **Support Agent**: Customer service
- **Finance Agent**: Invoice and payment processing
- **Quality Agent**: Complaint handling and QC
- **Management Agent**: Escalation and oversight

### Simulation Agents
- **Email Generator**: Creates realistic test emails
- **PDF Generator**: Creates order/invoice attachments
- **Performance Monitor**: Tracks KPIs and metrics
- **Royal Courtesy**: Ensures proper communication style

## File Structure

```
/home/pi/happy_button/
├── config/
│   ├── company.yaml              # Global company configuration
│   └── units/*.yaml             # Business unit configurations
├── src/
│   ├── agents/                  # Business unit agent implementations
│   ├── email/                   # Email processing logic
│   ├── simulation/              # Simulation engine
│   └── utils/                   # Utility functions
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── simulation/              # Simulation tests
├── templates/
│   └── replies/*.txt            # Royal courtesy templates
├── samples/                     # Generated sample documents
└── docs/                       # Documentation
```

## Development Workflow

### 1. Email Processing Development
```bash
# Start with email agent development
npx claude-flow sparc run spec-pseudocode "email triage system"
npx claude-flow sparc run architect "multi-agent email processing"
npx claude-flow sparc tdd "email routing functionality"
```

### 2. Business Unit Integration
```bash
# Develop business unit agents
npx claude-flow@alpha swarm "implement business unit agents" --claude
```

### 3. Simulation System
```bash
# Build simulation engine
npx claude-flow sparc pipeline "email simulation system"
```

## Testing Strategy

### Unit Tests
- Email parsing and routing logic
- Business rule validation
- Template rendering
- PDF generation

### Integration Tests
- End-to-end email processing
- Multi-agent coordination
- System integration points

### Simulation Tests
- Performance under load
- KPI achievement validation
- Royal courtesy compliance

## Monitoring & KPIs

### Key Metrics
- **Auto-handled Share**: Target ≥ 70%
- **Response Time**: Target ≤ 1 hour average
- **Escalation Rate**: Track management escalations
- **Customer Satisfaction**: Based on response quality

### Performance Tracking
```bash
# Monitor simulation performance
npx claude-flow@alpha swarm_monitor --metrics

# Check agent performance
npx claude-flow@alpha agent_metrics --unit all
```

## Deployment Configuration

### Environment Variables
```bash
# Email server configuration
IMAP_HOST=mail.h-bu.de
SMTP_HOST=mail.h-bu.de
COMPANY_DOMAIN=h-bu.de

# Database configuration
DATABASE_URL=sqlite:./simulation.db

# API endpoints (stub implementations)
ERP_ENDPOINT=http://localhost:3001/erp
CRM_ENDPOINT=http://localhost:3002/crm
WMS_ENDPOINT=http://localhost:3003/wms
```

### Docker Setup
```bash
# Build and run simulation
docker-compose up --build

# Scale agents
docker-compose scale email-agent=3 orders-agent=2
```

## Security & Compliance

### Data Protection
- No hardcoded credentials
- Secure email server connections
- Customer data anonymization in tests

### Royal Courtesy Compliance
- All communications must follow template standards
- Escalation procedures for ambiguous cases
- Quality assurance on automated responses

## Troubleshooting

### Common Issues
1. **Email routing failures**: Check triage rules in config
2. **Template rendering errors**: Validate royal courtesy templates
3. **Performance issues**: Monitor agent coordination overhead
4. **Integration failures**: Verify stub system responses

### Debug Commands
```bash
# Check swarm status
npx claude-flow@alpha swarm_status

# Validate configuration
python -m yaml config/company.yaml

# Test PDF generation
python pdf_generator.py --test
```

## Next Steps

1. **Phase 1**: Implement core email processing
2. **Phase 2**: Add business unit agents
3. **Phase 3**: Build simulation engine
4. **Phase 4**: Performance optimization
5. **Phase 5**: Production deployment

---

**Remember**: Maintain Royal English courtesy in all automated communications!