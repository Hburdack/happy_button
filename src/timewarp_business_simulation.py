"""
TimeWarp Business Simulation Engine - Release 2.1
Simulates a complete 7-day business week with configurable time acceleration

Features:
- 5-level TimeWarp acceleration (1x to 1008x speed)
- Weekly business cycle with automatic restart
- Comprehensive email generation patterns
- Customer/OEM/Supplier/Internal email simulation
- Agent-based processing system
- Configurable YAML settings for workflow issues
"""

import json
import yaml
import random
import datetime
import os
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import threading
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class BusinessContact:
    """Business contact information"""
    name: str
    email: str
    company: str
    contact_type: str  # customer, oem, supplier, internal
    priority_level: str  # low, medium, high, urgent
    response_expectation: int  # expected response time in minutes

@dataclass
class EmailTemplate:
    """Email template with variables"""
    subject_template: str
    body_template: str
    variables: Dict[str, Any]
    urgency: str
    requires_response: bool
    estimated_processing_minutes: int

class TimeWarpBusinessSimulator:
    """
    Comprehensive business email simulation system

    Features:
    - Realistic customer interaction patterns
    - OEM priority customer simulation (BMW, Audi, Mercedes, Porsche)
    - Supplier coordination patterns
    - Internal team communication
    - Time-scaled generation based on TimeWarp speed
    - Configurable business scenarios
    """

    def __init__(self):
        try:
            from .timewarp_config import get_timewarp_config
            from .timewarp_engine import get_timewarp
            self.config = get_timewarp_config()
            self.timewarp = get_timewarp()
        except ImportError:
            self.config = None
            self.timewarp = None

        # Business contacts database
        self.contacts = self._initialize_business_contacts()

        # Email templates by category
        self.email_templates = self._initialize_email_templates()

        # Business scenarios
        self.scenarios = self._initialize_business_scenarios()

        # Generation state
        self.current_week_day = 0
        self.emails_generated_today = 0
        self.total_emails_generated = 0
        self.active_scenarios = []

        # Output directory for generated emails
        self.output_dir = "data/timewarp_emails"
        self._ensure_output_directory()

        logger.info("TimeWarp Business Simulator initialized")

    def _initialize_business_contacts(self) -> Dict[str, List[BusinessContact]]:
        """Initialize comprehensive business contacts database"""
        contacts = {
            'customers': [
                BusinessContact("Andreas Weber", "andreas.weber@automotive-tech.de", "Automotive Tech GmbH", "customer", "medium", 60),
                BusinessContact("Maria Schneider", "m.schneider@precision-parts.com", "Precision Parts Ltd", "customer", "medium", 45),
                BusinessContact("Jürgen Schmidt", "j.schmidt@industrial-solutions.de", "Industrial Solutions AG", "customer", "high", 30),
                BusinessContact("Lisa Chen", "lisa@electronics-corp.com", "Electronics Corporation", "customer", "low", 120),
                BusinessContact("Thomas Müller", "thomas@machinery-plus.de", "Machinery Plus", "customer", "medium", 60),
                BusinessContact("Sarah Johnson", "sarah@manufacturing-systems.com", "Manufacturing Systems Inc", "customer", "high", 30),
                BusinessContact("Roberto Rossi", "r.rossi@italian-components.it", "Italian Components SRL", "customer", "medium", 90)
            ],

            'oem_partners': [
                # BMW Group
                BusinessContact("Dr. Klaus Hofmann", "klaus.hofmann@bmw.de", "BMW Group", "oem", "urgent", 15),
                BusinessContact("Ingrid Bauer", "ingrid.bauer@bmw-supplier.de", "BMW Supplier Network", "oem", "urgent", 10),

                # Audi Group
                BusinessContact("Friedrich Wagner", "f.wagner@audi.de", "Audi AG", "oem", "urgent", 15),
                BusinessContact("Petra Zimmer", "p.zimmer@audi-procurement.de", "Audi Procurement", "oem", "urgent", 10),

                # Mercedes-Benz
                BusinessContact("Alexander König", "alex.koenig@mercedes-benz.com", "Mercedes-Benz Group", "oem", "urgent", 15),
                BusinessContact("Susanne Weber", "s.weber@daimler-supplier.com", "Daimler Supplier Management", "oem", "urgent", 10),

                # Porsche
                BusinessContact("Matthias Hartmann", "m.hartmann@porsche.de", "Porsche AG", "oem", "urgent", 10),
                BusinessContact("Christine Becker", "c.becker@porsche-quality.de", "Porsche Quality Assurance", "oem", "urgent", 5),

                # Other Premium OEMs
                BusinessContact("Hans Zimmermann", "h.zimmermann@premium-auto.de", "Premium Automotive", "oem", "high", 20),
                BusinessContact("Elena Popović", "e.popovic@luxury-vehicles.eu", "Luxury Vehicles Europe", "oem", "high", 25)
            ],

            'suppliers': [
                BusinessContact("Wei Chen", "wei.chen@china-materials.com", "China Materials Ltd", "supplier", "medium", 120),
                BusinessContact("Piotr Kowalski", "p.kowalski@poland-plastics.com", "Poland Plastics", "supplier", "medium", 90),
                BusinessContact("Maria González", "maria@mexico-components.com", "Mexico Components", "supplier", "medium", 180),
                BusinessContact("Viktor Petrov", "viktor@eastern-supply.com", "Eastern Supply Chain", "supplier", "medium", 120),
                BusinessContact("James Mitchell", "james@raw-materials-uk.com", "Raw Materials UK", "supplier", "high", 60),
                BusinessContact("Anna Korhonen", "anna@nordic-materials.fi", "Nordic Materials", "supplier", "medium", 90),
                BusinessContact("Giuseppe Romano", "g.romano@italian-supply.it", "Italian Supply Network", "supplier", "medium", 150)
            ],

            'logistics_partners': [
                BusinessContact("Transport Coordination", "dispatch@global-logistics.com", "Global Logistics", "logistics", "medium", 30),
                BusinessContact("Warehouse Team", "warehouse@euro-storage.com", "Euro Storage Solutions", "logistics", "medium", 45),
                BusinessContact("Customs Department", "customs@trade-facilitation.eu", "Trade Facilitation Services", "logistics", "high", 20),
                BusinessContact("Shipping Coordination", "shipping@freight-express.com", "Freight Express", "logistics", "medium", 40),
                BusinessContact("Quality Transport", "quality@premium-logistics.de", "Premium Logistics", "logistics", "high", 25)
            ],

            'internal_teams': [
                BusinessContact("Production Manager", "production@h-bu.de", "Happy Buttons", "internal", "high", 30),
                BusinessContact("Quality Control", "quality@h-bu.de", "Happy Buttons", "internal", "urgent", 15),
                BusinessContact("Sales Team", "sales@h-bu.de", "Happy Buttons", "internal", "medium", 45),
                BusinessContact("Management", "management@h-bu.de", "Happy Buttons", "internal", "low", 60),
                BusinessContact("Engineering", "engineering@h-bu.de", "Happy Buttons", "internal", "medium", 45),
                BusinessContact("Finance", "finance@h-bu.de", "Happy Buttons", "internal", "medium", 60),
                BusinessContact("HR Department", "hr@h-bu.de", "Happy Buttons", "internal", "low", 120)
            ]
        }

        return contacts

    def _initialize_email_templates(self) -> Dict[str, List[EmailTemplate]]:
        """Initialize comprehensive email templates"""
        templates = {
            'customer_inquiry': [
                EmailTemplate(
                    "Button inquiry for automotive project #{project_id}",
                    "Dear Happy Buttons Team,\n\nWe are developing a new automotive project and require high-quality buttons with specific requirements:\n\n- Quantity: {quantity} units\n- Application: {application}\n- Delivery deadline: {deadline}\n\nCould you please provide detailed specifications, pricing, and lead times?\n\nBest regards,\n{sender_name}\n{company}",
                    {
                        'project_id': lambda: f"AP{random.randint(2024001, 2024999)}",
                        'quantity': lambda: random.choice([500, 1000, 2500, 5000, 10000]),
                        'application': lambda: random.choice(["dashboard controls", "door panels", "center console", "steering wheel", "seat controls"]),
                        'deadline': lambda: (datetime.now() + timedelta(days=random.randint(21, 90))).strftime('%Y-%m-%d')
                    },
                    "medium", True, 45
                ),
                EmailTemplate(
                    "Custom button specifications needed",
                    "Hello,\n\nWe need custom buttons for our new product line. Requirements:\n\n- Color: {color}\n- Size: {size}mm diameter\n- Operating force: {force}N\n- IP rating: {ip_rating}\n\nPlease send technical specifications and samples if available.\n\n{sender_name}\n{company}",
                    {
                        'color': lambda: random.choice(["Black", "Silver", "Red", "Blue", "Custom Color"]),
                        'size': lambda: random.choice([12, 16, 19, 22, 25, 30]),
                        'force': lambda: random.choice([2.5, 3.5, 5.0, 7.5, 10.0]),
                        'ip_rating': lambda: random.choice(["IP65", "IP67", "IP68", "IP69K"])
                    },
                    "medium", True, 30
                ),
                EmailTemplate(
                    "Bulk order pricing request - {quantity} units",
                    "Dear Team,\n\nWe require pricing for bulk order:\n\n- Quantity: {quantity} units\n- Product: {product_type}\n- Annual volume: {annual_volume}\n\nWhat volume discounts can you offer? We are planning long-term partnership.\n\nRegards,\n{sender_name}",
                    {
                        'quantity': lambda: random.choice([5000, 10000, 25000, 50000, 100000]),
                        'product_type': lambda: random.choice(["Standard push buttons", "Illuminated buttons", "Emergency stops", "Key switches"]),
                        'annual_volume': lambda: random.choice([25000, 50000, 100000, 200000, 500000])
                    },
                    "high", True, 60
                )
            ],

            'oem_order': [
                EmailTemplate(
                    "[URGENT] BMW Project #{project} - Button Order Required",
                    "Priority: HIGH\n\nDear Happy Buttons Team,\n\nWe have urgent requirements for BMW project #{project}:\n\n- Part Number: {part_number}\n- Quantity: {quantity} units\n- Delivery: {delivery_date}\n- Quality Standard: BMW GS-95011\n\nThis is critical path for production. Please confirm capacity and delivery schedule immediately.\n\nBest regards,\n{sender_name}\nBMW Supplier Network",
                    {
                        'project': lambda: f"BMW{random.randint(2024100, 2024999)}",
                        'part_number': lambda: f"HB-BMW-{random.randint(10000, 99999)}",
                        'quantity': lambda: random.choice([2500, 5000, 7500, 10000, 15000]),
                        'delivery_date': lambda: (datetime.now() + timedelta(days=random.randint(14, 45))).strftime('%Y-%m-%d')
                    },
                    "urgent", True, 15
                ),
                EmailTemplate(
                    "[Audi] Premium Button Order - Q{quarter} Production",
                    "Dear Supplier,\n\nAudi Q{quarter} production schedule requires:\n\n- Product: {product_line} buttons\n- Quantity: {quantity} sets\n- Quality: Audi specification AS-{spec_number}\n- Delivery: Weekly deliveries starting {start_date}\n\nPlease confirm production capacity and quality certification status.\n\nRegards,\n{sender_name}\nAudi Procurement Team",
                    {
                        'quarter': lambda: f"{random.choice([1, 2, 3, 4])}/2024",
                        'product_line': lambda: random.choice(["A3", "A4", "A6", "A8", "Q3", "Q5", "Q7", "Q8"]),
                        'quantity': lambda: random.choice([3000, 5000, 8000, 12000]),
                        'spec_number': lambda: f"2024{random.randint(100, 999)}",
                        'start_date': lambda: (datetime.now() + timedelta(days=random.randint(10, 30))).strftime('%Y-%m-%d')
                    },
                    "urgent", True, 10
                ),
                EmailTemplate(
                    "[Mercedes] S-Class Button Specifications - Immediate Response Required",
                    "CONFIDENTIAL - Mercedes-Benz\n\nDear Happy Buttons,\n\nS-Class project requires premium buttons:\n\n- Application: {application}\n- Quantity: {quantity} units\n- Quality Level: Mercedes Standard MS-{standard}\n- Special Requirements: {requirements}\n\nThis is time-critical. Please respond within 2 hours with capability confirmation.\n\n{sender_name}\nMercedes-Benz Group",
                    {
                        'application': lambda: random.choice(["Interior lighting controls", "Seat adjustment", "Climate control", "Entertainment system", "Door controls"]),
                        'quantity': lambda: random.choice([1500, 2500, 4000, 6000]),
                        'standard': lambda: f"2024-{random.randint(10, 99)}",
                        'requirements': lambda: random.choice(["Backlit illumination", "Haptic feedback", "Premium finish", "Silent operation"])
                    },
                    "urgent", True, 5
                )
            ],

            'quality_complaint': [
                EmailTemplate(
                    "URGENT: Quality Issue - Batch #{batch_id}",
                    "PRIORITY: URGENT\n\nDear Quality Team,\n\nWe have identified quality issues in batch #{batch_id}:\n\n- Issue: {defect_type}\n- Affected quantity: {affected_units} units\n- Discovery date: {discovery_date}\n- Impact: {impact_level}\n\nThis is affecting our production line. Immediate investigation and corrective action required.\n\nContact: {sender_name}\n{company}",
                    {
                        'batch_id': lambda: f"HB{datetime.now().year}{random.randint(1000, 9999)}",
                        'defect_type': lambda: random.choice(["Button sticking", "Inconsistent actuation force", "Color variation", "Dimensional tolerance", "Electrical resistance"]),
                        'affected_units': lambda: random.randint(50, 500),
                        'discovery_date': lambda: (datetime.now() - timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d'),
                        'impact_level': lambda: random.choice(["Production stopped", "Quality hold", "Customer complaint", "Inspection required"])
                    },
                    "urgent", True, 120
                ),
                EmailTemplate(
                    "Quality Control Failure - Order #{order_id}",
                    "Dear Team,\n\nQuality inspection failed for order #{order_id}:\n\n- Test: {test_type}\n- Failure rate: {failure_rate}%\n- Root cause: {root_cause}\n- Action required: {action_required}\n\nPlease investigate and provide corrective action plan within 24 hours.\n\n{sender_name}",
                    {
                        'order_id': lambda: f"ORD{random.randint(100000, 999999)}",
                        'test_type': lambda: random.choice(["Durability test", "Environmental test", "Electrical test", "Dimensional inspection"]),
                        'failure_rate': lambda: random.randint(5, 25),
                        'root_cause': lambda: random.choice(["Material variation", "Process deviation", "Tool wear", "Environmental factors"]),
                        'action_required': lambda: random.choice(["Process adjustment", "Material review", "Tool maintenance", "Reprocessing"])
                    },
                    "urgent", True, 90
                )
            ],

            'supplier_update': [
                EmailTemplate(
                    "Material Delivery Update - Order #{order_id}",
                    "Dear Happy Buttons,\n\nDelivery update for your order #{order_id}:\n\n- Material: {material_type}\n- Quantity: {quantity} kg\n- Shipping date: {ship_date}\n- Expected arrival: {arrival_date}\n- Tracking: {tracking_number}\n\nAll quality certificates are attached.\n\nBest regards,\n{sender_name}\n{company}",
                    {
                        'order_id': lambda: f"SUP{random.randint(100000, 999999)}",
                        'material_type': lambda: random.choice(["ABS plastic", "PC plastic", "Metal contacts", "Springs", "Sealing rings"]),
                        'quantity': lambda: random.randint(100, 2000),
                        'ship_date': lambda: (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                        'arrival_date': lambda: (datetime.now() + timedelta(days=random.randint(3, 10))).strftime('%Y-%m-%d'),
                        'tracking_number': lambda: f"TRK{random.randint(100000000, 999999999)}"
                    },
                    "medium", False, 15
                ),
                EmailTemplate(
                    "Quality Certificate - Batch #{batch_id}",
                    "Dear Team,\n\nQuality certificate for batch #{batch_id}:\n\n- Material: {material}\n- Test results: {test_results}\n- Certification: {certification}\n- Valid until: {valid_until}\n\nAll specifications met. Ready for production use.\n\n{sender_name}\nQuality Department",
                    {
                        'batch_id': lambda: f"QC{random.randint(10000, 99999)}",
                        'material': lambda: random.choice(["Raw plastic", "Metal components", "Electronic parts", "Packaging materials"]),
                        'test_results': lambda: "PASSED",
                        'certification': lambda: f"ISO-{random.randint(9000, 9999)}-{datetime.now().year}",
                        'valid_until': lambda: (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
                    },
                    "medium", False, 10
                )
            ],

            'internal_coordination': [
                EmailTemplate(
                    "Production Planning - Week {week_number}",
                    "Team,\n\nProduction planning for week {week_number}:\n\n- Target output: {target_output} units\n- Priority orders: {priority_orders}\n- Resource allocation: {resource_status}\n- Quality focus: {quality_focus}\n\nPlease confirm capacity and resource availability.\n\n{sender_name}\nProduction Management",
                    {
                        'week_number': lambda: datetime.now().isocalendar()[1],
                        'target_output': lambda: random.randint(25000, 75000),
                        'priority_orders': lambda: random.randint(3, 8),
                        'resource_status': lambda: random.choice(["Full capacity", "80% capacity", "Limited resources", "Overtime required"]),
                        'quality_focus': lambda: random.choice(["Standard inspection", "Enhanced testing", "Customer audit preparation", "Process improvement"])
                    },
                    "medium", True, 60
                ),
                EmailTemplate(
                    "Weekly Team Coordination Meeting - {date}",
                    "Dear Team,\n\nWeekly coordination meeting scheduled for {date} at {time}.\n\nAgenda:\n- {agenda_item_1}\n- {agenda_item_2}\n- {agenda_item_3}\n- {agenda_item_4}\n\nPlease prepare status updates for your departments.\n\n{sender_name}",
                    {
                        'date': lambda: (datetime.now() + timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d'),
                        'time': lambda: random.choice(["09:00", "10:00", "14:00", "15:00"]),
                        'agenda_item_1': lambda: random.choice(["Production status", "Quality metrics", "Customer feedback", "Process improvements"]),
                        'agenda_item_2': lambda: random.choice(["Resource planning", "Equipment maintenance", "Training needs", "Safety updates"]),
                        'agenda_item_3': lambda: random.choice(["New orders review", "Supplier performance", "Cost optimization", "Technology updates"]),
                        'agenda_item_4': lambda: random.choice(["Action items review", "Next week planning", "Project updates", "Team announcements"])
                    },
                    "low", True, 30
                )
            ]
        }

        return templates

    def _initialize_business_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Initialize business scenarios for realistic simulation"""
        return {
            'normal_operations': {
                'description': 'Standard business operations',
                'email_multiplier': 1.0,
                'urgency_distribution': {'low': 0.3, 'medium': 0.5, 'high': 0.15, 'urgent': 0.05},
                'active_probability': 0.8
            },

            'high_demand_period': {
                'description': 'High demand period with increased orders',
                'email_multiplier': 1.8,
                'urgency_distribution': {'low': 0.1, 'medium': 0.4, 'high': 0.35, 'urgent': 0.15},
                'active_probability': 0.3
            },

            'quality_crisis': {
                'description': 'Quality issue requiring immediate attention',
                'email_multiplier': 2.5,
                'urgency_distribution': {'low': 0.0, 'medium': 0.2, 'high': 0.4, 'urgent': 0.4},
                'active_probability': 0.1
            },

            'new_product_launch': {
                'description': 'New product launch with customer inquiries',
                'email_multiplier': 2.0,
                'urgency_distribution': {'low': 0.2, 'medium': 0.6, 'high': 0.2, 'urgent': 0.0},
                'active_probability': 0.2
            },

            'holiday_period': {
                'description': 'Reduced activity during holiday periods',
                'email_multiplier': 0.3,
                'urgency_distribution': {'low': 0.7, 'medium': 0.2, 'high': 0.1, 'urgent': 0.0},
                'active_probability': 0.1
            }
        }

    def _ensure_output_directory(self):
        """Create output directory structure"""
        os.makedirs(self.output_dir, exist_ok=True)
        for contact_type in self.contacts.keys():
            os.makedirs(os.path.join(self.output_dir, contact_type), exist_ok=True)

    def generate_business_emails(self, email_type: str, count: int, sim_time: datetime,
                               day: str, period: str) -> List[Dict[str, Any]]:
        """Generate realistic business emails based on type and context"""
        generated_emails = []

        try:
            # Determine active business scenario
            active_scenario = self._get_active_scenario(sim_time)
            scenario_config = self.scenarios.get(active_scenario, self.scenarios['normal_operations'])

            # Adjust count based on scenario
            adjusted_count = max(1, int(count * scenario_config['email_multiplier']))

            for i in range(adjusted_count):
                email = self._create_business_email(email_type, sim_time, day, period, scenario_config)
                if email:
                    generated_emails.append(email)
                    self._save_email(email)

            self.emails_generated_today += len(generated_emails)
            self.total_emails_generated += len(generated_emails)

            logger.info(f"Generated {len(generated_emails)} {email_type} emails for {day} {period} (scenario: {active_scenario})")

        except Exception as e:
            logger.error(f"Error generating business emails: {e}")

        return generated_emails

    def _get_active_scenario(self, sim_time: datetime) -> str:
        """Determine active business scenario based on simulation time and randomness"""
        # Check for specific scenario triggers
        day_of_week = sim_time.weekday()
        hour = sim_time.hour

        # Weekend = holiday period
        if day_of_week >= 5:
            return 'holiday_period'

        # Random scenario selection based on probabilities
        rand = random.random()
        cumulative_prob = 0

        for scenario_name, config in self.scenarios.items():
            cumulative_prob += config['active_probability']
            if rand <= cumulative_prob:
                return scenario_name

        return 'normal_operations'

    def _create_business_email(self, email_type: str, sim_time: datetime, day: str,
                             period: str, scenario_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a single realistic business email"""
        try:
            # Map email type to contact type
            contact_type_mapping = {
                'customer_inquiry': 'customers',
                'customer_follow_up': 'customers',
                'oem_order': 'oem_partners',
                'quality_complaint': ['customers', 'oem_partners'],
                'supplier_update': 'suppliers',
                'supplier_coordination': 'suppliers',
                'logistics_coordination': 'logistics_partners',
                'logistics_update': 'logistics_partners',
                'internal_coordination': 'internal_teams',
                'internal_status': 'internal_teams'
            }

            contact_types = contact_type_mapping.get(email_type)
            if not contact_types:
                logger.warning(f"Unknown email type: {email_type}")
                return None

            if isinstance(contact_types, str):
                contact_types = [contact_types]

            # Select contact type
            contact_type = random.choice(contact_types)
            contacts = self.contacts.get(contact_type, [])

            if not contacts:
                logger.warning(f"No contacts available for type: {contact_type}")
                return None

            # Select contact
            contact = random.choice(contacts)

            # Select email template
            templates = self.email_templates.get(email_type, [])
            if not templates:
                logger.warning(f"No templates available for type: {email_type}")
                return None

            template = random.choice(templates)

            # Generate template variables
            variables = {}
            for var_name, generator in template.variables.items():
                if callable(generator):
                    variables[var_name] = generator()
                else:
                    variables[var_name] = generator

            # Add standard variables
            variables.update({
                'sender_name': contact.name,
                'company': contact.company,
                'current_date': sim_time.strftime('%Y-%m-%d'),
                'current_time': sim_time.strftime('%H:%M')
            })

            # Format subject and body
            try:
                subject = template.subject_template.format(**variables)
            except KeyError as e:
                logger.warning(f"Missing variable {e} in subject template")
                subject = template.subject_template

            try:
                body = template.body_template.format(**variables)
            except KeyError as e:
                logger.warning(f"Missing variable {e} in body template")
                body = template.body_template

            # Determine urgency based on scenario
            urgency = self._determine_urgency(template.urgency, scenario_config)

            # Determine recipient
            recipient = self._get_recipient_for_email_type(email_type)

            # Create email object
            email = {
                'id': f"sim_{int(time.time())}_{random.randint(1000, 9999)}",
                'from': contact.email,
                'to': recipient,
                'subject': subject,
                'content': body,
                'full_content': body,
                'timestamp': sim_time,
                'type': email_type,
                'priority': urgency,
                'contact_type': contact_type,
                'company': contact.company,
                'requires_response': template.requires_response,
                'estimated_processing_minutes': template.estimated_processing_minutes,
                'source': 'timewarp_business_simulation',
                'simulation_context': {
                    'day': day,
                    'period': period,
                    'scenario': scenario_config,
                    'contact_priority': contact.priority_level,
                    'response_expectation': contact.response_expectation
                },
                'template_variables': variables,
                'generation_time': datetime.now(),
                'simulation_time': sim_time.isoformat()
            }

            return email

        except Exception as e:
            logger.error(f"Error creating business email: {e}")
            return None

    def _determine_urgency(self, base_urgency: str, scenario_config: Dict[str, Any]) -> str:
        """Determine email urgency based on base urgency and scenario"""
        urgency_distribution = scenario_config.get('urgency_distribution', {})

        # If scenario overrides urgency distribution, use random selection
        if urgency_distribution:
            rand = random.random()
            cumulative_prob = 0

            for urgency_level, probability in urgency_distribution.items():
                cumulative_prob += probability
                if rand <= cumulative_prob:
                    return urgency_level

        return base_urgency

    def _get_recipient_for_email_type(self, email_type: str) -> str:
        """Get appropriate recipient email based on email type"""
        recipient_mapping = {
            'customer_inquiry': 'info@h-bu.de',
            'customer_follow_up': 'info@h-bu.de',
            'oem_order': 'orders@h-bu.de',
            'quality_complaint': 'quality@h-bu.de',
            'supplier_update': 'logistics@h-bu.de',
            'supplier_coordination': 'logistics@h-bu.de',
            'logistics_coordination': 'logistics@h-bu.de',
            'logistics_update': 'logistics@h-bu.de',
            'internal_coordination': 'management@h-bu.de',
            'internal_status': 'management@h-bu.de'
        }

        return recipient_mapping.get(email_type, 'info@h-bu.de')

    def _save_email(self, email: Dict[str, Any]):
        """Save generated email to file"""
        try:
            contact_type = email.get('contact_type', 'general')
            filename = f"{email['id']}.json"
            filepath = os.path.join(self.output_dir, contact_type, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(email, f, indent=2, ensure_ascii=False, default=str)

            logger.debug(f"Saved email {email['id']} to {filepath}")

        except Exception as e:
            logger.error(f"Error saving email: {e}")

    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive generation statistics"""
        return {
            'total_emails_generated': self.total_emails_generated,
            'emails_today': self.emails_generated_today,
            'active_scenarios': self.active_scenarios,
            'contact_counts': {
                contact_type: len(contacts)
                for contact_type, contacts in self.contacts.items()
            },
            'template_counts': {
                email_type: len(templates)
                for email_type, templates in self.email_templates.items()
            },
            'output_directory': self.output_dir
        }

# Global business simulator instance
business_simulator = TimeWarpBusinessSimulator()

def get_business_simulator() -> TimeWarpBusinessSimulator:
    """Get the global business simulator instance"""
    return business_simulator