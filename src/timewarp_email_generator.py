#!/usr/bin/env python3
"""
TimeWarp Email Generator
Generates realistic business emails with TimeWarp-scaled timing

Creates authentic customer, supplier, and internal emails based on:
- Weekly business cycles
- TimeWarp speed acceleration
- Realistic business patterns
- Configurable scenarios
"""

import random
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import yaml
import logging
from dataclasses import dataclass

from .timewarp_engine import get_timewarp
from .timewarp_business_simulation import get_business_simulator
from .real_email_sender import get_real_email_sender

logger = logging.getLogger(__name__)

@dataclass
class EmailTemplate:
    """Email template structure"""
    sender_type: str
    sender_domain: str
    subject_templates: List[str]
    body_templates: List[str]
    priority_weight: float
    time_patterns: List[str]  # ['monday_morning', 'tuesday_afternoon', etc.]
    attachments_probability: float

class TimeWarpEmailGenerator:
    """Generates business emails with TimeWarp timing acceleration"""

    def __init__(self, config_path: Optional[str] = None):
        self.timewarp = get_timewarp()
        self.business_simulator = get_business_simulator()
        self.real_email_sender = get_real_email_sender()
        self.is_running = False
        self.generation_thread = None
        self.current_interval = 30  # Default 30 seconds

        # Email templates and patterns
        self.email_templates = self._load_email_templates()
        self.business_contacts = self._load_business_contacts()
        self.weekly_patterns = self._load_weekly_patterns()

        # Generation tracking
        self.emails_generated = 0
        self.daily_email_counts = {}
        self.generation_callbacks = []

        # Real email sending configuration
        self.send_real_emails = True  # Enable real email sending

        logger.info("TimeWarp Email Generator initialized")

    def _load_email_templates(self) -> Dict[str, EmailTemplate]:
        """Load email templates for different business scenarios"""
        templates = {
            "customer_inquiry": EmailTemplate(
                sender_type="customer",
                sender_domain="customer.com",
                subject_templates=[
                    "Button inquiry for automotive project",
                    "Custom button specifications needed",
                    "Quote request for 5000 units",
                    "Product catalog request",
                    "Technical specifications inquiry"
                ],
                body_templates=[
                    "Hello,\n\nWe are working on a new automotive project and need custom buttons. Could you provide specifications and pricing?\n\nBest regards,\n{name}",
                    "Hi,\n\nI'm interested in your button products for our manufacturing line. Please send catalog and pricing information.\n\nThank you,\n{name}",
                    "Dear Team,\n\nWe require high-quality buttons for our premium product line. What options do you have available?\n\nRegards,\n{name}"
                ],
                priority_weight=0.7,
                time_patterns=["monday_morning", "tuesday_morning", "wednesday_morning"],
                attachments_probability=0.3
            ),

            "oem_order": EmailTemplate(
                sender_type="oem_customer",
                sender_domain="oem1.com",
                subject_templates=[
                    "URGENT: BMW Project Button Order",
                    "Audi Q-Series Button Requirements",
                    "Premium Button Order - Priority Customer",
                    "OEM Partnership: Large Volume Order",
                    "Automotive Grade Button Specifications"
                ],
                body_templates=[
                    "Dear Happy Buttons Team,\n\nWe have an urgent requirement for our BMW project. Please prioritize this order:\n\n- Quantity: {quantity} units\n- Specifications: Automotive grade\n- Delivery: ASAP\n\nThis is critical for production timeline.\n\nBest regards,\n{name}\nOEM Division",
                    "Hello,\n\nAudi project requires premium buttons with specific tolerances. Please review attached specifications and confirm delivery schedule.\n\nPriority: HIGH\n\nRegards,\n{name}"
                ],
                priority_weight=0.95,
                time_patterns=["monday_morning", "tuesday_morning", "thursday_afternoon"],
                attachments_probability=0.8
            ),

            "supplier_update": EmailTemplate(
                sender_type="supplier",
                sender_domain="supplier.com",
                subject_templates=[
                    "Raw Material Delivery Update",
                    "Production Schedule Confirmation",
                    "Quality Certificate - Batch #{batch}",
                    "Shipping Notification: Order #{order}",
                    "Material Availability Notice"
                ],
                body_templates=[
                    "Dear Team,\n\nYour raw material order #{order} has been processed and will ship today. Expected delivery: {delivery_date}.\n\nTracking: {tracking}\n\nBest regards,\n{name}\nSupply Chain",
                    "Hello,\n\nBatch #{batch} has passed all quality checks. Certificate attached. Ready for production use.\n\nRegards,\n{name}"
                ],
                priority_weight=0.6,
                time_patterns=["tuesday_afternoon", "wednesday_morning", "friday_morning"],
                attachments_probability=0.5
            ),

            "quality_complaint": EmailTemplate(
                sender_type="customer",
                sender_domain="customer.com",
                subject_templates=[
                    "URGENT: Quality Issue - Batch #{batch}",
                    "Defective Button Complaint",
                    "Product Quality Concern",
                    "Warranty Claim - Order #{order}",
                    "Quality Control Issue Report"
                ],
                body_templates=[
                    "URGENT: We have discovered quality issues with batch #{batch}. Multiple buttons show defects. This is affecting our production line.\n\nImmediate action required.\n\n{name}",
                    "Dear Quality Team,\n\nWe need to report defective buttons in our recent order. Please investigate and provide immediate resolution.\n\nOrder: #{order}\nIssue: {issue}\n\nRegards,\n{name}"
                ],
                priority_weight=0.9,
                time_patterns=["monday_afternoon", "wednesday_afternoon", "thursday_morning"],
                attachments_probability=0.7
            ),

            "logistics_coordination": EmailTemplate(
                sender_type="logistics",
                sender_domain="logistics.com",
                subject_templates=[
                    "Shipment Pickup Schedule",
                    "Delivery Confirmation - #{tracking}",
                    "Warehouse Capacity Update",
                    "Transportation Delay Notice",
                    "Custom Clearance Status"
                ],
                body_templates=[
                    "Dear Team,\n\nPickup scheduled for {date} at {time}. Please have shipment ready at loading dock.\n\nTracking: #{tracking}\n\nRegards,\n{name}\nLogistics",
                    "Delivery completed for order #{order}. Signed receipt attached.\n\nNext pickup: {next_date}\n\n{name}"
                ],
                priority_weight=0.5,
                time_patterns=["monday_morning", "wednesday_morning", "friday_afternoon"],
                attachments_probability=0.4
            ),

            "internal_coordination": EmailTemplate(
                sender_type="internal",
                sender_domain="h-bu.de",
                subject_templates=[
                    "Production Planning Meeting",
                    "Weekly Status Update",
                    "Resource Allocation Review",
                    "Process Improvement Proposal",
                    "Team Coordination Update"
                ],
                body_templates=[
                    "Team,\n\nWeekly production meeting scheduled for {date}. Please review attached agenda.\n\nKey topics:\n- Current orders\n- Quality metrics\n- Resource planning\n\nRegards,\n{name}",
                    "Status Update:\n\nProduction: {production}%\nQuality: {quality}%\nDelivery: On schedule\n\nNext review: {next_date}\n\n{name}"
                ],
                priority_weight=0.4,
                time_patterns=["monday_morning", "friday_afternoon"],
                attachments_probability=0.6
            )
        }
        return templates

    def _load_business_contacts(self) -> Dict[str, List[Dict[str, str]]]:
        """Load realistic business contacts for different types"""
        return {
            "customer": [
                {"name": "John Mueller", "email": "john@customer.com", "company": "TechCorp"},
                {"name": "Sarah Johnson", "email": "s.johnson@manufacturing.com", "company": "ManufacturingCorp"},
                {"name": "Mike Wilson", "email": "mike.w@autoparts.com", "company": "AutoParts Ltd"},
                {"name": "Lisa Chen", "email": "lisa@electronics.com", "company": "Electronics Inc"},
                {"name": "David Brown", "email": "d.brown@industrial.com", "company": "Industrial Solutions"}
            ],
            "oem_customer": [
                {"name": "Hans Müller", "email": "hans@oem1.com", "company": "BMW Supplier"},
                {"name": "Klaus Wagner", "email": "k.wagner@oem1.com", "company": "BMW Parts"},
                {"name": "Ingrid Schmidt", "email": "ingrid@oem2.com", "company": "Audi Components"},
                {"name": "Friedrich Weber", "email": "f.weber@oem2.com", "company": "Audi Procurement"},
                {"name": "Alexander König", "email": "alex@premium-auto.com", "company": "Premium Auto"}
            ],
            "supplier": [
                {"name": "Chen Wei", "email": "chen@china-materials.com", "company": "China Materials Ltd"},
                {"name": "Piotr Kowalski", "email": "p.kowalski@poland-supply.com", "company": "Poland Supply"},
                {"name": "Maria Gonzalez", "email": "maria@mexico-plastics.com", "company": "Mexico Plastics"},
                {"name": "Viktor Petrov", "email": "viktor@moldovan-materials.com", "company": "Moldovan Materials"},
                {"name": "James Smith", "email": "james@raw-materials.com", "company": "Raw Materials Inc"}
            ],
            "logistics": [
                {"name": "Transport Team", "email": "dispatch@global-logistics.com", "company": "Global Logistics"},
                {"name": "Shipping Dept", "email": "shipping@eurofreight.com", "company": "Euro Freight"},
                {"name": "Warehouse", "email": "warehouse@storage-solutions.com", "company": "Storage Solutions"},
                {"name": "Customs", "email": "customs@trade-services.com", "company": "Trade Services"}
            ],
            "internal": [
                {"name": "Production Manager", "email": "production@h-bu.de", "company": "Happy Buttons"},
                {"name": "Quality Control", "email": "quality@h-bu.de", "company": "Happy Buttons"},
                {"name": "Sales Team", "email": "sales@h-bu.de", "company": "Happy Buttons"},
                {"name": "Management", "email": "management@h-bu.de", "company": "Happy Buttons"}
            ]
        }

    def _load_weekly_patterns(self) -> Dict[str, Dict[str, int]]:
        """Load weekly email generation patterns"""
        return {
            "monday": {
                "morning": {"customer_inquiry": 5, "internal_coordination": 3, "supplier_update": 2},
                "afternoon": {"quality_complaint": 2, "logistics_coordination": 3}
            },
            "tuesday": {
                "morning": {"oem_order": 3, "customer_inquiry": 4, "supplier_update": 2},
                "afternoon": {"quality_complaint": 1, "logistics_coordination": 2}
            },
            "wednesday": {
                "morning": {"customer_inquiry": 3, "supplier_update": 4, "logistics_coordination": 2},
                "afternoon": {"quality_complaint": 2, "oem_order": 1}
            },
            "thursday": {
                "morning": {"quality_complaint": 3, "customer_inquiry": 2},
                "afternoon": {"oem_order": 2, "internal_coordination": 2}
            },
            "friday": {
                "morning": {"supplier_update": 2, "logistics_coordination": 3},
                "afternoon": {"internal_coordination": 4, "customer_inquiry": 2}
            },
            "saturday": {
                "morning": {"quality_complaint": 1},
                "afternoon": {}
            },
            "sunday": {
                "morning": {},
                "afternoon": {}
            }
        }

    def start_generation(self):
        """Start email generation with TimeWarp timing"""
        if not self.is_running:
            self.is_running = True
            self.generation_thread = threading.Thread(target=self._generation_loop, daemon=True)
            self.generation_thread.start()

            # Register with TimeWarp engine
            self.timewarp.register_email_generator(self)

            # Start real email sender if enabled
            if self.send_real_emails and not self.real_email_sender.is_running:
                self.real_email_sender.start_service()

            logger.info("TimeWarp Email Generation started")

    def stop_generation(self):
        """Stop email generation"""
        self.is_running = False
        logger.info("TimeWarp Email Generation stopped")

    def set_generation_interval(self, interval_seconds: float):
        """Set email generation interval (called by TimeWarp)"""
        self.current_interval = max(0.1, interval_seconds)  # Minimum 100ms
        logger.debug(f"Email generation interval set to {self.current_interval:.2f} seconds")

    def add_generation_callback(self, callback):
        """Add callback function to be called when emails are generated"""
        self.generation_callbacks.append(callback)

    def _generation_loop(self):
        """Main email generation loop"""
        while self.is_running:
            try:
                if not self.timewarp.is_paused:
                    # Get current simulated time
                    sim_time = self.timewarp.get_current_simulation_time()

                    # Generate emails based on patterns
                    emails = self._generate_emails_for_time(sim_time)

                    # Process generated emails
                    for email in emails:
                        self._process_generated_email(email)
                        self.emails_generated += 1

                # Sleep based on current TimeWarp speed
                time.sleep(self.current_interval)

            except Exception as e:
                logger.error(f"Error in email generation loop: {e}")
                time.sleep(1)

    def _generate_emails_for_time(self, sim_time: datetime) -> List[Dict[str, Any]]:
        """Generate emails appropriate for the simulated time"""
        emails = []

        day_name = sim_time.strftime("%A").lower()
        hour = sim_time.hour

        # Determine time period
        if 8 <= hour <= 12:
            period = "morning"
        elif 13 <= hour <= 17:
            period = "afternoon"
        else:
            # Evening/night - minimal activity
            period = "evening"

        # Get patterns for this day/time
        if day_name in self.weekly_patterns and period in self.weekly_patterns[day_name]:
            patterns = self.weekly_patterns[day_name][period]

            for email_type, count in patterns.items():
                # Add randomness - sometimes generate more/less emails
                actual_count = max(0, count + random.randint(-1, 2))

                for _ in range(actual_count):
                    if random.random() < 0.3:  # 30% chance per interval
                        # Use business simulator for more realistic emails
                        business_emails = self.business_simulator.generate_business_emails(
                            email_type, 1, sim_time, day_name, period
                        )
                        emails.extend(business_emails)

                        # Fallback to original generator if business simulator fails
                        if not business_emails:
                            email = self._generate_single_email(email_type, sim_time)
                            if email:
                                emails.append(email)

        return emails

    def _generate_single_email(self, email_type: str, sim_time: datetime) -> Optional[Dict[str, Any]]:
        """Generate a single email of specified type"""
        if email_type not in self.email_templates:
            logger.warning(f"Unknown email type: {email_type}")
            return None

        template = self.email_templates[email_type]

        # Select random contact
        contacts = self.business_contacts.get(template.sender_type, [])
        if not contacts:
            logger.warning(f"No contacts available for sender type: {template.sender_type}")
            return None

        contact = random.choice(contacts)

        # Generate email content
        subject = random.choice(template.subject_templates)
        body = random.choice(template.body_templates)

        # Fill in template variables
        variables = {
            "name": contact["name"],
            "company": contact.get("company", ""),
            "date": sim_time.strftime("%Y-%m-%d"),
            "time": sim_time.strftime("%H:%M"),
            "order": f"ORD{random.randint(10000, 99999)}",
            "batch": f"B{random.randint(1000, 9999)}",
            "tracking": f"TRK{random.randint(100000, 999999)}",
            "quantity": random.choice([500, 1000, 2000, 5000, 10000]),
            "delivery_date": (sim_time + timedelta(days=random.randint(3, 14))).strftime("%Y-%m-%d"),
            "next_date": (sim_time + timedelta(days=7)).strftime("%Y-%m-%d"),
            "production": random.randint(85, 98),
            "quality": random.randint(92, 99),
            "issue": random.choice(["Color mismatch", "Size tolerance", "Surface defects", "Mechanical failure"])
        }

        try:
            subject = subject.format(**variables)
            body = body.format(**variables)
        except KeyError as e:
            logger.warning(f"Template variable error: {e}")

        # Generate attachments if applicable
        attachments = []
        if random.random() < template.attachments_probability:
            attachments = self._generate_attachments(email_type)

        email = {
            "id": f"tw_{int(time.time())}_{random.randint(1000, 9999)}",
            "from": contact["email"],
            "to": "info@h-bu.de",
            "subject": subject,
            "content": body,
            "full_content": body,
            "timestamp": sim_time,
            "type": email_type.split("_")[0],  # Extract main type
            "priority": self._calculate_priority(template.priority_weight),
            "attachments": attachments,
            "source": "timewarp_simulation",
            "timewarp_generated": True,
            "simulation_time": sim_time.isoformat(),
            "real_generation_time": datetime.now().isoformat()
        }

        return email

    def _generate_attachments(self, email_type: str) -> List[Dict[str, Any]]:
        """Generate realistic attachments for email type"""
        attachment_types = {
            "customer_inquiry": [
                {"name": "project_specs.pdf", "type": "document", "size": "245 KB"},
                {"name": "requirements.docx", "type": "document", "size": "128 KB"}
            ],
            "oem_order": [
                {"name": "BMW_specifications.pdf", "type": "document", "size": "1.2 MB"},
                {"name": "technical_drawing.dwg", "type": "document", "size": "856 KB"},
                {"name": "quality_requirements.pdf", "type": "document", "size": "445 KB"}
            ],
            "supplier_update": [
                {"name": "quality_certificate.pdf", "type": "document", "size": "234 KB"},
                {"name": "test_results.xlsx", "type": "spreadsheet", "size": "67 KB"}
            ],
            "quality_complaint": [
                {"name": "defect_photos.zip", "type": "image", "size": "2.3 MB"},
                {"name": "quality_report.pdf", "type": "document", "size": "345 KB"}
            ]
        }

        available_attachments = attachment_types.get(email_type, [])
        if not available_attachments:
            return []

        # Return 1-2 random attachments
        count = random.randint(1, min(2, len(available_attachments)))
        return random.sample(available_attachments, count)

    def _calculate_priority(self, weight: float) -> str:
        """Calculate email priority based on weight and randomness"""
        if weight > 0.8:
            return "high"
        elif weight > 0.5:
            return "medium"
        else:
            return "low"

    def _process_generated_email(self, email: Dict[str, Any]):
        """Process a generated email through callbacks and send real email"""
        try:
            # Call all registered callbacks
            for callback in self.generation_callbacks:
                callback(email)

            # Send real email if enabled
            if self.send_real_emails:
                self._send_real_email(email)

            logger.debug(f"Generated email: {email['type']} from {email['from']}")

        except Exception as e:
            logger.error(f"Error processing generated email: {e}")

    def _send_real_email(self, email: Dict[str, Any]):
        """Send the generated email as a real email"""
        try:
            # Map email types to real email sender types
            type_mapping = {
                "customer": "customer_inquiry",
                "order": "customer_inquiry",
                "support": "customer_inquiry",
                "oem": "oem_order",
                "quality": "quality_complaint",
                "supplier": "supplier_update",
                "logistics": "logistics_coordination",
                "inquiry": "customer_inquiry"
            }

            email_type = type_mapping.get(email.get('type', 'customer'), 'customer_inquiry')

            # Extract sender info
            sender_email = email.get('from', 'unknown@example.com')
            sender_name = sender_email.split('@')[0].replace('.', ' ').title()

            # Extract domain for company name
            domain = sender_email.split('@')[1] if '@' in sender_email else 'Unknown'
            company_name = domain.split('.')[0].title() + " Corp"

            # Send using real email sender
            success = self.real_email_sender.send_simulation_email(
                email_type=email_type,
                sender_info={
                    'name': sender_name,
                    'email': sender_email,
                    'company': company_name
                },
                variables={
                    'priority': email.get('priority', 'normal')
                }
            )

            if success:
                logger.info(f"📧 Real email sent: {email['subject'][:50]}...")
            else:
                logger.warning(f"❌ Failed to send real email: {email['subject'][:50]}...")

        except Exception as e:
            logger.error(f"Error sending real email: {e}")

    def get_generation_stats(self) -> Dict[str, Any]:
        """Get email generation statistics"""
        return {
            "total_generated": self.emails_generated,
            "is_running": self.is_running,
            "current_interval": self.current_interval,
            "current_speed_level": self.timewarp.current_level,
            "daily_counts": self.daily_email_counts.copy()
        }


# Global email generator instance
email_generator = TimeWarpEmailGenerator()

def get_email_generator() -> TimeWarpEmailGenerator:
    """Get the global TimeWarp email generator instance"""
    return email_generator


if __name__ == "__main__":
    # Test the email generator
    print("🧪 Testing TimeWarp Email Generator")
    print("=" * 50)

    # Initialize logging
    logging.basicConfig(level=logging.INFO)

    # Create and test generator
    generator = TimeWarpEmailGenerator()

    def email_callback(email):
        print(f"Generated: {email['type']} - {email['subject'][:50]}...")

    generator.add_generation_callback(email_callback)

    # Start TimeWarp and generator
    from .timewarp_engine import get_timewarp
    timewarp = get_timewarp()
    timewarp.start()

    generator.start_generation()

    print("Generating emails for 10 seconds...")
    time.sleep(10)

    stats = generator.get_generation_stats()
    print(f"\nGeneration Stats:")
    print(f"  Total Generated: {stats['total_generated']}")
    print(f"  Current Interval: {stats['current_interval']:.2f}s")
    print(f"  TimeWarp Level: {stats['current_speed_level']}")

    generator.stop_generation()
    timewarp.stop()

    print("\n✅ TimeWarp Email Generator test completed!")