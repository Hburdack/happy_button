"""
Scenario Email Generator for Release 3.0
Generates visible scenario emails that integrate with existing email system
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ScenarioEmailGenerator:
    """Generate scenario emails that integrate with existing email system"""

    def __init__(self):
        self.scenario_emails_dir = Path("data/scenario_emails")
        self.scenario_emails_dir.mkdir(parents=True, exist_ok=True)

        # Email templates for different scenarios
        self.email_templates = {
            'late_triage': {
                'customer_inquiry': {
                    'subject_templates': [
                        "Urgent: Order Status Update Required - Order #{order_id}",
                        "Delayed Response Needed: Product Information Request",
                        "ASAP: Customer Service Response Required",
                        "Time-Sensitive: Order Confirmation Needed #{order_id}"
                    ],
                    'body_templates': [
                        "Dear Happy Buttons Support,\n\nI sent an inquiry about my order #{order_id} {delay_hours} hours ago but haven't received any response. This is affecting my production schedule. Please respond urgently.\n\nBest regards,\n{customer_name}\n{company_name}",
                        "Hello,\n\nI've been waiting for {delay_hours} hours for someone to respond to my simple question about button specifications. This delay is very unprofessional.\n\nPlease prioritize customer service.\n\n{customer_name}",
                        "URGENT: I need immediate assistance with order #{order_id}. It's been {delay_hours} hours since my first email. This delay is costing my business money.\n\nExpecting immediate response,\n{customer_name}"
                    ]
                },
                'complaint': {
                    'subject_templates': [
                        "COMPLAINT: {delay_hours} Hour Delay in Response Time",
                        "Unacceptable Service - {delay_hours} Hours Without Reply",
                        "Formal Complaint: Poor Customer Service Response",
                        "Escalation Required: No Response for {delay_hours} Hours"
                    ],
                    'body_templates': [
                        "To Management,\n\nThis is a formal complaint about your company's poor response times. I have been waiting {delay_hours} hours for a simple response.\n\nI expect immediate action and an explanation for this delay.\n\n{customer_name}\nPurchasing Manager\n{company_name}",
                        "I am extremely disappointed with Happy Buttons' customer service. {delay_hours} hours without any acknowledgment is completely unacceptable in today's business environment.\n\nI'm considering switching suppliers if this continues.\n\n{customer_name}",
                        "ESCALATION NOTICE:\n\nYour team has failed to respond to my inquiry for {delay_hours} hours. This is affecting my business operations and I demand immediate action.\n\nIf I don't hear back within the next hour, I will be escalating this to your management and reconsidering our business relationship.\n\n{customer_name}\n{company_name}"
                    ]
                }
            },
            'missed_expedite': {
                'expedite_request': {
                    'subject_templates': [
                        "URGENT EXPEDITE: Rush Order Required - Premium Payment Ready",
                        "EXPEDITE REQUEST: Willing to Pay 200% Premium for Rush Delivery",
                        "TIME CRITICAL: Expedite Service Needed ASAP",
                        "RUSH ORDER: Premium Expedite Payment Approved"
                    ],
                    'body_templates': [
                        "URGENT EXPEDITE REQUEST\n\nWe need 50,000 units rushed for production line emergency. Willing to pay 200% premium for 48-hour delivery.\n\nOrder value: €25,000 + €50,000 expedite fee = €75,000 total\n\nPlease confirm immediately.\n\n{customer_name}\nProduction Manager\n{company_name}",
                        "Emergency production shortage requires immediate expedite service. We can pay premium rates for rush delivery.\n\nQuantity: {quantity} units\nStandard value: €{standard_value}\nWilling to pay: €{expedite_value} (200% premium)\n\nTime sensitive - please respond ASAP.\n\n{customer_name}",
                        "RUSH ORDER AUTHORIZATION\n\nOur production line is down waiting for buttons. CEO has authorized unlimited expedite budget.\n\nWe need {quantity} units delivered within 24-48 hours. Money is no object.\n\nPlease call me immediately at {phone}.\n\n{customer_name}\nOperations Director"
                    ]
                }
            },
            'vip_handling': {
                'vip_request': {
                    'subject_templates': [
                        "VIP Account: Custom Order Requirement - {company_name}",
                        "Premium Client: Urgent Custom Specification Request",
                        "VIP Service: Time-Sensitive Custom Order",
                        "Priority Account: Special Requirements for Major Order"
                    ],
                    'body_templates': [
                        "Dear Happy Buttons VIP Team,\n\nAs one of your largest customers (€500k+ annually), I need special attention for this custom order.\n\nRequirements:\n- Custom color matching\n- Special packaging\n- Dedicated quality inspection\n- Express shipping\n\nThis is for our flagship product launch. Please assign your best team.\n\n{customer_name}\nCEO, {company_name}",
                        "VIP ACCOUNT REQUEST\n\nWe're your top-tier customer requiring white-glove service for this order. Our annual volume justifies premium treatment.\n\nCustom specifications attached. This order is critical for our Q4 product launch affecting $2M in revenue.\n\nPlease prioritize accordingly.\n\n{customer_name}\nChief Procurement Officer",
                        "As a premium account holder, I expect VIP handling for all requests. This order requires special attention due to its strategic importance.\n\nPlease ensure:\n- Direct communication with senior management\n- Priority production scheduling\n- Premium quality assurance\n- Expedited shipping\n\n{customer_name}\n{company_name}"
                    ]
                }
            }
        }

        # Customer database for realistic names and companies
        self.customers = [
            {"name": "Sarah Mitchell", "company": "TechFlow Manufacturing", "phone": "+49-30-12345678"},
            {"name": "Robert Chen", "company": "Alpine Electronics GmbH", "phone": "+49-89-87654321"},
            {"name": "Maria Rodriguez", "company": "Precision Components Ltd", "phone": "+33-1-55443322"},
            {"name": "James Wilson", "company": "Industrial Solutions AG", "phone": "+41-44-7766554"},
            {"name": "Anna Kowalski", "company": "European Manufacturing Co", "phone": "+48-22-9988776"},
            {"name": "David Thompson", "company": "Premium Electronics", "phone": "+44-20-11223344"},
            {"name": "Lisa Andersson", "company": "Nordic Industries AB", "phone": "+46-8-44556677"},
            {"name": "Marco Rossi", "company": "Italian Design House", "phone": "+39-02-33445566"}
        ]

    def generate_scenario_email(self, scenario_type: str, email_type: str, delay_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a scenario email with realistic content"""

        if scenario_type not in self.email_templates:
            logger.warning(f"No templates for scenario type: {scenario_type}")
            return None

        if email_type not in self.email_templates[scenario_type]:
            logger.warning(f"No templates for email type: {email_type} in scenario {scenario_type}")
            return None

        template_set = self.email_templates[scenario_type][email_type]

        # Select random customer and templates
        import random
        customer = random.choice(self.customers)
        subject_template = random.choice(template_set['subject_templates'])
        body_template = random.choice(template_set['body_templates'])

        # Calculate delay information
        delay_minutes = delay_info.get('delay_minutes', 0)
        delay_hours = round(delay_minutes / 60, 1)

        # Generate realistic order data
        order_id = f"HB-{random.randint(100000, 999999)}"
        quantity = random.randint(1000, 100000)
        standard_value = quantity * random.uniform(0.15, 0.75)
        expedite_value = standard_value * 3  # 200% premium

        # Template variables
        template_vars = {
            'customer_name': customer['name'],
            'company_name': customer['company'],
            'phone': customer['phone'],
            'delay_hours': delay_hours,
            'delay_minutes': delay_minutes,
            'order_id': order_id,
            'quantity': f"{quantity:,}",
            'standard_value': f"{standard_value:,.0f}",
            'expedite_value': f"{expedite_value:,.0f}"
        }

        # Format templates
        try:
            subject = subject_template.format(**template_vars)
            body = body_template.format(**template_vars)
        except KeyError as e:
            logger.error(f"Template formatting error: {e}")
            return None

        # Create email object
        email = {
            'id': str(uuid.uuid4()),
            'scenario_type': scenario_type,
            'email_type': email_type,
            'timestamp': datetime.now().isoformat(),
            'delayed_timestamp': (datetime.now() - timedelta(minutes=delay_minutes)).isoformat(),
            'from': f"{customer['name']} <{customer['name'].lower().replace(' ', '.')}@{customer['company'].lower().replace(' ', '').replace(',', '').replace('.', '')}de>",
            'to': "support@happybuttons.de",
            'subject': subject,
            'body': body,
            'delay_info': delay_info,
            'customer_info': customer,
            'urgency': self._calculate_urgency(delay_minutes, email_type),
            'business_impact': self._calculate_business_impact(delay_minutes, email_type, template_vars),
            'sla_violation': delay_minutes > delay_info.get('sla_minutes', 60)
        }

        return email

    def _calculate_urgency(self, delay_minutes: int, email_type: str) -> str:
        """Calculate email urgency based on delay and type"""
        if email_type == 'complaint' and delay_minutes > 240:  # 4+ hours
            return 'critical'
        elif email_type == 'expedite_request' and delay_minutes > 60:  # 1+ hour
            return 'critical'
        elif delay_minutes > 180:  # 3+ hours
            return 'high'
        elif delay_minutes > 60:  # 1+ hour
            return 'medium'
        else:
            return 'low'

    def _calculate_business_impact(self, delay_minutes: int, email_type: str, template_vars: Dict) -> Dict[str, Any]:
        """Calculate business impact of the delayed email"""

        base_impact = {
            'customer_satisfaction_loss': min(50, delay_minutes * 0.2),
            'potential_revenue_loss': 0,
            'reputation_damage': min(30, delay_minutes * 0.1),
            'escalation_risk': min(90, delay_minutes * 0.3)
        }

        # Adjust based on email type
        if email_type == 'expedite_request':
            expedite_value = float(template_vars.get('expedite_value', '0').replace(',', ''))
            base_impact['potential_revenue_loss'] = expedite_value * min(1.0, delay_minutes / 120)

        elif email_type == 'complaint':
            base_impact['reputation_damage'] *= 2
            base_impact['escalation_risk'] *= 1.5

        elif email_type == 'vip_request':
            base_impact['customer_satisfaction_loss'] *= 3
            base_impact['reputation_damage'] *= 2

        return base_impact

    def save_scenario_email(self, email: Dict[str, Any]) -> str:
        """Save scenario email to file system for integration with email interfaces"""

        if not email:
            return None

        # Create filename
        timestamp = email['timestamp'].replace(':', '-').replace('.', '-')
        filename = f"scenario_{email['scenario_type']}_{email['email_type']}_{timestamp}.json"
        filepath = self.scenario_emails_dir / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(email, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved scenario email: {filename}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error saving scenario email: {e}")
            return None

    def get_scenario_emails(self, scenario_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get scenario emails for display in email interfaces"""

        emails = []

        try:
            for email_file in sorted(self.scenario_emails_dir.glob("*.json"),
                                   key=lambda x: x.stat().st_mtime, reverse=True):

                if len(emails) >= limit:
                    break

                try:
                    with open(email_file, 'r', encoding='utf-8') as f:
                        email = json.load(f)

                    # Filter by scenario type if specified
                    if scenario_type and email.get('scenario_type') != scenario_type:
                        continue

                    emails.append(email)

                except Exception as e:
                    logger.error(f"Error reading email file {email_file}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error listing scenario emails: {e}")

        return emails

    def clean_old_emails(self, days_old: int = 7):
        """Clean up old scenario emails"""

        cutoff_date = datetime.now() - timedelta(days=days_old)

        try:
            for email_file in self.scenario_emails_dir.glob("*.json"):
                if email_file.stat().st_mtime < cutoff_date.timestamp():
                    email_file.unlink()
                    logger.info(f"Cleaned up old scenario email: {email_file.name}")

        except Exception as e:
            logger.error(f"Error cleaning old emails: {e}")

# Global instance
scenario_email_generator = ScenarioEmailGenerator()