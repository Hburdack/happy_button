"""
Logistics Agent for Happy Buttons Release 2
Handles shipping, inventory management, supply chain coordination, and delivery tracking
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


class LogisticsAgent(BaseAgent):
    """
    Logistics Agent - Handles logistics@h-bu.de
    Manages shipping, inventory, supply chain, and delivery coordination
    """

    def __init__(self, agent_id: str = "logistics-001"):
        super().__init__(agent_id, "logistics_agent", {
            'warehouse_capacity': 50000,  # units
            'current_inventory': 25000,   # simulated current stock
            'shipping_zones': ['EU', 'NA', 'ASIA'],
            'standard_delivery_days': 5,
            'expedite_delivery_days': 2,
            'inventory_threshold_low': 5000,
            'inventory_threshold_critical': 1000
        })
        self.active_shipments = {}
        self.pending_deliveries = []

    async def _process_email_impl(self, parsed_email: ParsedEmail,
                                 routing_decision: RoutingDecision,
                                 task: AgentTask) -> AgentResponse:
        """Process logistics-related emails"""

        logistics_analysis = await self._analyze_logistics_request(parsed_email)

        response_data = {
            'action': 'logistics_processed',
            'request_type': logistics_analysis['type'],
            'inventory_status': logistics_analysis['inventory_check'],
            'shipping_plan': logistics_analysis['shipping_plan'],
            'delivery_estimate': logistics_analysis['delivery_estimate']
        }

        coordination_notes = []

        # Handle different types of logistics requests
        if logistics_analysis['type'] == 'expedite_shipping':
            success = await self.send_task_email(
                to_agent='finance_agent',
                task_type=TaskTypes.COST_APPROVAL,
                content=f"EXPEDITED SHIPPING COST APPROVAL REQUIRED\n\nShipment Details:\n- Order: {logistics_analysis['order_id']}\n- Destination: {logistics_analysis['destination']}\n- Weight: {logistics_analysis['weight']} kg\n- Standard Cost: €{logistics_analysis['standard_cost']:.2f}\n- Expedited Cost: €{logistics_analysis['expedited_cost']:.2f}\n- Additional Cost: €{logistics_analysis['additional_cost']:.2f}\n\nCustomer: {logistics_analysis['customer']}\nReason: {logistics_analysis['expedite_reason']}\nDelivery Time: {logistics_analysis['delivery_days']} days vs standard {self.config['standard_delivery_days']} days\n\nCustomer has agreed to expedited shipping charges.",
                priority="high",
                data={
                    'cost_type': 'expedited_shipping',
                    'additional_cost': logistics_analysis['additional_cost'],
                    'customer': logistics_analysis['customer'],
                    'order_id': logistics_analysis['order_id']
                },
                due_hours=2
            )
            if success:
                coordination_notes.append("Sent expedite cost approval to finance")

            # Coordinate with carrier
            success = await self.send_task_email(
                to_agent='logistics_agent',  # Self-notification for tracking
                task_type=TaskTypes.CARRIER_COORDINATION,
                content=f"Arrange expedited shipping pickup within 4 hours. Order {logistics_analysis['order_id']} for {logistics_analysis['customer']}. Destination: {logistics_analysis['destination']}.",
                priority="high",
                data={
                    'pickup_urgency': 'within_4_hours',
                    'shipping_type': 'expedited',
                    'order_id': logistics_analysis['order_id']
                },
                due_hours=1
            )

        elif logistics_analysis['type'] == 'inventory_check':
            # Check if inventory is sufficient
            if not logistics_analysis['inventory_sufficient']:
                success = await self.send_task_email(
                    to_agent='purchasing_agent',
                    task_type=TaskTypes.PROCUREMENT_REQUEST,
                    content=f"INVENTORY SHORTAGE - URGENT RESTOCKING REQUIRED\n\nProduct: {logistics_analysis['product_type']}\nCurrent Stock: {logistics_analysis['current_stock']} units\nRequired: {logistics_analysis['required_quantity']} units\nShortfall: {logistics_analysis['shortfall']} units\n\nOrders Affected:\n- Pending Orders: {logistics_analysis['affected_orders']}\n- Customer Impact: {logistics_analysis['customer_count']} customers\n- Revenue at Risk: €{logistics_analysis['revenue_risk']:,.2f}\n\nStock-out Date: {logistics_analysis['stockout_date']}\nUrgent procurement required to fulfill pending orders.",
                    priority="critical",
                    data={
                        'product_type': logistics_analysis['product_type'],
                        'shortfall_quantity': logistics_analysis['shortfall'],
                        'stockout_risk': 'high',
                        'procurement_urgency': 'critical'
                    },
                    due_hours=4
                )
                if success:
                    coordination_notes.append("Sent urgent restocking request to purchasing")

            # Coordinate with production
            success = await self.send_task_email(
                to_agent='production_agent',
                task_type=TaskTypes.PRODUCTION_COORDINATION,
                content=f"Inventory Status Update for Production Planning\n\nProduct: {logistics_analysis['product_type']}\nCurrent Inventory: {logistics_analysis['current_stock']} units\nPending Orders: {logistics_analysis['pending_orders']} units\nAvailable for New Orders: {logistics_analysis['available_inventory']} units\n\nProduction Recommendations:\n- {logistics_analysis['production_recommendation']}\n- Priority Level: {logistics_analysis['production_priority']}\n- Suggested Batch Size: {logistics_analysis['suggested_batch_size']} units",
                priority="medium",
                data={
                    'inventory_level': logistics_analysis['current_stock'],
                    'pending_demand': logistics_analysis['pending_orders'],
                    'production_priority': logistics_analysis['production_priority']
                },
                due_hours=8
            )
            if success:
                coordination_notes.append("Coordinated inventory status with production")

        elif logistics_analysis['type'] == 'delivery_tracking':
            # Update customer on delivery status
            tracking_info = logistics_analysis['tracking_info']
            if tracking_info['status'] == 'delayed':
                success = await self.send_task_email(
                    to_agent='info_agent',
                    task_type=TaskTypes.CUSTOMER_NOTIFICATION,
                    content=f"Customer Notification Required - Delivery Delay\n\nOrder: {logistics_analysis['order_id']}\nCustomer: {logistics_analysis['customer']}\nOriginal Delivery Date: {tracking_info['original_date']}\nNew Delivery Date: {tracking_info['new_date']}\nDelay Reason: {tracking_info['delay_reason']}\n\nCustomer should be proactively notified of delay and provided updated tracking information.",
                    priority="medium",
                    data={
                        'notification_type': 'delivery_delay',
                        'order_id': logistics_analysis['order_id'],
                        'delay_days': tracking_info['delay_days']
                    },
                    due_hours=2
                )
                if success:
                    coordination_notes.append("Requested customer notification for delivery delay")

        elif logistics_analysis['type'] == 'supply_chain_disruption':
            success = await self.send_task_email(
                to_agent='management_agent',
                task_type=TaskTypes.ESCALATION,
                content=f"SUPPLY CHAIN DISRUPTION - MANAGEMENT ATTENTION REQUIRED\n\nDisruption Type: {logistics_analysis['disruption_type']}\nImpact Level: {logistics_analysis['impact_level']}\nAffected Region: {logistics_analysis['affected_region']}\nExpected Duration: {logistics_analysis['duration']}\n\nImpact Assessment:\n- Delayed Shipments: {logistics_analysis['delayed_shipments']}\n- Affected Customers: {logistics_analysis['affected_customers']}\n- Revenue Impact: €{logistics_analysis['revenue_impact']:,.2f}\n- Alternative Routes: {logistics_analysis['alternative_routes']}\n\nMitigation Plan:\n{logistics_analysis['mitigation_plan']}",
                priority="critical",
                data={
                    'disruption_type': logistics_analysis['disruption_type'],
                    'impact_level': logistics_analysis['impact_level'],
                    'requires_executive_decision': True
                },
                due_hours=1
            )
            if success:
                coordination_notes.append("Escalated supply chain disruption to management")

        # Determine auto-reply
        auto_reply = self._select_logistics_reply(logistics_analysis)

        return AgentResponse(
            task_id=task.id,
            agent_id=self.agent_id,
            status="success",
            response_data=response_data,
            auto_reply=auto_reply,
            next_actions=self._determine_logistics_actions(logistics_analysis),
            coordination_notes=coordination_notes
        )

    async def _analyze_logistics_request(self, parsed_email: ParsedEmail) -> Dict[str, Any]:
        """Analyze logistics request and determine type and requirements"""
        content = f"{parsed_email.subject} {parsed_email.body}".lower()

        # Determine request type
        if any(word in content for word in ['expedite', 'rush', 'urgent', 'asap', 'emergency']):
            request_type = 'expedite_shipping'
        elif any(word in content for word in ['inventory', 'stock', 'availability', 'check']):
            request_type = 'inventory_check'
        elif any(word in content for word in ['tracking', 'delivery', 'shipment', 'status']):
            request_type = 'delivery_tracking'
        elif any(word in content for word in ['disruption', 'delay', 'suez', 'blocked', 'problem']):
            request_type = 'supply_chain_disruption'
        elif any(word in content for word in ['warehouse', 'storage', 'space']):
            request_type = 'warehouse_management'
        else:
            request_type = 'general_inquiry'

        # Extract common information
        qty_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*(?:pieces|pcs|units|buttons)', content)
        quantity = int(qty_match.group(1).replace(',', '')) if qty_match else 1000

        order_match = re.search(r'(?:order|po)\s*#?\s*(\w+)', content, re.IGNORECASE)
        order_id = order_match.group(1) if order_match else f"ORD-{datetime.now().strftime('%Y%m%d')}-{parsed_email.id[:6]}"

        # Base analysis
        analysis = {
            'type': request_type,
            'quantity': quantity,
            'order_id': order_id,
            'customer': parsed_email.sender.email,
            'customer_domain': parsed_email.sender.domain
        }

        # Add type-specific analysis
        if request_type == 'expedite_shipping':
            analysis.update(self._analyze_expedite_request(content, quantity, order_id))
        elif request_type == 'inventory_check':
            analysis.update(self._analyze_inventory_request(content, quantity))
        elif request_type == 'delivery_tracking':
            analysis.update(self._analyze_tracking_request(content, order_id))
        elif request_type == 'supply_chain_disruption':
            analysis.update(self._analyze_disruption_request(content))

        return analysis

    def _analyze_expedite_request(self, content: str, quantity: int, order_id: str) -> Dict[str, Any]:
        """Analyze expedited shipping request"""
        # Determine destination zone
        destination = 'EU'  # Default
        if any(word in content for word in ['usa', 'america', 'us']):
            destination = 'NA'
        elif any(word in content for word in ['asia', 'china', 'japan']):
            destination = 'ASIA'

        # Calculate shipping costs
        weight = quantity * 0.05  # 50g per button
        standard_cost = weight * 2.0  # €2 per kg standard
        expedited_cost = weight * 8.0  # €8 per kg expedited
        additional_cost = expedited_cost - standard_cost

        # Determine expedite reason
        if 'emergency' in content:
            expedite_reason = 'Customer emergency requirement'
        elif 'production' in content:
            expedite_reason = 'Production deadline requirement'
        else:
            expedite_reason = 'Customer request for faster delivery'

        return {
            'destination': destination,
            'weight': weight,
            'standard_cost': standard_cost,
            'expedited_cost': expedited_cost,
            'additional_cost': additional_cost,
            'delivery_days': self.config['expedite_delivery_days'],
            'expedite_reason': expedite_reason,
            'shipping_plan': {
                'carrier': 'DHL Express',
                'service_level': 'Express',
                'pickup_time': 'Within 4 hours',
                'delivery_guarantee': f"{self.config['expedite_delivery_days']} business days"
            },
            'delivery_estimate': (datetime.now() + timedelta(days=self.config['expedite_delivery_days'])).isoformat()
        }

    def _analyze_inventory_request(self, content: str, quantity: int) -> Dict[str, Any]:
        """Analyze inventory availability request"""
        # Simulate product-specific inventory
        product_type = 'BTN-001'  # Default
        if 'blue' in content:
            product_type = 'BTN-002'
        elif 'premium' in content or 'royal' in content:
            product_type = 'BTN-003'

        # Simulate current stock (would come from actual inventory system)
        base_stock = self.config['current_inventory']
        current_stock = max(0, base_stock - (hash(product_type) % 5000))  # Simulate variance

        # Check if sufficient inventory
        inventory_sufficient = current_stock >= quantity
        shortfall = max(0, quantity - current_stock)

        # Calculate affected orders and risk
        affected_orders = min(10, shortfall // 500)  # Estimate affected orders
        customer_count = min(5, affected_orders)
        revenue_risk = shortfall * 2.50  # €2.50 per button average

        # Determine stockout date
        daily_consumption = 500  # Estimate daily usage
        days_until_stockout = current_stock / daily_consumption if current_stock > 0 else 0
        stockout_date = (datetime.now() + timedelta(days=days_until_stockout)).date().isoformat()

        # Production recommendations
        if current_stock < self.config['inventory_threshold_critical']:
            production_priority = 'critical'
            production_recommendation = 'Immediate production required - critical stock level'
            suggested_batch_size = max(5000, shortfall)
        elif current_stock < self.config['inventory_threshold_low']:
            production_priority = 'high'
            production_recommendation = 'Production should be scheduled within 2 days'
            suggested_batch_size = max(3000, shortfall)
        else:
            production_priority = 'medium'
            production_recommendation = 'Normal production schedule sufficient'
            suggested_batch_size = 2000

        return {
            'product_type': product_type,
            'current_stock': current_stock,
            'required_quantity': quantity,
            'inventory_sufficient': inventory_sufficient,
            'shortfall': shortfall,
            'affected_orders': affected_orders,
            'customer_count': customer_count,
            'revenue_risk': revenue_risk,
            'stockout_date': stockout_date,
            'pending_orders': quantity + (affected_orders * 500),
            'available_inventory': max(0, current_stock - quantity),
            'production_recommendation': production_recommendation,
            'production_priority': production_priority,
            'suggested_batch_size': suggested_batch_size,
            'inventory_check': {
                'status': 'sufficient' if inventory_sufficient else 'insufficient',
                'current_level': current_stock,
                'threshold_status': self._get_inventory_threshold_status(current_stock)
            },
            'shipping_plan': {
                'available_quantity': min(current_stock, quantity),
                'ship_immediately': inventory_sufficient,
                'partial_shipment': not inventory_sufficient and current_stock > 0
            },
            'delivery_estimate': (datetime.now() + timedelta(days=self.config['standard_delivery_days'])).isoformat() if inventory_sufficient else None
        }

    def _analyze_tracking_request(self, content: str, order_id: str) -> Dict[str, Any]:
        """Analyze delivery tracking request"""
        # Simulate tracking information
        import random

        tracking_statuses = ['in_transit', 'delivered', 'delayed', 'processing']
        status = random.choice(tracking_statuses)

        if status == 'delayed':
            original_date = (datetime.now() + timedelta(days=self.config['standard_delivery_days'])).date()
            delay_days = random.randint(1, 3)
            new_date = original_date + timedelta(days=delay_days)
            delay_reasons = ['Weather conditions', 'Carrier capacity issues', 'Customs delay', 'Traffic disruption']
            delay_reason = random.choice(delay_reasons)

            tracking_info = {
                'status': status,
                'original_date': original_date.isoformat(),
                'new_date': new_date.isoformat(),
                'delay_days': delay_days,
                'delay_reason': delay_reason
            }
        else:
            tracking_info = {
                'status': status,
                'estimated_delivery': (datetime.now() + timedelta(days=self.config['standard_delivery_days'])).date().isoformat(),
                'current_location': 'Distribution Center'
            }

        return {
            'tracking_info': tracking_info,
            'shipping_plan': {
                'tracking_number': f"TRK-{order_id}-{datetime.now().strftime('%Y%m%d')}",
                'carrier': 'Standard Carrier',
                'last_update': datetime.now().isoformat()
            },
            'delivery_estimate': tracking_info.get('new_date') or tracking_info.get('estimated_delivery')
        }

    def _analyze_disruption_request(self, content: str) -> Dict[str, Any]:
        """Analyze supply chain disruption"""
        # Determine disruption type
        if 'suez' in content:
            disruption_type = 'Suez Canal Blockage'
            impact_level = 'critical'
            affected_region = 'Global shipping routes'
            duration = '1-2 weeks'
        elif 'weather' in content:
            disruption_type = 'Severe Weather'
            impact_level = 'high'
            affected_region = 'Regional'
            duration = '3-5 days'
        else:
            disruption_type = 'Logistics Network Issue'
            impact_level = 'medium'
            affected_region = 'Local'
            duration = '1-2 days'

        # Calculate impact
        delayed_shipments = 15 if impact_level == 'critical' else 8 if impact_level == 'high' else 3
        affected_customers = min(10, delayed_shipments)
        revenue_impact = delayed_shipments * 2500  # Average order value

        # Alternative routes
        alternative_routes = 'Air freight available' if impact_level == 'critical' else 'Alternative ground routes identified'

        # Mitigation plan
        mitigation_steps = [
            'Activate alternative shipping routes',
            'Contact affected customers proactively',
            'Coordinate with backup carriers',
            'Monitor situation hourly'
        ]

        return {
            'disruption_type': disruption_type,
            'impact_level': impact_level,
            'affected_region': affected_region,
            'duration': duration,
            'delayed_shipments': delayed_shipments,
            'affected_customers': affected_customers,
            'revenue_impact': revenue_impact,
            'alternative_routes': alternative_routes,
            'mitigation_plan': '\n'.join(f"- {step}" for step in mitigation_steps),
            'shipping_plan': {
                'contingency_activated': True,
                'alternative_carrier': 'Emergency Logistics Partner',
                'additional_cost_impact': '25% increase in shipping costs'
            },
            'delivery_estimate': (datetime.now() + timedelta(days=7)).isoformat()  # Extended timeline
        }

    def _get_inventory_threshold_status(self, current_stock: int) -> str:
        """Get inventory threshold status"""
        if current_stock <= self.config['inventory_threshold_critical']:
            return 'critical'
        elif current_stock <= self.config['inventory_threshold_low']:
            return 'low'
        else:
            return 'normal'

    def _select_logistics_reply(self, analysis: Dict) -> str:
        """Select appropriate auto-reply template"""
        if analysis['type'] == 'expedite_shipping':
            return 'logistics_expedite_ack'
        elif analysis['type'] == 'inventory_check':
            return 'logistics_inventory_ack'
        elif analysis['type'] == 'delivery_tracking':
            return 'logistics_tracking_ack'
        elif analysis['type'] == 'supply_chain_disruption':
            return 'logistics_disruption_ack'
        else:
            return 'logistics_ack'

    def _determine_logistics_actions(self, analysis: Dict) -> List[str]:
        """Determine next actions based on logistics analysis"""
        actions = []

        if analysis['type'] == 'expedite_shipping':
            actions.extend([
                "Arrange expedited carrier pickup",
                "Generate expedited shipping label",
                "Send tracking information to customer"
            ])
        elif analysis['type'] == 'inventory_check':
            if not analysis.get('inventory_sufficient', True):
                actions.extend([
                    "Request urgent production scheduling",
                    "Consider partial shipment if possible",
                    "Alert customer of potential delay"
                ])
            else:
                actions.append("Confirm inventory allocation for order")
        elif analysis['type'] == 'delivery_tracking':
            actions.extend([
                "Provide detailed tracking information",
                "Monitor shipment progress",
                "Update customer on any status changes"
            ])
        elif analysis['type'] == 'supply_chain_disruption':
            actions.extend([
                "Activate contingency shipping plans",
                "Communicate with affected customers",
                "Monitor alternative route availability"
            ])

        # Common actions
        actions.append("Update logistics database")
        if analysis.get('delivery_estimate'):
            actions.append("Communicate delivery timeline to customer")

        return actions

    def get_agent_capabilities(self) -> Dict[str, Any]:
        return {
            'shipping_coordination': True,
            'inventory_management': True,
            'supply_chain_optimization': True,
            'expedited_shipping': True,
            'delivery_tracking': True,
            'warehouse_management': True,
            'disruption_management': True,
            'warehouse_capacity': self.config['warehouse_capacity'],
            'shipping_zones': self.config['shipping_zones'],
            'standard_delivery_days': self.config['standard_delivery_days'],
            'expedite_delivery_days': self.config['expedite_delivery_days']
        }

    def validate_email_for_agent(self, parsed_email: ParsedEmail) -> bool:
        content = f"{parsed_email.subject} {parsed_email.body}".lower()
        logistics_keywords = [
            'shipping', 'delivery', 'logistics', 'inventory', 'stock',
            'tracking', 'expedite', 'warehouse', 'supply', 'disruption'
        ]
        return any(keyword in content for keyword in logistics_keywords)


if __name__ == "__main__":
    # Test the logistics agent
    async def test_logistics_agent():
        agent = LogisticsAgent()
        print(f"Logistics Agent: {agent.agent_id}")
        print(f"Capabilities: {agent.get_agent_capabilities()}")

    asyncio.run(test_logistics_agent())