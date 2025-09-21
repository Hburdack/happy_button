"""
Happy Buttons Email Router - Python Implementation
Routes emails to appropriate business units based on rules
"""

import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging

from .parser import ParsedEmail, EmailMetadata

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """Email routing decision with reasoning"""
    email_id: str
    timestamp: datetime
    destination: str
    reasoning: List[str] = field(default_factory=list)
    priority: str = "medium"
    requires_human_review: bool = False
    auto_reply_template: Optional[str] = None
    escalation_level: int = 0
    sla_hours: int = 12
    confidence_score: float = 0.0


@dataclass
class RoutingRule:
    """Individual routing rule configuration"""
    condition: str
    destination: str
    priority: int = 1
    requires_review: bool = False
    auto_reply: Optional[str] = None


class EmailRouter:
    """
    Email Router for Happy Buttons Agentic Simulation
    Routes emails to appropriate business units based on rules
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config = None
        self.routing_rules = {}
        self.priority_rules = {}
        self.escalation_rules = {}
        self.sla_rules = {}

        # Load configuration
        if config_path and config_path.exists():
            self.load_config(config_path)
        else:
            self.setup_default_rules()

        # Statistics
        self.routing_stats = {
            'total_routed': 0,
            'auto_routed': 0,
            'escalated': 0,
            'human_review': 0
        }

    def load_config(self, config_path: Path) -> None:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                self.config = yaml.safe_load(file)
                self.setup_routing_rules()
                logger.info(f"Loaded router configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load router config: {str(e)}")
            self.setup_default_rules()

    def setup_routing_rules(self) -> None:
        """Setup routing rules from loaded configuration"""
        if not self.config:
            return

        # Extract company configuration
        company_config = self.config.get('company', {})

        # SLA Rules
        sla_config = company_config.get('sla', {})
        self.sla_rules = {
            'default_response_hours': sla_config.get('default_response_hours', 12),
            'expedite_window_hours': sla_config.get('expedite_window_hours', 24),
            'oem_response_hours': 4,  # Priority for OEM customers
            'critical_response_hours': 2  # Critical issues
        }

        # Priority Rules
        priority_config = self.config.get('priority', {})
        self.priority_rules = {
            'oem_over_b2c': priority_config.get('oem_over_b2c', True),
            'oem_domains': ['oem1.com'],  # From config
            'high_value_threshold': 10000
        }

        # Escalation Rules
        escalation_config = self.config.get('escalation', {})
        self.escalation_rules = {
            'ambiguous_to': escalation_config.get('ambiguous_to', 'management@h-bu.de'),
            'auto_escalation_hours': 24,
            'max_retries': 3
        }

        # Setup main routing rules
        self.setup_business_routing_rules()

    def setup_default_rules(self) -> None:
        """Initialize default routing rules"""
        self.sla_rules = {
            'default_response_hours': 12,
            'expedite_window_hours': 24,
            'oem_response_hours': 4,
            'critical_response_hours': 2
        }

        self.priority_rules = {
            'oem_over_b2c': True,
            'oem_domains': ['oem1.com'],
            'high_value_threshold': 10000
        }

        self.escalation_rules = {
            'ambiguous_to': 'management@h-bu.de',
            'auto_escalation_hours': 24,
            'max_retries': 3
        }

        self.setup_business_routing_rules()

    def setup_business_routing_rules(self) -> None:
        """Setup business-specific routing rules"""
        self.routing_rules = {
            # High Priority Routes (evaluated first)
            'order_pdf': {
                'destination': 'orders@h-bu.de',
                'priority': 10,
                'condition': 'has_order_pdf',
                'auto_reply': 'order_received'
            },
            'invoice_pdf': {
                'destination': 'finance@h-bu.de',
                'priority': 10,
                'condition': 'has_invoice_pdf',
                'auto_reply': 'invoice_received'
            },
            'oem_priority': {
                'destination': 'oem1@h-bu.de',
                'priority': 9,
                'condition': 'is_oem',
                'auto_reply': 'oem_priority_ack'
            },

            # Category-based Routes
            'supplier_category': {
                'destination': 'supplier@h-bu.de',
                'priority': 7,
                'condition': 'category_supplier',
                'auto_reply': 'supplier_ack'
            },
            'complaint_category': {
                'destination': 'quality@h-bu.de',
                'priority': 8,
                'condition': 'category_complaint',
                'requires_review': True,
                'auto_reply': 'complaint_ack'
            },
            'order_category': {
                'destination': 'orders@h-bu.de',
                'priority': 6,
                'condition': 'category_order',
                'auto_reply': 'order_received'
            },
            'invoice_category': {
                'destination': 'finance@h-bu.de',
                'priority': 6,
                'condition': 'category_invoice',
                'auto_reply': 'invoice_received'
            },
            'hr_category': {
                'destination': 'hr@h-bu.de',
                'priority': 5,
                'condition': 'category_hr',
                'auto_reply': 'hr_ack'
            },
            'logistics_category': {
                'destination': 'logistics@h-bu.de',
                'priority': 5,
                'condition': 'category_logistics',
                'auto_reply': 'generic_ack'
            },

            # Escalation Routes
            'management_escalation': {
                'destination': 'management@h-bu.de',
                'priority': 15,
                'condition': 'requires_escalation',
                'requires_review': True,
                'auto_reply': None
            },

            # Default Route
            'default_support': {
                'destination': 'support@h-bu.de',
                'priority': 1,
                'condition': 'default',
                'auto_reply': 'generic_ack'
            }
        }

    async def route_email(self, parsed_email: ParsedEmail) -> RoutingDecision:
        """
        Route parsed email to appropriate destination

        Args:
            parsed_email: Parsed email object

        Returns:
            RoutingDecision: Routing decision with destination and reasoning
        """
        try:
            # Initialize routing decision
            decision = RoutingDecision(
                email_id=parsed_email.id,
                timestamp=datetime.now(),
                destination="",
                priority=parsed_email.metadata.priority
            )

            # Apply routing logic
            matched_rule = self._find_matching_rule(parsed_email)

            if matched_rule:
                rule_name, rule_config = matched_rule
                decision.destination = rule_config['destination']
                decision.auto_reply_template = rule_config.get('auto_reply')
                decision.requires_human_review = rule_config.get('requires_review', False)
                decision.reasoning.append(f"Matched rule: {rule_name}")

                # Add specific reasoning based on rule
                self._add_routing_reasoning(decision, parsed_email, rule_name)
            else:
                # Fallback to default
                decision.destination = self.routing_rules['default_support']['destination']
                decision.auto_reply_template = 'generic_ack'
                decision.reasoning.append("No specific rule matched, using default routing")

            # Determine SLA
            decision.sla_hours = self._calculate_sla_hours(parsed_email, decision)

            # Check for escalation needs
            if self._requires_escalation(parsed_email):
                decision.destination = self.escalation_rules['ambiguous_to']
                decision.requires_human_review = True
                decision.escalation_level = 1
                decision.auto_reply_template = None
                decision.reasoning.append("Escalated due to sensitive content")

            # Calculate confidence score
            decision.confidence_score = self._calculate_routing_confidence(parsed_email, decision)

            # Update statistics
            self._update_routing_stats(decision)

            logger.info(f"Routed email {parsed_email.id} to {decision.destination}")
            return decision

        except Exception as e:
            logger.error(f"Email routing failed for {parsed_email.id}: {str(e)}")
            return self._create_error_routing(parsed_email, e)

    def _find_matching_rule(self, parsed_email: ParsedEmail) -> Optional[tuple]:
        """Find the highest priority matching rule"""
        matched_rules = []

        for rule_name, rule_config in self.routing_rules.items():
            if self._evaluate_rule_condition(parsed_email, rule_config['condition']):
                matched_rules.append((rule_name, rule_config))

        # Sort by priority (highest first)
        if matched_rules:
            matched_rules.sort(key=lambda x: x[1]['priority'], reverse=True)
            return matched_rules[0]

        return None

    def _evaluate_rule_condition(self, parsed_email: ParsedEmail, condition: str) -> bool:
        """Evaluate if email matches rule condition"""
        metadata = parsed_email.metadata

        condition_map = {
            'has_order_pdf': metadata.has_order_pdf,
            'has_invoice_pdf': metadata.has_invoice_pdf,
            'is_oem': metadata.is_oem,
            'category_supplier': metadata.category == 'supplier',
            'category_complaint': metadata.category == 'complaint',
            'category_order': metadata.category == 'order',
            'category_invoice': metadata.category == 'invoice',
            'category_hr': metadata.category == 'hr',
            'category_logistics': metadata.category == 'logistics',
            'category_finance': metadata.category == 'finance',
            'requires_escalation': self._requires_escalation(parsed_email),
            'is_urgent': metadata.is_urgent,
            'default': True
        }

        return condition_map.get(condition, False)

    def _add_routing_reasoning(self, decision: RoutingDecision,
                              parsed_email: ParsedEmail, rule_name: str) -> None:
        """Add specific reasoning for routing decision"""
        metadata = parsed_email.metadata

        reasoning_map = {
            'order_pdf': "Order PDF attachment detected",
            'invoice_pdf': "Invoice PDF attachment detected",
            'oem_priority': f"OEM customer from domain: {parsed_email.sender.domain}",
            'supplier_category': "Supplier-related keywords detected",
            'complaint_category': "Complaint keywords detected - flagged for review",
            'order_category': "Order-related content identified",
            'invoice_category': "Invoice-related content identified",
            'hr_category': "HR/Employment related inquiry",
            'logistics_category': "Logistics/Shipping related content",
            'management_escalation': "Content requires management attention"
        }

        reason = reasoning_map.get(rule_name, f"Matched {rule_name} rule")
        decision.reasoning.append(reason)

        # Add urgency note if applicable
        if metadata.is_urgent:
            decision.reasoning.append("Urgent keywords detected")

        # Add keyword information
        if metadata.keywords:
            decision.reasoning.append(f"Keywords found: {', '.join(metadata.keywords[:3])}")

    def _calculate_sla_hours(self, parsed_email: ParsedEmail,
                           decision: RoutingDecision) -> int:
        """Calculate SLA response time in hours"""
        metadata = parsed_email.metadata

        # Critical/urgent cases
        if metadata.priority == 'critical' or metadata.is_urgent:
            return self.sla_rules['critical_response_hours']

        # OEM customers get priority
        if metadata.is_oem:
            return self.sla_rules['oem_response_hours']

        # High priority cases
        if metadata.priority == 'high':
            return self.sla_rules['expedite_window_hours']

        # Default SLA
        return self.sla_rules['default_response_hours']

    def _requires_escalation(self, parsed_email: ParsedEmail) -> bool:
        """Check if email requires escalation to management"""
        content = f"{parsed_email.subject} {parsed_email.body}".lower()

        # Escalation trigger keywords
        escalation_keywords = [
            'legal', 'lawsuit', 'attorney', 'lawyer',
            'regulatory', 'compliance', 'audit',
            'ceo', 'president', 'director',
            'media', 'press', 'journalist',
            'emergency', 'critical', 'severe',
            'fraud', 'security breach'
        ]

        # Check for escalation triggers
        if any(keyword in content for keyword in escalation_keywords):
            return True

        # Check for high-value orders
        import re
        amounts = re.findall(r'\$[\d,]+\.?\d*', content)
        if amounts:
            max_amount = max(float(amount.replace('$', '').replace(',', ''))
                           for amount in amounts)
            if max_amount > 50000:
                return True

        return False

    def _calculate_routing_confidence(self, parsed_email: ParsedEmail,
                                    decision: RoutingDecision) -> float:
        """Calculate confidence score for routing decision"""
        confidence = 0.5  # Base confidence

        metadata = parsed_email.metadata

        # High confidence indicators
        if metadata.has_order_pdf or metadata.has_invoice_pdf:
            confidence += 0.3

        if metadata.is_oem:
            confidence += 0.2

        if len(metadata.keywords) > 2:
            confidence += 0.2

        if len(decision.reasoning) > 1:
            confidence += 0.1

        # Use metadata confidence as factor
        confidence = (confidence + metadata.confidence_score) / 2

        return min(confidence, 1.0)

    def _create_error_routing(self, parsed_email: ParsedEmail, error: Exception) -> RoutingDecision:
        """Create error routing for failed processing"""
        return RoutingDecision(
            email_id=parsed_email.id,
            timestamp=datetime.now(),
            destination=self.escalation_rules['ambiguous_to'],
            reasoning=[f"Routing error: {str(error)}"],
            priority='high',
            requires_human_review=True,
            auto_reply_template=None,
            escalation_level=2,
            sla_hours=self.sla_rules['critical_response_hours'],
            confidence_score=0.0
        )

    def _update_routing_stats(self, decision: RoutingDecision) -> None:
        """Update routing statistics"""
        self.routing_stats['total_routed'] += 1

        if decision.requires_human_review:
            self.routing_stats['human_review'] += 1

        if decision.escalation_level > 0:
            self.routing_stats['escalated'] += 1

        if decision.auto_reply_template:
            self.routing_stats['auto_routed'] += 1

    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        total = self.routing_stats['total_routed']

        stats = dict(self.routing_stats)
        if total > 0:
            stats.update({
                'auto_route_rate': (self.routing_stats['auto_routed'] / total) * 100,
                'escalation_rate': (self.routing_stats['escalated'] / total) * 100,
                'human_review_rate': (self.routing_stats['human_review'] / total) * 100
            })

        stats['available_destinations'] = list(set(
            rule['destination'] for rule in self.routing_rules.values()
        ))

        return stats

    def test_routing(self, parsed_email: ParsedEmail) -> RoutingDecision:
        """Test routing for an email without updating statistics"""
        # Save current stats
        original_stats = dict(self.routing_stats)

        # Perform routing
        import asyncio
        decision = asyncio.run(self.route_email(parsed_email))

        # Restore original stats
        self.routing_stats = original_stats

        # Mark as test
        decision.reasoning.append("(Test routing - stats not updated)")

        return decision

    def update_routing_rules(self, new_rules: Dict[str, Any]) -> None:
        """Update routing rules dynamically"""
        self.routing_rules.update(new_rules)
        logger.info(f"Updated routing rules: {list(new_rules.keys())}")

    def validate_routing_decision(self, decision: RoutingDecision) -> bool:
        """Validate routing decision"""
        required_fields = ['email_id', 'destination', 'priority']

        for field in required_fields:
            if not getattr(decision, field, None):
                return False

        # Validate destination format
        if '@' not in decision.destination:
            return False

        return True

    def get_available_destinations(self) -> List[str]:
        """Get all available routing destinations"""
        destinations = set()
        for rule in self.routing_rules.values():
            destinations.add(rule['destination'])

        return sorted(list(destinations))

    def get_rules_summary(self) -> Dict[str, Any]:
        """Get summary of current routing rules"""
        return {
            'total_rules': len(self.routing_rules),
            'destinations': len(self.get_available_destinations()),
            'sla_default_hours': self.sla_rules['default_response_hours'],
            'escalation_enabled': bool(self.escalation_rules.get('ambiguous_to')),
            'oem_priority_enabled': self.priority_rules['oem_over_b2c']
        }


if __name__ == "__main__":
    # Test the router
    import asyncio
    from .parser import create_test_email

    async def test_router():
        router = EmailRouter()

        # Create test emails
        test_cases = [
            {
                'sender': 'John Smith <john@oem1.com>',
                'subject': 'Urgent Order Request',
                'body': 'We need an urgent quote for buttons.',
                'expected_category': 'OEM Priority'
            },
            {
                'sender': 'supplier@materials.com',
                'subject': 'Delivery Confirmation',
                'body': 'Your shipment has been delivered.',
                'expected_category': 'Supplier'
            },
            {
                'sender': 'customer@email.com',
                'subject': 'Complaint about quality',
                'body': 'The buttons we received are defective.',
                'expected_category': 'Quality/Complaint'
            }
        ]

        for i, test_case in enumerate(test_cases):
            print(f"\n--- Test Case {i+1}: {test_case['expected_category']} ---")

            email = create_test_email(
                test_case['sender'],
                test_case['subject'],
                test_case['body']
            )

            decision = await router.route_email(email)

            print(f"Destination: {decision.destination}")
            print(f"Priority: {decision.priority}")
            print(f"SLA Hours: {decision.sla_hours}")
            print(f"Auto-reply: {decision.auto_reply_template}")
            print(f"Reasoning: {'; '.join(decision.reasoning)}")
            print(f"Confidence: {decision.confidence_score:.2f}")

        print(f"\n--- Routing Statistics ---")
        stats = router.get_routing_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

    asyncio.run(test_router())