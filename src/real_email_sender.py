#!/usr/bin/env python3
"""
Real Email Sender for Happy Buttons
Sends actual emails to the mailbox during simulations
"""

import smtplib
import time
import logging
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import yaml
import threading
from queue import Queue
import os

logger = logging.getLogger(__name__)

class RealEmailSender:
    """Sends real emails to mailboxes during simulations"""

    def __init__(self, config_path: str = "config/email_settings.yaml"):
        self.config_path = config_path
        self.config = self._load_config()

        # SMTP configuration from working send_test_email.py
        self.smtp_config = {
            'server': '192.168.2.13',  # mail.h-bu.de resolves to this
            'port': 587,
            'username': 'info@h-bu.de',
            'password': 'Adrian1234&',
            'use_starttls': True
        }

        # Email queue for batch sending
        self.email_queue = Queue()
        self.sender_thread = None
        self.is_running = False

        # Rate limiting - reduced for mail server limits
        self.max_emails_per_minute = 5  # Reduced from 10 to 5
        self.max_emails_per_hour = 30   # Added hourly limit
        self.last_send_times = []
        self.hourly_send_times = []

        # Statistics
        self.emails_sent = 0
        self.errors_count = 0

        logger.info("Real Email Sender initialized")

    def _load_config(self) -> dict:
        """Load email configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load config {self.config_path}: {e}")
            return {}

    def start_service(self):
        """Start the email sending service"""
        if self.is_running:
            return

        self.is_running = True
        self.sender_thread = threading.Thread(target=self._sender_loop, daemon=True)
        self.sender_thread.start()

        logger.info("✅ Real Email Sender service started")

    def stop_service(self):
        """Stop the email sending service"""
        self.is_running = False
        if self.sender_thread:
            self.sender_thread.join(timeout=5)
        logger.info("🛑 Real Email Sender service stopped")

    def queue_email(self, sender_email: str, subject: str, body: str,
                   recipient: str = "info@h-bu.de", priority: str = "normal") -> bool:
        """Queue an email for sending"""
        try:
            email_data = {
                'from': sender_email,
                'to': recipient,
                'subject': subject,
                'body': body,
                'priority': priority,
                'queued_at': time.time(),
                'id': f"email_{int(time.time())}_{random.randint(1000, 9999)}"
            }

            # Add priority ordering
            priority_order = {'critical': 0, 'high': 1, 'normal': 2, 'low': 3}
            priority_value = priority_order.get(priority, 2)

            self.email_queue.put((priority_value, email_data))

            logger.debug(f"📧 Email queued: {subject[:50]}... from {sender_email}")
            return True

        except Exception as e:
            logger.error(f"Error queueing email: {e}")
            return False

    def _sender_loop(self):
        """Background thread that sends queued emails"""
        while self.is_running:
            try:
                if self.email_queue.empty():
                    time.sleep(1)
                    continue

                # Check rate limiting
                if not self._can_send_email():
                    time.sleep(2)
                    continue

                # Get next email (priority queue)
                priority_value, email_data = self.email_queue.get()

                # Send the email
                success = self._send_single_email(email_data)

                if success:
                    self.emails_sent += 1
                    logger.info(f"✅ Email sent: {email_data['subject'][:50]}...")
                else:
                    self.errors_count += 1
                    logger.warning(f"❌ Failed to send: {email_data['subject'][:50]}...")

                # Small delay between emails
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error in sender loop: {e}")
                time.sleep(2)

    def _can_send_email(self) -> bool:
        """Check rate limiting for both minute and hour limits"""
        current_time = time.time()

        # Remove old timestamps (minute limit)
        self.last_send_times = [t for t in self.last_send_times if current_time - t < 60]

        # Remove old timestamps (hour limit)
        self.hourly_send_times = [t for t in self.hourly_send_times if current_time - t < 3600]

        # Check both minute and hour limits
        minute_ok = len(self.last_send_times) < self.max_emails_per_minute
        hour_ok = len(self.hourly_send_times) < self.max_emails_per_hour

        return minute_ok and hour_ok

    def _send_single_email(self, email_data: Dict[str, Any]) -> bool:
        """Send a single email via SMTP"""
        try:
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = email_data['from']
            msg['To'] = email_data['to']
            msg['Subject'] = email_data['subject']

            # Add timestamp to body for tracking
            timestamp_info = f"\\n\\n---\\nGenerated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\nSimulation: Happy Buttons TimeWarp\\nEmail ID: {email_data['id']}"
            body_with_timestamp = email_data['body'] + timestamp_info

            msg.attach(MIMEText(body_with_timestamp, 'plain'))

            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port'])

            if self.smtp_config.get('use_starttls'):
                server.starttls()

            server.login(self.smtp_config['username'], self.smtp_config['password'])

            # Send email
            text = msg.as_string()
            server.sendmail(email_data['from'], email_data['to'], text)
            server.quit()

            # Record send time for rate limiting
            current_time = time.time()
            self.last_send_times.append(current_time)
            self.hourly_send_times.append(current_time)

            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def send_simulation_email(self, email_type: str, sender_info: Dict[str, str],
                             variables: Dict[str, Any] = None) -> bool:
        """Send a simulation email based on type"""
        if variables is None:
            variables = {}

        # Email templates for different business scenarios
        templates = {
            "customer_inquiry": {
                "subject": "Button inquiry for {project_type} project - Order #{order_id}",
                "body": """Dear Happy Buttons Team,

We are working on a {project_type} project and need custom buttons.

Requirements:
- Quantity: {quantity} units
- Specifications: {specifications}
- Delivery date: {delivery_date}

Could you please provide specifications and pricing for this order?

Best regards,
{sender_name}
{company_name}"""
            },

            "oem_order": {
                "subject": "URGENT: {customer_name} Project Button Order - Priority",
                "body": """Dear Happy Buttons Team,

We have an urgent requirement for our {customer_name} project. Please prioritize this order:

- Quantity: {quantity} units
- Specifications: Automotive grade, {specifications}
- Delivery: ASAP - Required by {delivery_date}
- Priority: CRITICAL for production timeline

This is essential for our production schedule. Please confirm receipt and delivery timeline immediately.

Best regards,
{sender_name}
OEM Division - {company_name}"""
            },

            "quality_complaint": {
                "subject": "URGENT: Quality Issue - Batch #{batch_id} - Immediate Action Required",
                "body": """URGENT QUALITY ISSUE

We have discovered quality issues with batch #{batch_id}:

- Issue: {issue_description}
- Affected units: {affected_units}
- Impact: {impact_description}
- Detection date: {detection_date}

This is affecting our production line and requires immediate action. Please investigate and provide immediate resolution plan.

Contact: {sender_name}
Company: {company_name}
Priority: HIGH"""
            },

            "supplier_update": {
                "subject": "Material Delivery Update - Order #{order_id}",
                "body": """Dear Team,

Your raw material order #{order_id} status update:

- Status: {status}
- Delivery date: {delivery_date}
- Tracking number: {tracking}
- Material type: {material_type}

Please prepare for receipt. Quality certificate will be provided upon delivery.

Best regards,
{sender_name}
{company_name} Supply Chain"""
            },

            "logistics_coordination": {
                "subject": "Shipment Coordination - Pickup #{pickup_id}",
                "body": """Dear Logistics Team,

Pickup coordination for Happy Buttons shipment:

- Pickup ID: #{pickup_id}
- Scheduled: {pickup_date} at {pickup_time}
- Destination: {destination}
- Weight: {weight}kg
- Special instructions: {instructions}

Please have shipment ready at loading dock.

Regards,
{sender_name}
{company_name} Logistics"""
            }
        }

        # Get template
        template = templates.get(email_type)
        if not template:
            logger.warning(f"Unknown email type: {email_type}")
            return False

        # Fill in variables
        try:
            # Default variables
            default_vars = {
                'sender_name': sender_info.get('name', 'Unknown'),
                'company_name': sender_info.get('company', 'Unknown Company'),
                'project_type': random.choice(['automotive', 'electronics', 'industrial', 'consumer']),
                'order_id': f"ORD{random.randint(10000, 99999)}",
                'batch_id': f"B{random.randint(1000, 9999)}",
                'pickup_id': f"PU{random.randint(1000, 9999)}",
                'quantity': random.choice([500, 1000, 2000, 5000, 10000]),
                'specifications': random.choice(['Standard grade', 'Premium quality', 'Industrial grade', 'Custom specs']),
                'delivery_date': (datetime.now() + timedelta(days=random.randint(7, 21))).strftime('%Y-%m-%d'),
                'pickup_date': (datetime.now() + timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d'),
                'pickup_time': f"{random.randint(8, 16)}:00",
                'customer_name': random.choice(['BMW', 'Audi', 'Mercedes', 'VW', 'Porsche']),
                'issue_description': random.choice(['Color mismatch', 'Size tolerance', 'Surface defects', 'Mechanical failure']),
                'affected_units': f"{random.randint(10, 500)} units",
                'impact_description': 'Production delay expected',
                'detection_date': datetime.now().strftime('%Y-%m-%d'),
                'status': random.choice(['Shipped', 'In Transit', 'Ready for pickup']),
                'tracking': f"TRK{random.randint(100000, 999999)}",
                'material_type': random.choice(['Plastic pellets', 'Metal components', 'Electronic parts']),
                'destination': random.choice(['Munich', 'Stuttgart', 'Frankfurt', 'Berlin']),
                'weight': random.randint(50, 500),
                'instructions': 'Handle with care - fragile components'
            }

            # Merge with provided variables
            all_vars = {**default_vars, **variables}

            # Format subject and body
            subject = template['subject'].format(**all_vars)
            body = template['body'].format(**all_vars)

            # Queue the email
            return self.queue_email(
                sender_email=sender_info.get('email', 'unknown@example.com'),
                subject=subject,
                body=body,
                priority=variables.get('priority', 'normal')
            )

        except Exception as e:
            logger.error(f"Error formatting email template: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'is_running': self.is_running,
            'queue_size': self.email_queue.qsize(),
            'emails_sent': self.emails_sent,
            'errors_count': self.errors_count,
            'rate_limit_minute': self.max_emails_per_minute,
            'rate_limit_hour': self.max_emails_per_hour,
            'recent_send_rate_minute': len(self.last_send_times),
            'recent_send_rate_hour': len(self.hourly_send_times)
        }

# Global instance
real_email_sender = RealEmailSender()

def get_real_email_sender() -> RealEmailSender:
    """Get the global real email sender instance"""
    return real_email_sender

def send_business_email(email_type: str, sender_name: str, sender_email: str,
                       company_name: str = "Business Partner", **kwargs) -> bool:
    """Convenience function to send a business email"""
    sender = get_real_email_sender()

    if not sender.is_running:
        sender.start_service()

    sender_info = {
        'name': sender_name,
        'email': sender_email,
        'company': company_name
    }

    return sender.send_simulation_email(email_type, sender_info, kwargs)

# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("🧪 Testing Real Email Sender")
    print("=" * 50)

    sender = RealEmailSender()
    sender.start_service()

    # Test different email types
    test_emails = [
        ("customer_inquiry", "John Mueller", "john@customer.com", "TechCorp"),
        ("oem_order", "Hans Müller", "hans@oem1.com", "BMW Supplier"),
        ("quality_complaint", "Sarah Johnson", "s.johnson@manufacturing.com", "ManufacturingCorp")
    ]

    print("📧 Sending test emails...")
    for email_type, name, email, company in test_emails:
        success = send_business_email(email_type, name, email, company)
        print(f"  {email_type}: {'✅ Queued' if success else '❌ Failed'}")

    print("\n⏱️  Waiting for emails to be sent...")
    time.sleep(10)

    status = sender.get_status()
    print(f"\n📊 Status: {status}")

    sender.stop_service()
    print("\n✅ Test completed!")