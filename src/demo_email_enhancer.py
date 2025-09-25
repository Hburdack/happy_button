#!/usr/bin/env python3
"""
Demo Email Enhancer
Enhances real emails with demo-friendly features while keeping authentic data
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid
from real_email_connector import RealEmailConnector

class DemoEmailEnhancer:
    """Enhances real emails with demo-friendly features"""

    def __init__(self):
        self.real_connector = RealEmailConnector("sim/config/company_release2.yaml")

        # Demo enhancement templates for different email types
        self.demo_enhancements = {
            'order': {
                'sample_content_additions': [
                    "\n\n📦 Order Details:\n- Quantity: {quantity} units\n- Value: €{value:,.2f}\n- Delivery: {delivery_date}",
                    "\n\n🎯 Business Priority: {priority_reason}\n- Customer Type: {customer_type}\n- SLA: {sla_hours} hours"
                ],
                'demo_customers': [
                    'BMW Manufacturing GmbH',
                    'Siemens Industrial',
                    'Volkswagen Parts Division',
                    'Mercedes-Benz Components',
                    'Bosch Engineering'
                ]
            },
            'support': {
                'sample_content_additions': [
                    "\n\n🔧 Support Ticket: #{ticket_id}\n- Issue Type: {issue_type}\n- Urgency: {urgency_level}",
                    "\n\n📊 Customer Impact: {impact_level}\n- Affected Users: {user_count}\n- Estimated Resolution: {resolution_time}"
                ],
                'issue_types': ['Installation Help', 'Quality Issue', 'Technical Question', 'Product Defect', 'Usage Guide']
            },
            'finance': {
                'sample_content_additions': [
                    "\n\n💰 Financial Details:\n- Invoice #: INV-{invoice_num}\n- Amount: €{amount:,.2f}\n- Due Date: {due_date}",
                    "\n\n📈 Payment Terms: {payment_terms}\n- Account Status: {account_status}\n- Credit Limit: €{credit_limit:,.2f}"
                ]
            },
            'inquiry': {
                'sample_content_additions': [
                    "\n\n📋 Inquiry Type: {inquiry_type}\n- Follow-up Required: {followup}\n- Expected Response: {response_time}",
                    "\n\n🏢 Company Profile:\n- Industry: {industry}\n- Size: {company_size}\n- Location: {location}"
                ]
            }
        }

        # Demo flow simulation states
        self.flow_states = [
            'received', 'parsed', 'classified', 'routed', 'assigned', 'processing', 'response_generated', 'sent', 'completed'
        ]

    def get_enhanced_emails_for_demo(self, limit=20, show_flow=True, add_demo_data=True) -> List[Dict[str, Any]]:
        """Get real emails enhanced with demo features"""

        # Start with real emails
        real_emails = self.real_connector.get_real_emails(limit=limit)
        enhanced_emails = []

        for email in real_emails:
            enhanced_email = email.copy()

            if add_demo_data:
                enhanced_email = self._add_demo_enhancements(enhanced_email)

            if show_flow:
                enhanced_email = self._add_flow_simulation(enhanced_email)

            enhanced_emails.append(enhanced_email)

        # Sort by timestamp for demo flow
        enhanced_emails.sort(key=lambda x: x.get('demo_timestamp', x['timestamp']), reverse=True)

        return enhanced_emails

    def _add_demo_enhancements(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """Add demo-friendly enhancements to real email"""

        email_type = email.get('type', 'inquiry')

        # Add demo metadata
        email['demo_enhanced'] = True
        email['demo_id'] = f"DEMO-{uuid.uuid4().hex[:8].upper()}"

        # Enhance content based on type
        if email_type in self.demo_enhancements:
            email = self._enhance_by_type(email, email_type)

        # Add processing metrics
        email['demo_metrics'] = {
            'processing_time_ms': random.randint(250, 1500),
            'confidence_score': random.uniform(0.85, 0.98),
            'automation_possible': random.choice([True, True, True, False]),  # 75% automation rate
            'estimated_value': random.randint(1000, 50000) if email_type == 'order' else 0
        }

        # Add agent assignment
        email['demo_agent'] = {
            'assigned_to': f"{email.get('mailbox', 'info').title()}Agent",
            'assignment_time': datetime.now() - timedelta(minutes=random.randint(5, 120)),
            'status': random.choice(['processing', 'completed', 'pending_review'])
        }

        return email

    def _enhance_by_type(self, email: Dict[str, Any], email_type: str) -> Dict[str, Any]:
        """Add type-specific demo enhancements"""

        enhancements = self.demo_enhancements[email_type]

        if email_type == 'order':
            # Add order-specific demo data
            demo_data = {
                'quantity': random.randint(100, 10000),
                'value': random.uniform(5000, 50000),
                'delivery_date': (datetime.now() + timedelta(days=random.randint(7, 30))).strftime('%Y-%m-%d'),
                'priority_reason': random.choice(['Large Order', 'OEM Customer', 'Urgent Request', 'New Customer']),
                'customer_type': random.choice(['OEM', 'Distributor', 'End User', 'Reseller']),
                'sla_hours': random.choice([2, 4, 12, 24])
            }

            # Enhance subject if it's generic
            if 'test' in email['subject'].lower() or len(email['subject']) < 20:
                customer = random.choice(enhancements['demo_customers'])
                email['subject'] = f"Order Request: {demo_data['quantity']} Premium Buttons - {customer}"

        elif email_type == 'support':
            demo_data = {
                'ticket_id': f"SUP-{random.randint(10000, 99999)}",
                'issue_type': random.choice(enhancements['issue_types']),
                'urgency_level': random.choice(['Low', 'Medium', 'High', 'Critical']),
                'impact_level': random.choice(['User', 'Department', 'Company', 'Critical']),
                'user_count': random.randint(1, 50),
                'resolution_time': f"{random.randint(1, 24)} hours"
            }

        elif email_type == 'finance':
            demo_data = {
                'invoice_num': random.randint(100000, 999999),
                'amount': random.uniform(1000, 25000),
                'due_date': (datetime.now() + timedelta(days=random.randint(7, 30))).strftime('%Y-%m-%d'),
                'payment_terms': random.choice(['Net 30', 'Net 15', 'Due on Receipt', 'Net 45']),
                'account_status': random.choice(['Good Standing', 'Current', 'Past Due']),
                'credit_limit': random.uniform(10000, 100000)
            }

        else:  # inquiry
            demo_data = {
                'inquiry_type': random.choice(['Product Info', 'Pricing', 'Technical Specs', 'Partnership', 'General']),
                'followup': random.choice(['Yes', 'No', 'Scheduled']),
                'response_time': random.choice(['2 hours', '24 hours', '48 hours']),
                'industry': random.choice(['Automotive', 'Electronics', 'Manufacturing', 'Textiles']),
                'company_size': random.choice(['Small (1-50)', 'Medium (51-200)', 'Large (200+)']),
                'location': random.choice(['Germany', 'Europe', 'North America', 'Asia'])
            }

        # Add demo enhancement to content
        if 'sample_content_additions' in enhancements and demo_data:
            addition_template = random.choice(enhancements['sample_content_additions'])
            demo_addition = addition_template.format(**demo_data)
            email['full_content'] = email.get('full_content', email['content']) + demo_addition
            email['content'] = email['full_content'][:500] + "..." if len(email['full_content']) > 500 else email['full_content']

        # Store demo data for reference
        email['demo_data'] = demo_data

        return email

    def _add_flow_simulation(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """Add email flow simulation for demo purposes"""

        # Simulate processing flow
        current_state_index = random.randint(3, len(self.flow_states) - 1)  # Most emails are processed
        email['demo_flow'] = {
            'current_state': self.flow_states[current_state_index],
            'completed_steps': self.flow_states[:current_state_index + 1],
            'next_steps': self.flow_states[current_state_index + 1:] if current_state_index < len(self.flow_states) - 1 else [],
            'progress_percentage': int((current_state_index + 1) / len(self.flow_states) * 100)
        }

        # Add timestamps for each flow step
        base_time = email['timestamp']
        email['demo_flow']['step_timestamps'] = {}

        for i, step in enumerate(email['demo_flow']['completed_steps']):
            step_time = base_time + timedelta(seconds=i * random.randint(30, 300))
            email['demo_flow']['step_timestamps'][step] = step_time

        # Add demo timestamp for sorting (slightly randomized for demo effect)
        email['demo_timestamp'] = base_time + timedelta(minutes=random.randint(-30, 30))

        return email

    def get_live_demo_stats(self) -> Dict[str, Any]:
        """Get enhanced statistics for demo purposes"""

        # Get real stats
        real_counts = self.real_connector.get_mailbox_counts()
        real_total = sum(real_counts.values())

        # Enhance with demo metrics
        demo_stats = {
            'real_email_counts': real_counts,
            'total_real_emails': real_total,
            'demo_metrics': {
                'emails_processed_today': real_total + random.randint(50, 200),
                'auto_response_rate': random.uniform(85, 95),
                'average_response_time': f"{random.uniform(0.5, 2.0):.1f} hours",
                'customer_satisfaction': random.uniform(92, 98),
                'agent_efficiency': random.uniform(88, 96),
                'sla_compliance': random.uniform(94, 99)
            },
            'flow_statistics': {
                'emails_in_processing': random.randint(2, 8),
                'completed_today': random.randint(15, 45),
                'pending_review': random.randint(0, 3),
                'auto_handled': random.randint(20, 35)
            },
            'business_impact': {
                'orders_generated': random.randint(5, 15),
                'estimated_revenue': random.randint(25000, 75000),
                'support_tickets_resolved': random.randint(8, 20),
                'customer_inquiries_handled': random.randint(15, 35)
            }
        }

        return demo_stats

if __name__ == "__main__":
    # Test the demo enhancer
    print("🎬 TESTING DEMO EMAIL ENHANCER")
    print("=" * 50)

    enhancer = DemoEmailEnhancer()

    # Test enhanced emails
    print("📧 ENHANCED REAL EMAILS FOR DEMO:")
    enhanced_emails = enhancer.get_enhanced_emails_for_demo(limit=5, show_flow=True, add_demo_data=True)

    print(f"   Retrieved {len(enhanced_emails)} enhanced real emails")

    for i, email in enumerate(enhanced_emails[:3]):
        print(f"\n   📨 Enhanced Email {i+1}:")
        print(f"      From: {email['from']}")
        print(f"      Subject: {email['subject'][:60]}...")
        print(f"      Demo ID: {email.get('demo_id', 'N/A')}")
        print(f"      Flow State: {email.get('demo_flow', {}).get('current_state', 'N/A')}")
        print(f"      Progress: {email.get('demo_flow', {}).get('progress_percentage', 0)}%")
        print(f"      Processing Time: {email.get('demo_metrics', {}).get('processing_time_ms', 0)}ms")
        if 'demo_data' in email:
            print(f"      Demo Enhancement: ✅ Applied")

    # Test demo stats
    print(f"\n📊 DEMO STATISTICS:")
    stats = enhancer.get_live_demo_stats()
    print(f"   Real Emails: {stats['total_real_emails']}")
    print(f"   Demo Enhanced: {stats['demo_metrics']['emails_processed_today']}")
    print(f"   Auto Response Rate: {stats['demo_metrics']['auto_response_rate']:.1f}%")
    print(f"   SLA Compliance: {stats['demo_metrics']['sla_compliance']:.1f}%")

    print(f"\n✅ Demo enhancer working - real emails with demo appeal!")