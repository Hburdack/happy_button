"""
Business Unit Agents for Happy Buttons Agentic Simulation
Specialized agents for different business functions with Claude Flow integration
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re

from base_agent import BaseAgent, AgentResponse, AgentTask
from email.parser import ParsedEmail
from email.router import RoutingDecision

logger = logging.getLogger(__name__)


class InfoAgent(BaseAgent):
    """
    Main Info Agent - Handles info@h-bu.de
    Triages and routes emails, handles general inquiries
    """

    def __init__(self, agent_id: str = "info-001"):
        super().__init__(agent_id, "info_agent", {
            'handles_triage': True,
            'auto_reply_enabled': True,
            'escalation_threshold': 0.7
        })

    async def _process_email_impl(self, parsed_email: ParsedEmail,
                                 routing_decision: RoutingDecision,
                                 task: AgentTask) -> AgentResponse:
        """Process general info emails and triage decisions"""

        response_data = {
            'action': 'triage_completed',
            'original_destination': routing_decision.destination,
            'processing_time': datetime.now().isoformat()
        }

        # Check if this email needs immediate attention
        if parsed_email.metadata.is_urgent:
            response_data['priority_escalated'] = True
            await self.coordinate_with_agent('management-001',
                                           f"Urgent email requires attention: {parsed_email.id}")

        # Generate appropriate auto-reply
        auto_reply_template = self._select_auto_reply_template(parsed_email, routing_decision)

        return AgentResponse(
            task_id=task.id,
            agent_id=self.agent_id,
            status="success",
            response_data=response_data,
            auto_reply=auto_reply_template,
            next_actions=[f"Route to {routing_decision.destination}"],
            coordination_notes=[f"Processed general inquiry from {parsed_email.sender.email}"]
        )

    def _select_auto_reply_template(self, parsed_email: ParsedEmail,
                                   routing_decision: RoutingDecision) -> str:
        """Select appropriate auto-reply template"""
        if routing_decision.requires_human_review:
            return None  # No auto-reply for human review cases

        if parsed_email.metadata.is_urgent:
            return 'expedite_ack'
        elif parsed_email.metadata.is_oem:
            return 'oem_priority_ack'
        else:
            return 'generic_ack'

    def get_agent_capabilities(self) -> Dict[str, Any]:
        return {
            'triage': True,
            'general_inquiry': True,
            'auto_reply': True,
            'escalation': True,
            'supported_languages': ['en'],
            'max_concurrent_tasks': 50
        }

    def validate_email_for_agent(self, parsed_email: ParsedEmail) -> bool:
        """Info agent can handle any email for triage"""
        return True


class OrdersAgent(BaseAgent):
    """
    Orders Agent - Handles orders@h-bu.de
    Processes order requests, confirmations, and order-related inquiries
    """

    def __init__(self, agent_id: str = "orders-001"):
        super().__init__(agent_id, "orders_agent", {
            'auto_process_threshold': 5000,  # Auto-process orders under $5000
            'requires_approval_over': 25000,  # Require approval over $25000
            'oem_priority': True
        })

    async def _process_email_impl(self, parsed_email: ParsedEmail,
                                 routing_decision: RoutingDecision,
                                 task: AgentTask) -> AgentResponse:
        """Process order-related emails"""

        # Extract order information
        order_info = await self._extract_order_info(parsed_email)

        response_data = {
            'action': 'order_processed',
            'order_info': order_info,
            'auto_processable': order_info['value'] < self.config['auto_process_threshold'],
            'requires_approval': order_info['value'] > self.config['requires_approval_over']
        }

        # Coordinate with other agents if needed
        coordination_notes = []

        if order_info['requires_inventory_check']:
            await self.coordinate_with_agent('logistics-001',
                                           f"Inventory check needed for order {order_info['id']}")
            coordination_notes.append("Coordinated with logistics for inventory check")

        if response_data['requires_approval']:
            await self.coordinate_with_agent('management-001',
                                           f"High-value order requires approval: {order_info['value']}")
            coordination_notes.append("Escalated to management for approval")

        # Determine auto-reply
        auto_reply = 'order_received'
        if parsed_email.metadata.is_urgent:
            auto_reply = 'expedite_ack'

        return AgentResponse(
            task_id=task.id,
            agent_id=self.agent_id,
            status="success",
            response_data=response_data,
            auto_reply=auto_reply,
            next_actions=self._determine_next_actions(order_info, response_data),
            coordination_notes=coordination_notes
        )

    async def _extract_order_info(self, parsed_email: ParsedEmail) -> Dict[str, Any]:
        """Extract order information from email"""
        content = f"{parsed_email.subject} {parsed_email.body}"

        # Extract order number
        order_match = re.search(r'(?:order|po)\s*#?\s*(\w+)', content, re.IGNORECASE)
        order_id = order_match.group(1) if order_match else f"ORD-{datetime.now().strftime('%Y%m%d')}-{parsed_email.id[:6]}"

        # Extract monetary amounts
        amounts = re.findall(r'\$[\d,]+\.?\d*', content)
        order_value = 0
        if amounts:
            # Take the largest amount found
            order_value = max(float(amount.replace('$', '').replace(',', '')) for amount in amounts)

        # Extract quantities
        qty_match = re.search(r'(\d+)\s*(?:pieces|pcs|units|buttons)', content, re.IGNORECASE)
        quantity = int(qty_match.group(1)) if qty_match else 0

        return {
            'id': order_id,
            'value': order_value,
            'quantity': quantity,
            'customer': parsed_email.sender.email,
            'customer_domain': parsed_email.sender.domain,
            'is_oem': parsed_email.metadata.is_oem,
            'requires_inventory_check': quantity > 1000,
            'extracted_at': datetime.now().isoformat()
        }

    def _determine_next_actions(self, order_info: Dict, response_data: Dict) -> List[str]:
        """Determine next actions based on order analysis"""
        actions = []

        if response_data['auto_processable']:
            actions.append("Auto-process order")
        else:
            actions.append("Manual review required")

        if order_info['requires_inventory_check']:
            actions.append("Verify inventory availability")

        if response_data['requires_approval']:
            actions.append("Await management approval")

        return actions

    def get_agent_capabilities(self) -> Dict[str, Any]:
        return {
            'order_processing': True,
            'order_validation': True,
            'inventory_coordination': True,
            'auto_processing': True,
            'value_limits': {
                'auto_process_max': self.config['auto_process_threshold'],
                'approval_required_over': self.config['requires_approval_over']
            }
        }

    def validate_email_for_agent(self, parsed_email: ParsedEmail) -> bool:
        return (parsed_email.metadata.category == 'order' or
                parsed_email.metadata.has_order_pdf or
                'order' in parsed_email.subject.lower())


class OEMAgent(BaseAgent):
    """
    OEM Agent - Handles oem1@h-bu.de
    Specialized handling for OEM customers with priority service
    """

    def __init__(self, agent_id: str = "oem-001"):
        super().__init__(agent_id, "oem_agent", {
            'priority_sla_hours': 4,
            'auto_escalate_after_hours': 2,
            'volume_discount_threshold': 50000
        })

    async def _process_email_impl(self, parsed_email: ParsedEmail,
                                 routing_decision: RoutingDecision,
                                 task: AgentTask) -> AgentResponse:
        """Process OEM customer emails with priority handling"""

        # Enhanced analysis for OEM customers
        oem_analysis = await self._analyze_oem_request(parsed_email)

        response_data = {
            'action': 'oem_priority_processed',
            'customer_tier': oem_analysis['tier'],
            'estimated_value': oem_analysis['value'],
            'priority_level': 'high',
            'sla_deadline': (datetime.now() + timedelta(hours=self.config['priority_sla_hours'])).isoformat()
        }

        # Coordinate with relevant departments
        coordination_notes = []

        if oem_analysis['needs_custom_quote']:
            await self.coordinate_with_agent('finance-001',
                                           f"Custom quote needed for OEM customer: {parsed_email.sender.domain}")
            coordination_notes.append("Coordinated with finance for custom pricing")

        if oem_analysis['large_volume']:
            await self.coordinate_with_agent('logistics-001',
                                           f"Large volume OEM order - capacity planning needed")
            coordination_notes.append("Alerted logistics for capacity planning")

        return AgentResponse(
            task_id=task.id,
            agent_id=self.agent_id,
            status="success",
            response_data=response_data,
            auto_reply='oem_priority_ack',
            next_actions=self._determine_oem_actions(oem_analysis),
            coordination_notes=coordination_notes
        )

    async def _analyze_oem_request(self, parsed_email: ParsedEmail) -> Dict[str, Any]:
        """Analyze OEM customer request"""
        content = f"{parsed_email.subject} {parsed_email.body}".lower()

        # Determine customer tier based on domain and content
        tier = 'gold' if parsed_email.sender.domain in ['oem1.com'] else 'standard'

        # Extract value indicators
        amounts = re.findall(r'\$[\d,]+\.?\d*', content)
        estimated_value = max(float(amount.replace('$', '').replace(',', ''))
                            for amount in amounts) if amounts else 0

        # Check for volume indicators
        volume_keywords = ['bulk', 'volume', 'large order', 'thousands', 'million']
        large_volume = any(keyword in content for keyword in volume_keywords)

        return {
            'tier': tier,
            'value': estimated_value,
            'large_volume': large_volume or estimated_value > self.config['volume_discount_threshold'],
            'needs_custom_quote': 'custom' in content or 'quote' in content,
            'urgency_level': 'high' if parsed_email.metadata.is_urgent else 'medium'
        }

    def _determine_oem_actions(self, analysis: Dict) -> List[str]:
        """Determine actions for OEM customer"""
        actions = ["Assign dedicated account manager"]

        if analysis['needs_custom_quote']:
            actions.append("Prepare custom quotation")

        if analysis['large_volume']:
            actions.append("Schedule capacity planning meeting")
            actions.append("Prepare volume discount proposal")

        return actions

    def get_agent_capabilities(self) -> Dict[str, Any]:
        return {
            'oem_priority': True,
            'custom_pricing': True,
            'volume_discounts': True,
            'dedicated_support': True,
            'fast_track': True,
            'sla_hours': self.config['priority_sla_hours']
        }

    def validate_email_for_agent(self, parsed_email: ParsedEmail) -> bool:
        return parsed_email.metadata.is_oem


class SupplierAgent(BaseAgent):
    """
    Supplier Agent - Handles supplier@h-bu.de
    Manages supplier communications, deliveries, and procurement
    """

    def __init__(self, agent_id: str = "supplier-001"):
        super().__init__(agent_id, "supplier_agent", {
            'auto_confirm_deliveries': True,
            'track_inventory_updates': True
        })

    async def _process_email_impl(self, parsed_email: ParsedEmail,
                                 routing_decision: RoutingDecision,
                                 task: AgentTask) -> AgentResponse:
        """Process supplier communications"""

        supplier_info = await self._analyze_supplier_communication(parsed_email)

        response_data = {
            'action': 'supplier_processed',
            'communication_type': supplier_info['type'],
            'supplier_id': supplier_info['supplier_id'],
            'requires_inventory_update': supplier_info['affects_inventory']
        }

        coordination_notes = []

        if supplier_info['affects_inventory']:
            await self.coordinate_with_agent('logistics-001',
                                           f"Inventory update from supplier: {supplier_info['type']}")
            coordination_notes.append("Coordinated inventory update with logistics")

        return AgentResponse(
            task_id=task.id,
            agent_id=self.agent_id,
            status="success",
            response_data=response_data,
            auto_reply='supplier_ack',
            coordination_notes=coordination_notes
        )

    async def _analyze_supplier_communication(self, parsed_email: ParsedEmail) -> Dict[str, Any]:
        """Analyze supplier communication type and content"""
        content = f"{parsed_email.subject} {parsed_email.body}".lower()

        # Determine communication type
        if any(word in content for word in ['delivery', 'delivered', 'shipment', 'shipped']):
            comm_type = 'delivery_confirmation'
        elif any(word in content for word in ['invoice', 'bill', 'payment']):
            comm_type = 'invoice'
        elif any(word in content for word in ['delay', 'postpone', 'late']):
            comm_type = 'delay_notification'
        else:
            comm_type = 'general'

        return {
            'type': comm_type,
            'supplier_id': parsed_email.sender.domain,
            'affects_inventory': comm_type in ['delivery_confirmation', 'delay_notification'],
            'priority': 'high' if comm_type == 'delay_notification' else 'medium'
        }

    def get_agent_capabilities(self) -> Dict[str, Any]:
        return {
            'supplier_management': True,
            'delivery_tracking': True,
            'inventory_coordination': True,
            'procurement_support': True
        }

    def validate_email_for_agent(self, parsed_email: ParsedEmail) -> bool:
        return parsed_email.metadata.category == 'supplier'


class QualityAgent(BaseAgent):
    """
    Quality Agent - Handles quality@h-bu.de
    Manages complaints, quality issues, and product feedback
    """

    def __init__(self, agent_id: str = "quality-001"):
        super().__init__(agent_id, "quality_agent", {
            'auto_escalate_serious': True,
            'requires_photo_evidence': True,
            'issue_tracking': True
        })

    async def _process_email_impl(self, parsed_email: ParsedEmail,
                                 routing_decision: RoutingDecision,
                                 task: AgentTask) -> AgentResponse:
        """Process quality issues and complaints"""

        quality_analysis = await self._analyze_quality_issue(parsed_email)

        response_data = {
            'action': 'quality_issue_logged',
            'severity': quality_analysis['severity'],
            'issue_id': quality_analysis['issue_id'],
            'requires_investigation': quality_analysis['needs_investigation']
        }

        coordination_notes = []

        if quality_analysis['severity'] == 'critical':
            await self.coordinate_with_agent('management-001',
                                           f"Critical quality issue: {quality_analysis['issue_id']}")
            coordination_notes.append("Escalated critical issue to management")

        return AgentResponse(
            task_id=task.id,
            agent_id=self.agent_id,
            status="success",
            response_data=response_data,
            auto_reply='quality_ack',
            next_actions=self._determine_quality_actions(quality_analysis),
            coordination_notes=coordination_notes
        )

    async def _analyze_quality_issue(self, parsed_email: ParsedEmail) -> Dict[str, Any]:
        """Analyze quality issue severity and type"""
        content = f"{parsed_email.subject} {parsed_email.body}".lower()

        # Determine severity
        if any(word in content for word in ['critical', 'dangerous', 'safety', 'recall']):
            severity = 'critical'
        elif any(word in content for word in ['defective', 'broken', 'wrong', 'damaged']):
            severity = 'high'
        elif any(word in content for word in ['minor', 'cosmetic', 'slight']):
            severity = 'low'
        else:
            severity = 'medium'

        issue_id = f"QI-{datetime.now().strftime('%Y%m%d')}-{parsed_email.id[:6]}"

        return {
            'issue_id': issue_id,
            'severity': severity,
            'needs_investigation': severity in ['critical', 'high'],
            'customer': parsed_email.sender.email,
            'reported_at': datetime.now().isoformat()
        }

    def _determine_quality_actions(self, analysis: Dict) -> List[str]:
        """Determine actions based on quality issue analysis"""
        actions = [f"Log issue {analysis['issue_id']}"]

        if analysis['severity'] == 'critical':
            actions.extend([
                "Immediate investigation required",
                "Customer callback within 2 hours",
                "Quality manager notification"
            ])
        elif analysis['severity'] == 'high':
            actions.extend([
                "Schedule investigation",
                "Customer response within 4 hours"
            ])

        return actions

    def get_agent_capabilities(self) -> Dict[str, Any]:
        return {
            'quality_management': True,
            'complaint_handling': True,
            'issue_tracking': True,
            'investigation_coordination': True,
            'severity_assessment': True
        }

    def validate_email_for_agent(self, parsed_email: ParsedEmail) -> bool:
        return parsed_email.metadata.category == 'complaint'


class ManagementAgent(BaseAgent):
    """
    Management Agent - Handles management@h-bu.de
    Handles escalations, high-value decisions, and oversight
    """

    def __init__(self, agent_id: str = "management-001"):
        super().__init__(agent_id, "management_agent", {
            'escalation_handler': True,
            'decision_authority': True,
            'oversight_role': True
        })

    async def _process_email_impl(self, parsed_email: ParsedEmail,
                                 routing_decision: RoutingDecision,
                                 task: AgentTask) -> AgentResponse:
        """Process management escalations and high-level decisions"""

        escalation_analysis = await self._analyze_escalation(parsed_email)

        response_data = {
            'action': 'management_review',
            'escalation_type': escalation_analysis['type'],
            'priority': 'critical',
            'requires_immediate_attention': escalation_analysis['immediate'],
            'decision_deadline': (datetime.now() + timedelta(hours=2)).isoformat()
        }

        return AgentResponse(
            task_id=task.id,
            agent_id=self.agent_id,
            status="success",
            response_data=response_data,
            auto_reply=None,  # Management reviews require personal attention
            next_actions=["Schedule management review", "Prepare briefing document"],
            coordination_notes=["Escalated to senior management level"]
        )

    async def _analyze_escalation(self, parsed_email: ParsedEmail) -> Dict[str, Any]:
        """Analyze escalation type and urgency"""
        content = f"{parsed_email.subject} {parsed_email.body}".lower()

        if any(word in content for word in ['legal', 'lawsuit', 'attorney']):
            escalation_type = 'legal'
        elif any(word in content for word in ['media', 'press', 'journalist']):
            escalation_type = 'media'
        elif any(word in content for word in ['regulatory', 'compliance']):
            escalation_type = 'regulatory'
        else:
            escalation_type = 'business'

        immediate = any(word in content for word in ['urgent', 'immediate', 'emergency'])

        return {
            'type': escalation_type,
            'immediate': immediate,
            'sender_type': 'oem' if parsed_email.metadata.is_oem else 'standard'
        }

    def get_agent_capabilities(self) -> Dict[str, Any]:
        return {
            'escalation_handling': True,
            'executive_decisions': True,
            'crisis_management': True,
            'stakeholder_communication': True,
            'authority_level': 'executive'
        }

    def validate_email_for_agent(self, parsed_email: ParsedEmail) -> bool:
        # Management agent handles escalations and sensitive content
        content = parsed_email.body.lower()
        return any(word in content for word in ['legal', 'ceo', 'president', 'media', 'management', 'escalation'])


# Agent Factory
def create_business_agents() -> Dict[str, BaseAgent]:
    """Create all business unit agents"""
    return {
        'info': InfoAgent(),
        'orders': OrdersAgent(),
        'oem': OEMAgent(),
        'supplier': SupplierAgent(),
        'quality': QualityAgent(),
        'management': ManagementAgent()
    }


if __name__ == "__main__":
    # Test the business agents
    async def test_agents():
        agents = create_business_agents()

        for agent_name, agent in agents.items():
            print(f"\n--- {agent_name.upper()} AGENT ---")
            print(f"ID: {agent.agent_id}")
            print(f"Type: {agent.agent_type}")
            print(f"Capabilities: {agent.get_agent_capabilities()}")

    asyncio.run(test_agents())