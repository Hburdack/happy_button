# Scenario Email Integration Guide

## Overview

The scenario email integration system automatically generates realistic email files when scenarios run, making scenario effects visible in the email system interfaces. This addresses the user concern "i dont see scenario email please check" by creating actual emails that appear in the Happy Buttons email system.

## How It Works

### 1. **Automatic Email Generation**
When scenarios execute, they now automatically:
- Generate realistic customer emails based on scenario events
- Save emails as JSON files in `data/scenario_emails/`
- Include detailed business impact and urgency information
- Map scenario events to appropriate email types

### 2. **Email Types Generated**

| Scenario | Email Types | When Generated |
|----------|-------------|----------------|
| **Late Triage** | `customer_inquiry`, `complaint` | When email processing is delayed beyond SLA |
| **Missed Expedite** | `expedite_request` | When high-profit expedite opportunities are missed |
| **VIP Handling** | `vip_request` | When VIP customers experience service issues |
| **Global Disruption** | `customer_inquiry`, `complaint` | When supply chain delays affect orders |

### 3. **Email Content Features**

✅ **Realistic Content**: Authentic business language and scenarios
✅ **Customer Data**: Real company names, contact info, order details
✅ **Urgency Levels**: Calculated based on delay severity and impact
✅ **Business Impact**: Revenue loss, satisfaction impact, escalation risk
✅ **SLA Tracking**: Violation detection and compliance metrics

## Generated Email Structure

```json
{
  "id": "unique-email-id",
  "scenario_type": "late_triage",
  "email_type": "complaint",
  "timestamp": "2025-09-27T08:33:23.181382",
  "from": "customer@company.com",
  "to": "support@happybuttons.de",
  "subject": "Formal Complaint: Poor Customer Service Response",
  "body": "Email content with specific delay details...",
  "delay_info": {
    "delay_minutes": 183,
    "sla_minutes": 30,
    "customer_impact": "severe",
    "escalation_triggered": true
  },
  "customer_info": {
    "name": "Customer Name",
    "company": "Company Name",
    "phone": "+XX-XX-XXXXXXXX"
  },
  "urgency": "high",
  "business_impact": {
    "customer_satisfaction_loss": 36.6,
    "potential_revenue_loss": 0,
    "reputation_damage": 36.6,
    "escalation_risk": 82.35
  },
  "sla_violation": true
}
```

## Integration Points

### 1. **Scenario Files Modified**
- `src/scenarios/late_triage.py` - Added email generation for delays
- `src/scenarios/missed_expedite.py` - Added email generation for missed opportunities
- `src/scenarios/vip_handling.py` - Added email generation for VIP incidents
- `src/scenarios/global_disruption.py` - Added email generation for affected orders

### 2. **Email Generator**
- `src/scenarios/email_generator.py` - Core email generation logic
- Realistic templates for each scenario type
- Customer database with authentic business contacts
- Business impact calculation algorithms

### 3. **File Storage**
- **Location**: `data/scenario_emails/`
- **Format**: JSON files with descriptive names
- **Naming**: `scenario_{type}_{email_type}_{timestamp}.json`
- **Retention**: Automatic cleanup of old emails (configurable)

## Viewing Generated Emails

### 1. **File System**
```bash
# List generated emails
ls -la data/scenario_emails/

# View latest emails
ls -lt data/scenario_emails/ | head -5

# Count emails by type
ls data/scenario_emails/ | grep "late_triage" | wc -l
```

### 2. **Email System Integration**
The generated emails are saved as files that can be:
- Read by email processing systems
- Displayed in email interfaces
- Processed by agents and workflows
- Analyzed for metrics and reporting

### 3. **Real-time Monitoring**
```bash
# Watch for new emails being created
watch -n 1 'ls -lt data/scenario_emails/ | head -5'

# Monitor scenario logs
tail -f logs/happy_buttons.log | grep "Generated scenario email"
```

## Testing the Integration

### Quick Test
```bash
# Run the integration test script
python test_scenario_email_integration.py
```

### Manual Testing
1. **Start a scenario** from the dashboard
2. **Wait 10-30 seconds** for emails to be generated
3. **Check the email directory**: `ls data/scenario_emails/`
4. **View email content**: `cat data/scenario_emails/scenario_*.json`

## Email Examples

### Late Triage Complaint
```
Subject: "COMPLAINT: 3.0 Hour Delay in Response Time"
From: "Industrial Solutions AG"
Content: Formal complaint about unacceptable response delays
Urgency: High (3+ hour delay)
Impact: Customer satisfaction loss, reputation damage
```

### Missed Expedite Request
```
Subject: "URGENT EXPEDITE: Rush Order Required - Premium Payment Ready"
From: "Precision Components Ltd"
Content: High-value expedite request with premium payment offer
Urgency: Critical (missed opportunity)
Impact: €29,692 potential revenue loss
```

### VIP Service Issue
```
Subject: "VIP Account: Custom Order Requirement - Premium Client"
From: "Royal Palace Procurement"
Content: VIP customer requiring special attention
Urgency: Critical (VIP tier customer)
Impact: Relationship damage, media attention risk
```

## Configuration

### Email Generation Settings
The email generator can be configured via the scenario configurations:

```yaml
# In scenario config files
email_generation:
  enabled: true
  save_to_filesystem: true
  cleanup_days: 7
  realistic_delays: true
  business_impact_calculation: true
```

### Template Customization
Email templates can be customized in `src/scenarios/email_generator.py`:

```python
# Add new templates
self.email_templates['new_scenario'] = {
    'email_type': {
        'subject_templates': [...],
        'body_templates': [...]
    }
}
```

## Troubleshooting

### No Emails Generated
1. **Check scenario execution**: Verify scenarios are actually running
2. **Check directory permissions**: Ensure `data/scenario_emails/` is writable
3. **Check logs**: Look for email generation errors in logs
4. **Run test script**: `python test_scenario_email_integration.py`

### Invalid Email Format
1. **Check JSON syntax**: Validate email files with `python -m json.tool filename.json`
2. **Check template variables**: Ensure all template variables are properly defined
3. **Check character encoding**: Files should be UTF-8 encoded

### Missing Email Types
1. **Check scenario mapping**: Verify email type mapping in scenario files
2. **Check templates**: Ensure templates exist for the scenario type
3. **Check configuration**: Verify scenario email generation is enabled

## Performance Impact

- **Minimal CPU overhead**: Email generation is asynchronous
- **Small storage impact**: ~1-2KB per email file
- **No network impact**: Files are saved locally
- **Auto-cleanup**: Old emails are automatically removed

## Benefits

✅ **Visible Scenario Effects**: Users can now see emails generated by scenarios
✅ **Realistic Business Impact**: Emails show authentic customer frustration
✅ **Integration Testing**: Email system can be tested with scenario data
✅ **Metrics Tracking**: Email generation contributes to KPI calculations
✅ **User Experience**: Clear evidence that scenarios are working

## Next Steps

1. **Monitor email generation** during scenario runs
2. **Integrate with email processing agents** for automatic responses
3. **Add email metrics** to dashboard displays
4. **Customize templates** for specific business needs
5. **Configure email cleanup** policies as needed

---

*This integration ensures that when users run scenarios, they will immediately see realistic emails appear in their email system, providing clear evidence of scenario effects and enabling comprehensive testing of email-based business processes.*