#!/usr/bin/env python3
"""
Enhanced Business Week Simulation for Happy Buttons
Creates a complex, realistic week of business activity with issues and optimization opportunities
"""

import time
import random
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# Import real email sender
try:
    from .real_email_sender import get_real_email_sender
    REAL_EMAIL_AVAILABLE = True
except ImportError:
    try:
        # Try without relative import
        from real_email_sender import get_real_email_sender
        REAL_EMAIL_AVAILABLE = True
    except ImportError:
        REAL_EMAIL_AVAILABLE = False

logger = logging.getLogger(__name__)

class EnhancedBusinessSimulation:
    """Enhanced business simulation with realistic complex scenarios"""

    def __init__(self):
        self.running = False
        self.day_number = 1
        self.hour = 9  # Start at 9 AM
        self.current_issues = []
        self.resolved_issues = []
        self.email_queue = []

        # Real email sending configuration
        self.send_real_emails = True
        if REAL_EMAIL_AVAILABLE:
            self.real_email_sender = get_real_email_sender()
        else:
            self.real_email_sender = None
            self.send_real_emails = False

        # Business week scenarios with increasing complexity
        self.business_scenarios = {
            1: {  # Monday - Week Start Rush
                "theme": "Monday Morning Rush",
                "email_volume": "high",
                "issues": ["server_overload", "weekend_order_backlog"],
                "priority_customers": ["OEM Partners", "Enterprise Clients"]
            },
            2: {  # Tuesday - Quality Issues Emerge
                "theme": "Quality Control Crisis",
                "email_volume": "medium",
                "issues": ["quality_complaints", "defective_batch"],
                "priority_customers": ["Retail Chains", "Quality Auditors"]
            },
            3: {  # Wednesday - Supplier Problems
                "theme": "Supply Chain Disruption",
                "email_volume": "high",
                "issues": ["supplier_delay", "material_shortage"],
                "priority_customers": ["Production Managers", "Suppliers"]
            },
            4: {  # Thursday - Customer Escalations
                "theme": "Customer Escalation Day",
                "email_volume": "very_high",
                "issues": ["customer_complaints", "delivery_delays"],
                "priority_customers": ["Unhappy Customers", "VIP Accounts"]
            },
            5: {  # Friday - Week End Chaos
                "theme": "Friday Pressure Cooker",
                "email_volume": "extreme",
                "issues": ["system_overload", "staff_shortage", "urgent_orders"],
                "priority_customers": ["All Customer Types"]
            }
        }

        # Complex email patterns for realistic business communication
        self.email_patterns = {
            "monday_rush": [
                {
                    "from": "orders@manufacturing-corp.com",
                    "subject": "URGENT: Weekly order - 50K buttons needed by Friday",
                    "body": "We need to place our weekly order immediately. Production schedule is tight.",
                    "priority": "high",
                    "volume": 8
                },
                {
                    "from": "weekend-orders@system.internal",
                    "subject": "Weekend Order Backlog - 127 orders pending",
                    "body": "System accumulated 127 orders over the weekend requiring immediate processing.",
                    "priority": "high",
                    "volume": 12
                }
            ],
            "quality_crisis": [
                {
                    "from": "quality@retail-chain.com",
                    "subject": "DEFECTIVE BATCH ALERT - Batch #4521 Quality Issues",
                    "body": "We've discovered quality issues with batch #4521. 15% failure rate detected.",
                    "priority": "critical",
                    "volume": 6
                },
                {
                    "from": "complaints@customer-service.com",
                    "subject": "Multiple quality complaints - Immediate action required",
                    "body": "Receiving multiple complaints about button durability. Investigation needed.",
                    "priority": "high",
                    "volume": 15
                }
            ],
            "supply_disruption": [
                {
                    "from": "logistics@supplier-materials.com",
                    "subject": "SUPPLY CHAIN ALERT: Raw material delivery delayed 72 hours",
                    "body": "Due to transport strike, raw materials will be delayed by 3 days minimum.",
                    "priority": "critical",
                    "volume": 4
                },
                {
                    "from": "production@internal.h-bu.de",
                    "subject": "Material shortage affecting production schedule",
                    "body": "Current material levels insufficient for planned production. Need alternatives.",
                    "priority": "high",
                    "volume": 8
                }
            ],
            "customer_escalation": [
                {
                    "from": "ceo@important-client.com",
                    "subject": "ESCALATION: Unacceptable delay on Project Phoenix",
                    "body": "This delay is unacceptable. We need executive attention immediately.",
                    "priority": "critical",
                    "volume": 3
                },
                {
                    "from": "angry@customer.com",
                    "subject": "Order #HB-7789 - Complete disaster, demanding refund",
                    "body": "This is the worst service I've experienced. Demanding full refund and compensation.",
                    "priority": "high",
                    "volume": 22
                }
            ],
            "friday_chaos": [
                {
                    "from": "emergency@last-minute.com",
                    "subject": "FRIDAY EMERGENCY: Need 10K buttons delivered Monday",
                    "body": "Critical situation - need immediate production and weekend delivery.",
                    "priority": "critical",
                    "volume": 5
                },
                {
                    "from": "system@overload.alert",
                    "subject": "SYSTEM OVERLOAD: All agents at maximum capacity",
                    "body": "All customer service agents are at maximum capacity. Queue overflow detected.",
                    "priority": "critical",
                    "volume": 1
                }
            ]
        }

    def start_simulation(self, speed_multiplier=1):
        """Start the enhanced business simulation"""
        logger.info(f"🚀 Starting Enhanced Business Week Simulation (Speed: {speed_multiplier}x)")
        self.running = True
        self.speed_multiplier = speed_multiplier

        # Start real email sender if available
        if self.send_real_emails and self.real_email_sender and not self.real_email_sender.is_running:
            self.real_email_sender.start_service()
            logger.info("📧 Real email sender started for Enhanced Business Simulation")

        # Start simulation thread
        simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        simulation_thread.start()

    def _simulation_loop(self):
        """Main simulation loop with dynamic business scenarios"""
        while self.running and self.day_number <= 5:
            current_scenario = self.business_scenarios[self.day_number]

            logger.info(f"📅 Day {self.day_number} ({self._get_day_name()}): {current_scenario['theme']}")

            # Simulate business day (9 AM to 6 PM)
            for hour in range(9, 19):  # 9 AM to 6 PM
                if not self.running:
                    break

                self.hour = hour
                self._simulate_business_hour(current_scenario)

                # Sleep based on speed multiplier (1 hour = 60 seconds / speed_multiplier)
                time.sleep(60 / self.speed_multiplier)

            # End of day processing
            self._end_of_day_processing()
            self.day_number += 1

        logger.info("✅ Business Week Simulation Complete")

    def _simulate_business_hour(self, scenario):
        """Simulate one hour of business activity"""
        hour_name = self._get_hour_name(self.hour)
        volume = scenario["email_volume"]

        # Generate emails based on time and scenario
        email_count = self._calculate_email_volume(volume, self.hour)

        # Generate realistic emails for this hour
        for _ in range(email_count):
            email = self._generate_scenario_email(scenario)
            if email:
                # Add to display queue
                display_email = {
                    **email,
                    "timestamp": datetime.now(),
                    "day": self.day_number,
                    "hour": self.hour,
                    "scenario": scenario["theme"]
                }
                self.email_queue.append(display_email)

                # Send as real email
                if self.send_real_emails:
                    self._send_real_email(display_email)

        # Introduce issues based on scenario
        self._introduce_business_issues(scenario)

        logger.info(f"📧 {hour_name}: Generated {email_count} emails ({scenario['theme']})")

    def _calculate_email_volume(self, volume_level, hour):
        """Calculate realistic email volume based on time and business scenario"""
        base_volumes = {
            "low": 2,
            "medium": 5,
            "high": 12,
            "very_high": 20,
            "extreme": 35
        }

        base_count = base_volumes.get(volume_level, 5)

        # Business hours influence (more emails during peak hours)
        if hour in [9, 10, 11]:  # Morning rush
            multiplier = 1.5
        elif hour in [13, 14, 15]:  # Afternoon peak
            multiplier = 1.3
        elif hour in [16, 17, 18]:  # End of day rush
            multiplier = 1.8
        else:
            multiplier = 1.0

        return int(base_count * multiplier * random.uniform(0.7, 1.3))

    def _generate_scenario_email(self, scenario):
        """Generate contextual email based on current scenario"""
        scenario_key = scenario["theme"].lower().replace(" ", "_").replace(":", "")

        # Map themes to email patterns
        pattern_map = {
            "monday_morning_rush": "monday_rush",
            "quality_control_crisis": "quality_crisis",
            "supply_chain_disruption": "supply_disruption",
            "customer_escalation_day": "customer_escalation",
            "friday_pressure_cooker": "friday_chaos"
        }

        pattern_key = pattern_map.get(scenario_key, "monday_rush")
        patterns = self.email_patterns.get(pattern_key, [])

        if not patterns:
            return None

        # Select random pattern and customize
        pattern = random.choice(patterns)

        return {
            "from": pattern["from"],
            "subject": pattern["subject"],
            "body": pattern["body"],
            "priority": pattern["priority"],
            "needs_escalation": pattern["priority"] == "critical",
            "estimated_complexity": random.randint(1, 10)
        }

    def _introduce_business_issues(self, scenario):
        """Introduce realistic business issues that create optimization opportunities"""
        for issue_type in scenario["issues"]:
            if random.random() < 0.3:  # 30% chance per hour
                issue = self._create_business_issue(issue_type)
                self.current_issues.append(issue)
                logger.warning(f"⚠️ Business Issue: {issue['description']}")

    def _create_business_issue(self, issue_type):
        """Create specific business issues with impact metrics"""
        issues = {
            "server_overload": {
                "title": "Server Overload",
                "description": "Email processing servers at 95% capacity",
                "impact": "Response times increased by 300%",
                "solution": "Scale up email processing infrastructure",
                "optimization_potential": "High"
            },
            "weekend_order_backlog": {
                "title": "Weekend Order Backlog",
                "description": "127 orders accumulated over weekend",
                "impact": "Customer satisfaction dropping",
                "solution": "Implement weekend processing automation",
                "optimization_potential": "Medium"
            },
            "quality_complaints": {
                "title": "Quality Complaint Spike",
                "description": "15% increase in quality complaints",
                "impact": "Brand reputation at risk",
                "solution": "Enhanced quality control processes",
                "optimization_potential": "High"
            },
            "supplier_delay": {
                "title": "Supplier Delivery Delay",
                "description": "Key materials delayed by 72 hours",
                "impact": "Production schedule disrupted",
                "solution": "Diversify supplier base",
                "optimization_potential": "Critical"
            },
            "customer_complaints": {
                "title": "Customer Complaint Escalation",
                "description": "VIP customer threatening contract cancellation",
                "impact": "Potential €50K revenue loss",
                "solution": "Executive intervention required",
                "optimization_potential": "Critical"
            },
            "system_overload": {
                "title": "System Overload",
                "description": "All agents at maximum capacity",
                "impact": "New emails queuing for hours",
                "solution": "Dynamic agent scaling needed",
                "optimization_potential": "High"
            }
        }

        base_issue = issues.get(issue_type, issues["server_overload"])
        return {
            **base_issue,
            "timestamp": datetime.now(),
            "day": self.day_number,
            "hour": self.hour,
            "status": "active",
            "id": f"ISSUE-{random.randint(1000, 9999)}"
        }

    def _end_of_day_processing(self):
        """Process end of day activities and generate summary"""
        day_name = self._get_day_name()
        total_emails = len([e for e in self.email_queue if e["day"] == self.day_number])
        active_issues = len(self.current_issues)

        logger.info(f"📊 {day_name} Summary:")
        logger.info(f"   📧 Total Emails: {total_emails}")
        logger.info(f"   ⚠️ Active Issues: {active_issues}")
        logger.info(f"   🎯 Optimization Opportunities: {self._count_optimization_opportunities()}")

    def _count_optimization_opportunities(self):
        """Count potential optimization opportunities"""
        high_priority = len([i for i in self.current_issues if i.get("optimization_potential") == "High"])
        critical = len([i for i in self.current_issues if i.get("optimization_potential") == "Critical"])
        return high_priority + (critical * 2)

    def _get_day_name(self):
        """Get day name for current day number"""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        return days[self.day_number - 1] if self.day_number <= 5 else "Weekend"

    def _get_hour_name(self, hour):
        """Get formatted hour name"""
        return f"{hour:02d}:00"

    def get_simulation_status(self):
        """Get current simulation status"""
        return {
            "running": self.running,
            "day_number": self.day_number,
            "day_name": self._get_day_name(),
            "hour": self.hour,
            "current_issues": len(self.current_issues),
            "total_emails_today": len([e for e in self.email_queue if e["day"] == self.day_number]),
            "optimization_opportunities": self._count_optimization_opportunities(),
            "issues": self.current_issues[-3:],  # Last 3 issues
            "theme": self.business_scenarios.get(self.day_number, {}).get("theme", "Unknown")
        }

    def get_generated_emails(self, limit=50):
        """Get recently generated emails"""
        return self.email_queue[-limit:] if self.email_queue else []

    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False
        logger.info("🛑 Enhanced Business Simulation Stopped")

    def _send_real_email(self, email: Dict[str, Any]):
        """Send the generated email as a real email"""
        try:
            if not self.real_email_sender:
                return

            # Map email types to real email sender types
            type_mapping = {
                "critical": "quality_complaint",
                "high": "oem_order",
                "medium": "customer_inquiry",
                "low": "customer_inquiry",
                "urgent": "oem_order",
                "complaint": "quality_complaint",
                "order": "customer_inquiry",
                "supply": "supplier_update",
                "logistics": "logistics_coordination"
            }

            # Determine email type from priority or subject
            email_priority = email.get('priority', 'medium')
            subject = email.get('subject', '').lower()

            # Determine type from subject content
            if 'quality' in subject or 'defective' in subject or 'complaint' in subject:
                email_type = 'quality_complaint'
            elif 'urgent' in subject or 'bmw' in subject or 'audi' in subject or 'oem' in subject:
                email_type = 'oem_order'
            elif 'supplier' in subject or 'material' in subject or 'delivery' in subject:
                email_type = 'supplier_update'
            elif 'shipment' in subject or 'logistics' in subject or 'pickup' in subject:
                email_type = 'logistics_coordination'
            else:
                email_type = type_mapping.get(email_priority, 'customer_inquiry')

            # Extract sender info from email
            sender_email = email.get('from', 'simulation@business.com')
            sender_name = sender_email.split('@')[0].replace('.', ' ').title()

            # Extract domain for company name
            domain = sender_email.split('@')[1] if '@' in sender_email else 'business.com'
            company_name = domain.split('.')[0].title() + " Corp"

            # Use enhanced business scenario themes as context
            scenario_theme = email.get('scenario', 'Business Activity')

            # Send using real email sender
            success = self.real_email_sender.send_simulation_email(
                email_type=email_type,
                sender_info={
                    'name': sender_name,
                    'email': sender_email,
                    'company': company_name
                },
                variables={
                    'priority': email_priority,
                    'simulation_day': f"Day {self.day_number}",
                    'scenario_theme': scenario_theme
                }
            )

            if success:
                logger.info(f"📧 Real email sent from Enhanced Simulation: {email.get('subject', '')[:50]}...")
            else:
                logger.warning(f"❌ Failed to send real email: {email.get('subject', '')[:50]}...")

        except Exception as e:
            logger.error(f"Error sending real email from Enhanced Simulation: {e}")

# Global instance
enhanced_simulation = EnhancedBusinessSimulation()

def get_enhanced_simulation():
    """Get the global enhanced simulation instance"""
    return enhanced_simulation