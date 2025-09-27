"""
Production Agent for Happy Buttons Release 2
Handles production planning, scheduling, capacity management, and quality control
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .base_agent import BaseAgent, AgentResponse, AgentTask
from .agent_email_dispatcher import TaskTypes

try:
    from email_processing.parser import ParsedEmail
    from email_processing.router import RoutingDecision
except ImportError:
    from ..email_processing.parser import ParsedEmail
    from ..email_processing.router import RoutingDecision

logger = logging.getLogger(__name__)


class ProductionAgent(BaseAgent):
    """
    Production Agent - Handles production@h-bu.de
    Manages production schedules, capacity planning, and manufacturing coordination
    """

    def __init__(self, agent_id: str = "production-001"):
        super().__init__(agent_id, "production_agent", {
            'daily_capacity': 10000,  # buttons per day
            'shift_hours': 16,  # production hours per day
            'min_batch_size': 500,
            'max_batch_size': 5000,
            'quality_check_percentage': 5.0,
            'lead_time_days': 3
        })
        self.current_production_queue = []
        self.daily_production_target = self.config['daily_capacity']

    async def _process_email_impl(self, parsed_email: ParsedEmail,
                                 routing_decision: RoutingDecision,
                                 task: AgentTask) -> AgentResponse:
        """Process production-related emails"""

        production_analysis = await self._analyze_production_request(parsed_email)

        response_data = {
            'action': 'production_scheduled',
            'request_type': production_analysis['type'],
            'production_schedule': production_analysis['schedule'],
            'capacity_available': production_analysis['capacity_check'],
            'estimated_completion': production_analysis['completion_date']
        }

        coordination_notes = []

        # Handle different types of production requests
        if production_analysis['type'] == 'urgent_order':
            success = await self.send_task_email(
                to_agent='logistics_agent',
                task_type=TaskTypes.EXPEDITE_REQUEST,
                content=f"URGENT PRODUCTION REQUEST - PRIORITY HANDLING REQUIRED\n\nOrder Details:\n- Quantity: {production_analysis['quantity']} units\n- Product: {production_analysis['product_type']}\n- Customer: {production_analysis['customer']}\n- Deadline: {production_analysis['deadline']}\n\nProduction Status:\n- Capacity Available: {production_analysis['capacity_check']}\n- Estimated Completion: {production_analysis['completion_date']}\n- Quality Check Required: {production_analysis['quality_required']}\n\nPlease coordinate expedited shipping arrangements.",
                priority="critical",
                data={
                    'order_quantity': production_analysis['quantity'],
                    'product_type': production_analysis['product_type'],
                    'customer': production_analysis['customer'],
                    'deadline': production_analysis['deadline'],
                    'production_priority': 'urgent',
                    'shipping_expedite': True
                },
                due_hours=1
            )
            if success:
                coordination_notes.append("Sent urgent coordination to logistics")
            else:
                coordination_notes.append("Failed to coordinate with logistics")

        elif production_analysis['type'] == 'capacity_planning':
            success = await self.send_task_email(
                to_agent='management_agent',
                task_type=TaskTypes.CAPACITY_REPORT,
                content=f"Production Capacity Analysis Report\n\nCurrent Status:\n- Daily Capacity: {self.config['daily_capacity']} units\n- Current Queue: {len(self.current_production_queue)} orders\n- Capacity Utilization: {production_analysis['utilization']:.1f}%\n\nRequest Analysis:\n- Requested Quantity: {production_analysis['quantity']} units\n- Feasibility: {production_analysis['feasible']}\n- Required Additional Capacity: {production_analysis['additional_capacity_needed']} units/day\n\nRecommendations:\n{production_analysis['recommendations']}",
                priority="high",
                data={
                    'current_capacity': self.config['daily_capacity'],
                    'utilization_percentage': production_analysis['utilization'],
                    'feasible': production_analysis['feasible'],
                    'recommendations': production_analysis['recommendations']
                },
                due_hours=4
            )
            if success:
                coordination_notes.append("Sent capacity analysis to management")

        elif production_analysis['type'] == 'quality_issue':
            success = await self.send_task_email(
                to_agent='quality_agent',
                task_type=TaskTypes.QUALITY_INVESTIGATION,
                content=f"Production Quality Issue Detected\n\nIssue Details:\n- Batch ID: {production_analysis['batch_id']}\n- Product Type: {production_analysis['product_type']}\n- Issue Description: {production_analysis['issue_description']}\n- Affected Quantity: {production_analysis['affected_quantity']} units\n- Detection Time: {production_analysis['detection_time']}\n\nImmediate Actions Taken:\n- Production line halted for affected product\n- Batch quarantined pending investigation\n- Alternative production line activated\n\nRequired Actions:\n- Full quality investigation\n- Root cause analysis\n- Corrective action plan\n- Customer notification if shipped",
                priority="high",
                data={
                    'batch_id': production_analysis['batch_id'],
                    'issue_type': 'production_defect',
                    'affected_quantity': production_analysis['affected_quantity'],
                    'immediate_action_required': True
                },
                due_hours=2
            )
            if success:
                coordination_notes.append("Initiated quality investigation")

        elif production_analysis['type'] == 'material_shortage':
            success = await self.send_task_email(
                to_agent='purchasing_agent',
                task_type=TaskTypes.MATERIAL_REQUEST,
                content=f"URGENT MATERIAL SHORTAGE - PRODUCTION IMPACT\n\nShortage Details:\n- Material: {production_analysis['material_type']}\n- Current Stock: {production_analysis['current_stock']} units\n- Required for Production: {production_analysis['required_quantity']} units\n- Impact: Production halt in {production_analysis['halt_hours']} hours\n\nAffected Orders:\n- {production_analysis['affected_orders']} orders pending\n- Total Value: €{production_analysis['order_value']:,.2f}\n- Customer Impact: {production_analysis['customer_count']} customers\n\nUrgent procurement required to maintain production schedule.",
                priority="critical",
                data={
                    'material_type': production_analysis['material_type'],
                    'shortage_severity': 'critical',
                    'halt_hours': production_analysis['halt_hours'],
                    'affected_orders': production_analysis['affected_orders'],
                    'procurement_urgency': 'immediate'
                },
                due_hours=2
            )
            if success:
                coordination_notes.append("Sent urgent material request to purchasing")

        # Determine auto-reply based on request type
        auto_reply = self._select_production_reply(production_analysis)

        return AgentResponse(
            task_id=task.id,
            agent_id=self.agent_id,
            status="success",
            response_data=response_data,
            auto_reply=auto_reply,
            next_actions=self._determine_production_actions(production_analysis),
            coordination_notes=coordination_notes
        )

    async def _analyze_production_request(self, parsed_email: ParsedEmail) -> Dict[str, Any]:
        """Analyze production request and determine type and requirements"""
        content = f"{parsed_email.subject} {parsed_email.body}".lower()

        # Determine request type
        if any(word in content for word in ['urgent', 'rush', 'expedite', 'asap', 'emergency']):
            request_type = 'urgent_order'
        elif any(word in content for word in ['capacity', 'planning', 'forecast', 'volume']):
            request_type = 'capacity_planning'
        elif any(word in content for word in ['defect', 'quality', 'problem', 'issue', 'reject']):
            request_type = 'quality_issue'
        elif any(word in content for word in ['material', 'shortage', 'supply', 'stock']):
            request_type = 'material_shortage'
        elif any(word in content for word in ['schedule', 'timeline', 'delivery']):
            request_type = 'schedule_request'
        else:
            request_type = 'general_inquiry'

        # Extract quantity information
        qty_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*(?:pieces|pcs|units|buttons)', content)
        quantity = int(qty_match.group(1).replace(',', '')) if qty_match else 1000

        # Extract product type
        product_type = 'BTN-001'  # Default
        if 'blue' in content:
            product_type = 'BTN-002'
        elif 'premium' in content or 'royal' in content:
            product_type = 'BTN-003'

        # Calculate production schedule
        schedule_info = self._calculate_production_schedule(quantity, request_type)

        # Perform capacity check
        capacity_check = self._check_production_capacity(quantity)

        # Calculate completion date
        completion_date = self._estimate_completion_date(quantity, request_type)

        analysis = {
            'type': request_type,
            'quantity': quantity,
            'product_type': product_type,
            'customer': parsed_email.sender.email,
            'schedule': schedule_info,
            'capacity_check': capacity_check,
            'completion_date': completion_date,
            'feasible': capacity_check['available'],
            'utilization': capacity_check['utilization_percentage']
        }

        # Add type-specific analysis
        if request_type == 'urgent_order':
            analysis.update({
                'deadline': (datetime.now() + timedelta(hours=24)).isoformat(),
                'quality_required': True,
                'additional_capacity_needed': max(0, quantity - capacity_check['daily_available'])
            })
        elif request_type == 'quality_issue':
            analysis.update({
                'batch_id': f"BATCH-{datetime.now().strftime('%Y%m%d')}-{parsed_email.id[:6]}",
                'issue_description': 'Quality concern reported via email',
                'affected_quantity': min(quantity, 500),  # Estimate affected batch size
                'detection_time': datetime.now().isoformat()
            })
        elif request_type == 'material_shortage':
            analysis.update({
                'material_type': 'button_components',
                'current_stock': max(0, 1000 - quantity),  # Simulate stock
                'required_quantity': quantity,
                'halt_hours': 8,  # Hours until production stops
                'affected_orders': min(5, quantity // 1000),
                'order_value': quantity * 2.50,  # Estimate value
                'customer_count': min(3, quantity // 1500)
            })
        elif request_type == 'capacity_planning':
            analysis.update({
                'recommendations': self._generate_capacity_recommendations(quantity, capacity_check),
                'additional_capacity_needed': max(0, quantity - self.config['daily_capacity'])
            })

        return analysis

    def _calculate_production_schedule(self, quantity: int, request_type: str) -> Dict[str, Any]:
        """Calculate production schedule based on quantity and priority"""
        batch_size = min(max(quantity, self.config['min_batch_size']), self.config['max_batch_size'])
        num_batches = (quantity + batch_size - 1) // batch_size  # Ceiling division

        # Calculate production time
        if request_type == 'urgent_order':
            # Expedited production with overtime
            production_rate = self.config['daily_capacity'] * 1.5  # 150% capacity with overtime
            production_days = max(1, quantity / production_rate)
        else:
            # Normal production schedule
            production_rate = self.config['daily_capacity']
            production_days = max(1, quantity / production_rate)

        start_date = datetime.now() + timedelta(days=1)  # Start tomorrow
        end_date = start_date + timedelta(days=production_days)

        return {
            'batch_size': batch_size,
            'num_batches': num_batches,
            'production_days': round(production_days, 1),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'priority': 'high' if request_type == 'urgent_order' else 'normal'
        }

    def _check_production_capacity(self, quantity: int) -> Dict[str, Any]:
        """Check current production capacity and availability"""
        # Simulate current production load
        current_queue_size = len(self.current_production_queue) * 1000  # Estimate
        remaining_daily_capacity = max(0, self.config['daily_capacity'] - current_queue_size)

        utilization_percentage = (current_queue_size / self.config['daily_capacity']) * 100

        return {
            'daily_capacity': self.config['daily_capacity'],
            'current_queue': current_queue_size,
            'daily_available': remaining_daily_capacity,
            'utilization_percentage': min(100, utilization_percentage),
            'available': remaining_daily_capacity >= quantity or utilization_percentage < 90,
            'requires_overtime': quantity > remaining_daily_capacity,
            'requires_additional_shifts': quantity > self.config['daily_capacity']
        }

    def _estimate_completion_date(self, quantity: int, request_type: str) -> str:
        """Estimate production completion date"""
        base_lead_time = self.config['lead_time_days']

        if request_type == 'urgent_order':
            # Expedited processing
            lead_time = max(1, base_lead_time / 2)
        else:
            # Add buffer for large orders
            if quantity > self.config['daily_capacity']:
                lead_time = base_lead_time + (quantity / self.config['daily_capacity'])
            else:
                lead_time = base_lead_time

        completion_date = datetime.now() + timedelta(days=lead_time)
        return completion_date.isoformat()

    def _generate_capacity_recommendations(self, quantity: int, capacity_check: Dict) -> str:
        """Generate capacity planning recommendations"""
        recommendations = []

        if quantity > self.config['daily_capacity']:
            recommendations.append("Consider additional production shifts")
            recommendations.append("Evaluate equipment upgrades for higher throughput")

        if capacity_check['utilization_percentage'] > 85:
            recommendations.append("Current capacity utilization high - consider expansion")

        if capacity_check['requires_overtime']:
            recommendations.append("Overtime scheduling required for timely delivery")

        if not recommendations:
            recommendations.append("Current capacity sufficient for requested volume")

        return '\n'.join(f"- {rec}" for rec in recommendations)

    def _select_production_reply(self, analysis: Dict) -> str:
        """Select appropriate auto-reply template"""
        if analysis['type'] == 'urgent_order':
            return 'production_urgent_ack'
        elif analysis['type'] == 'quality_issue':
            return 'production_quality_ack'
        elif analysis['type'] == 'material_shortage':
            return 'production_shortage_ack'
        else:
            return 'production_ack'

    def _determine_production_actions(self, analysis: Dict) -> List[str]:
        """Determine next actions based on production analysis"""
        actions = []

        if analysis['type'] == 'urgent_order':
            actions.extend([
                "Schedule urgent production slot",
                "Coordinate with logistics for expedited shipping",
                "Monitor production progress hourly"
            ])
        elif analysis['type'] == 'capacity_planning':
            actions.extend([
                "Analyze current capacity utilization",
                "Prepare capacity expansion proposal",
                "Review production efficiency metrics"
            ])
        elif analysis['type'] == 'quality_issue':
            actions.extend([
                "Halt affected production line",
                "Quarantine affected batch",
                "Initiate quality investigation"
            ])
        elif analysis['type'] == 'material_shortage':
            actions.extend([
                "Request urgent material procurement",
                "Identify alternative suppliers",
                "Prepare production contingency plan"
            ])

        # Common actions
        actions.append(f"Add to production queue: {analysis['quantity']} units")
        if not analysis['feasible']:
            actions.append("Evaluate overtime or additional capacity options")

        return actions

    def get_agent_capabilities(self) -> Dict[str, Any]:
        return {
            'production_scheduling': True,
            'capacity_planning': True,
            'quality_coordination': True,
            'urgent_order_handling': True,
            'material_coordination': True,
            'batch_processing': True,
            'daily_capacity': self.config['daily_capacity'],
            'lead_time_days': self.config['lead_time_days']
        }

    def validate_email_for_agent(self, parsed_email: ParsedEmail) -> bool:
        content = f"{parsed_email.subject} {parsed_email.body}".lower()
        production_keywords = [
            'production', 'manufacturing', 'schedule', 'capacity',
            'batch', 'quality', 'defect', 'material', 'shortage'
        ]
        return any(keyword in content for keyword in production_keywords)


if __name__ == "__main__":
    # Test the production agent
    async def test_production_agent():
        agent = ProductionAgent()
        print(f"Production Agent: {agent.agent_id}")
        print(f"Capabilities: {agent.get_agent_capabilities()}")

    asyncio.run(test_production_agent())