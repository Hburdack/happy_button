"""
Purchasing Agent for Happy Buttons Release 2
Handles procurement, supplier management, inventory restocking, and purchase approvals
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


class PurchasingAgent(BaseAgent):
    """
    Purchasing Agent - Handles purchasing@h-bu.de
    Manages procurement, supplier relationships, inventory restocking, and purchase approvals
    """

    def __init__(self, agent_id: str = "purchasing-001"):
        super().__init__(agent_id, "purchasing_agent", {
            'auto_approve_threshold': 2500,  # Auto-approve purchases under €2500
            'management_approval_threshold': 15000,  # Require management approval over €15000
            'emergency_procurement_threshold': 5000,  # Emergency procurement limit
            'preferred_suppliers': {
                'button_components': ['ComponentSupply Co', 'ButtonTech Industries', 'Premium Parts Ltd'],
                'packaging': ['PackagePro', 'EcoPackaging Solutions'],
                'equipment': ['MachineWorks', 'Industrial Equipment Inc'],
                'materials': ['RawMaterials Direct', 'Quality Materials Co']
            },
            'standard_lead_times': {
                'button_components': 7,  # days
                'packaging': 3,
                'equipment': 21,
                'materials': 5
            },
            'inventory_reorder_points': {
                'BTN-001': 5000,
                'BTN-002': 3000,
                'BTN-003': 2000,
                'packaging': 10000
            }
        })
        self.active_purchases = {}
        self.supplier_performance = self._initialize_supplier_data()

    def _initialize_supplier_data(self):
        """Initialize supplier performance tracking"""
        return {
            'ComponentSupply Co': {'rating': 4.2, 'on_time_delivery': 92, 'quality_score': 88},
            'ButtonTech Industries': {'rating': 4.5, 'on_time_delivery': 95, 'quality_score': 94},
            'Premium Parts Ltd': {'rating': 4.0, 'on_time_delivery': 89, 'quality_score': 91},
            'PackagePro': {'rating': 4.3, 'on_time_delivery': 96, 'quality_score': 90},
            'EcoPackaging Solutions': {'rating': 4.1, 'on_time_delivery': 88, 'quality_score': 85}
        }

    async def _process_email_impl(self, parsed_email: ParsedEmail,
                                 routing_decision: RoutingDecision,
                                 task: AgentTask) -> AgentResponse:
        """Process purchasing-related emails"""

        purchasing_analysis = await self._analyze_purchasing_request(parsed_email)

        response_data = {
            'action': 'purchasing_processed',
            'request_type': purchasing_analysis['type'],
            'procurement_plan': purchasing_analysis.get('procurement_plan', {}),
            'approval_status': purchasing_analysis['approval_status'],
            'cost_estimate': purchasing_analysis.get('cost_estimate', 0)
        }

        coordination_notes = []

        # Handle different types of purchasing requests
        if purchasing_analysis['type'] == 'urgent_procurement':
            procurement_data = purchasing_analysis['procurement_data']

            # Coordinate with finance for emergency approval
            success = await self.send_task_email(
                to_agent='finance_agent',
                task_type=TaskTypes.EMERGENCY_APPROVAL,
                content=f"URGENT PROCUREMENT REQUEST - EMERGENCY APPROVAL NEEDED\n\nMaterial: {procurement_data['material_type']}\nQuantity: {procurement_data['quantity']:,} units\nEstimated Cost: €{procurement_data['estimated_cost']:,.2f}\nUrgency: {procurement_data['urgency_level']}\nSupplier: {procurement_data['recommended_supplier']}\n\nBusiness Impact:\n- Production Halt Risk: {procurement_data['halt_risk']}\n- Affected Orders: {procurement_data['affected_orders']}\n- Customer Impact: {procurement_data['customer_impact']}\n- Revenue at Risk: €{procurement_data['revenue_risk']:,.2f}\n\nDelivery Timeline: {procurement_data['delivery_timeline']}\nPayment Terms: {procurement_data['payment_terms']}\n\nEmergency procurement approval required to prevent production disruption.",
                priority="critical",
                data={
                    'procurement_type': 'emergency',
                    'cost': procurement_data['estimated_cost'],
                    'material': procurement_data['material_type'],
                    'urgency': procurement_data['urgency_level']
                },
                due_hours=2
            )
            if success:
                coordination_notes.append("Sent emergency procurement approval to finance")

            # Coordinate with production on timeline
            success = await self.send_task_email(
                to_agent='production_agent',
                task_type=TaskTypes.MATERIAL_UPDATE,
                content=f"Emergency Material Procurement Update\n\nMaterial: {procurement_data['material_type']}\nQuantity: {procurement_data['quantity']:,} units\nExpected Delivery: {procurement_data['delivery_date']}\nSupplier: {procurement_data['recommended_supplier']}\n\nProduction Planning:\n- Material arrival: {procurement_data['delivery_timeline']}\n- Quality inspection: {procurement_data['inspection_time']}\n- Available for production: {procurement_data['production_ready_date']}\n\nPlease adjust production schedule accordingly and prepare for material receipt.",
                priority="high",
                data={
                    'material_type': procurement_data['material_type'],
                    'delivery_date': procurement_data['delivery_date'],
                    'quantity': procurement_data['quantity']
                },
                due_hours=4
            )
            if success:
                coordination_notes.append("Updated production on material procurement timeline")

        elif purchasing_analysis['type'] == 'supplier_evaluation':
            supplier_data = purchasing_analysis['supplier_data']

            success = await self.send_task_email(
                to_agent='quality_agent',
                task_type=TaskTypes.SUPPLIER_AUDIT,
                content=f"New Supplier Quality Evaluation Required\n\nSupplier: {supplier_data['supplier_name']}\nMaterials: {supplier_data['materials_offered']}\nEvaluation Type: {supplier_data['evaluation_type']}\nProposed Pricing: €{supplier_data['pricing_estimate']:,.2f}\n\nQuality Requirements:\n- ISO Certifications: {supplier_data['certifications_required']}\n- Quality Standards: {supplier_data['quality_standards']}\n- Testing Requirements: {supplier_data['testing_requirements']}\n\nEvaluation Timeline:\n- Initial Assessment: {supplier_data['assessment_timeline']}\n- Sample Testing: {supplier_data['testing_timeline']}\n- Final Decision: {supplier_data['decision_timeline']}\n\nPlease conduct comprehensive quality evaluation and provide recommendation.",
                priority="medium",
                data={
                    'supplier': supplier_data['supplier_name'],
                    'evaluation_type': supplier_data['evaluation_type'],
                    'materials': supplier_data['materials_offered']
                },
                due_hours=72
            )
            if success:
                coordination_notes.append("Requested supplier quality evaluation")

        elif purchasing_analysis['type'] == 'inventory_restocking':
            inventory_data = purchasing_analysis['inventory_data']

            # Coordinate with logistics on inventory levels
            success = await self.send_task_email(
                to_agent='logistics_agent',
                task_type=TaskTypes.INVENTORY_COORDINATION,
                content=f"Inventory Restocking Coordination\n\nMaterials Being Ordered:\n{inventory_data['order_summary']}\n\nDelivery Schedule:\n{inventory_data['delivery_schedule']}\n\nWarehouse Preparation:\n- Total Volume: {inventory_data['total_volume']} m³\n- Unloading Requirements: {inventory_data['unloading_requirements']}\n- Storage Location: {inventory_data['storage_location']}\n- Quality Inspection Space: {inventory_data['inspection_requirements']}\n\nPlease prepare warehouse for incoming materials and coordinate receiving schedule.",
                priority="medium",
                data={
                    'delivery_volume': inventory_data['total_volume'],
                    'materials_incoming': inventory_data['material_types'],
                    'delivery_timeline': inventory_data['delivery_schedule']
                },
                due_hours=48
            )
            if success:
                coordination_notes.append("Coordinated inventory restocking with logistics")

        elif purchasing_analysis['type'] == 'cost_analysis':
            cost_data = purchasing_analysis['cost_data']

            success = await self.send_task_email(
                to_agent='finance_agent',
                task_type=TaskTypes.COST_ANALYSIS,
                content=f"Procurement Cost Analysis Report\n\nAnalysis Period: {cost_data['analysis_period']}\nTotal Procurement Spend: €{cost_data['total_spend']:,.2f}\nBudget Utilization: {cost_data['budget_utilization']:.1f}%\nCost Variance: €{cost_data['cost_variance']:,.2f} ({cost_data['variance_percentage']:+.1f}%)\n\nSupplier Breakdown:\n{cost_data['supplier_breakdown']}\n\nCost Optimization Opportunities:\n{cost_data['optimization_opportunities']}\n\nRecommendations:\n{cost_data['recommendations']}\n\nNext Period Budget Forecast: €{cost_data['budget_forecast']:,.2f}",
                priority="low",
                data={
                    'analysis_type': 'procurement_costs',
                    'total_spend': cost_data['total_spend'],
                    'budget_utilization': cost_data['budget_utilization']
                },
                due_hours=168  # 1 week
            )
            if success:
                coordination_notes.append("Sent procurement cost analysis to finance")

        elif purchasing_analysis['type'] == 'contract_negotiation':
            contract_data = purchasing_analysis['contract_data']

            if contract_data['value'] > self.config['management_approval_threshold']:
                success = await self.send_task_email(
                    to_agent='management_agent',
                    task_type=TaskTypes.CONTRACT_APPROVAL,
                    content=f"HIGH-VALUE CONTRACT NEGOTIATION APPROVAL\n\nSupplier: {contract_data['supplier']}\nContract Type: {contract_data['contract_type']}\nContract Value: €{contract_data['value']:,.2f}\nDuration: {contract_data['duration']}\nMaterials: {contract_data['materials']}\n\nNegotiation Summary:\n{contract_data['negotiation_summary']}\n\nKey Terms:\n{contract_data['key_terms']}\n\nRisk Assessment:\n{contract_data['risk_assessment']}\n\nRecommendation: {contract_data['recommendation']}\n\nManagement approval required for contract exceeding €{self.config['management_approval_threshold']:,} threshold.",
                    priority="high",
                    data={
                        'contract_value': contract_data['value'],
                        'supplier': contract_data['supplier'],
                        'contract_type': contract_data['contract_type']
                    },
                    due_hours=72
                )
                if success:
                    coordination_notes.append("Sent contract approval request to management")

        # Determine auto-reply
        auto_reply = self._select_purchasing_reply(purchasing_analysis)

        return AgentResponse(
            task_id=task.id,
            agent_id=self.agent_id,
            status="success",
            response_data=response_data,
            auto_reply=auto_reply,
            next_actions=self._determine_purchasing_actions(purchasing_analysis),
            coordination_notes=coordination_notes
        )

    async def _analyze_purchasing_request(self, parsed_email: ParsedEmail) -> Dict[str, Any]:
        """Analyze purchasing request and determine type and requirements"""
        content = f"{parsed_email.subject} {parsed_email.body}".lower()

        # Determine request type
        if any(word in content for word in ['urgent', 'emergency', 'shortage', 'halt', 'immediate']):
            request_type = 'urgent_procurement'
        elif any(word in content for word in ['supplier', 'vendor', 'evaluation', 'quote', 'rfq']):
            request_type = 'supplier_evaluation'
        elif any(word in content for word in ['inventory', 'restock', 'reorder', 'stock', 'material']):
            request_type = 'inventory_restocking'
        elif any(word in content for word in ['cost', 'analysis', 'report', 'budget', 'spend']):
            request_type = 'cost_analysis'
        elif any(word in content for word in ['contract', 'agreement', 'negotiation', 'terms']):
            request_type = 'contract_negotiation'
        elif any(word in content for word in ['approval', 'purchase', 'buy', 'order']):
            request_type = 'purchase_approval'
        else:
            request_type = 'general_inquiry'

        # Base analysis
        analysis = {
            'type': request_type,
            'requester': parsed_email.sender.email,
            'timestamp': datetime.now().isoformat()
        }

        # Add type-specific analysis
        if request_type == 'urgent_procurement':
            analysis.update(self._analyze_urgent_procurement(content))
        elif request_type == 'supplier_evaluation':
            analysis.update(self._analyze_supplier_evaluation(content))
        elif request_type == 'inventory_restocking':
            analysis.update(self._analyze_inventory_restocking(content))
        elif request_type == 'cost_analysis':
            analysis.update(self._analyze_cost_analysis(content))
        elif request_type == 'contract_negotiation':
            analysis.update(self._analyze_contract_negotiation(content))
        elif request_type == 'purchase_approval':
            analysis.update(self._analyze_purchase_approval(content))

        return analysis

    def _analyze_urgent_procurement(self, content: str) -> Dict[str, Any]:
        """Analyze urgent procurement request"""
        # Extract quantity
        qty_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*(?:pieces|units|kg|tons)', content)
        quantity = int(qty_match.group(1).replace(',', '')) if qty_match else 5000

        # Determine material type
        material_type = 'button_components'
        if 'packaging' in content:
            material_type = 'packaging'
        elif 'equipment' in content or 'machine' in content:
            material_type = 'equipment'
        elif 'raw' in content or 'material' in content:
            material_type = 'materials'

        # Estimate cost
        cost_per_unit = {'button_components': 0.15, 'packaging': 0.05, 'equipment': 1000, 'materials': 0.25}
        estimated_cost = quantity * cost_per_unit.get(material_type, 0.20)

        # Determine urgency level
        if any(word in content for word in ['emergency', 'halt', 'immediate']):
            urgency_level = 'critical'
            delivery_timeline = '24-48 hours'
        elif 'urgent' in content:
            urgency_level = 'high'
            delivery_timeline = '2-3 days'
        else:
            urgency_level = 'medium'
            delivery_timeline = '3-5 days'

        # Select supplier
        suppliers = self.config['preferred_suppliers'].get(material_type, ['General Supplier'])
        recommended_supplier = max(suppliers, key=lambda s: self.supplier_performance.get(s, {}).get('rating', 3.0))

        # Calculate business impact
        affected_orders = min(10, quantity // 500)
        revenue_risk = affected_orders * 2500  # Average order value

        delivery_date = (datetime.now() + timedelta(days=2 if urgency_level == 'critical' else 5)).date().isoformat()
        production_ready_date = (datetime.now() + timedelta(days=3 if urgency_level == 'critical' else 6)).date().isoformat()

        procurement_data = {
            'material_type': material_type,
            'quantity': quantity,
            'estimated_cost': estimated_cost,
            'urgency_level': urgency_level,
            'recommended_supplier': recommended_supplier,
            'delivery_timeline': delivery_timeline,
            'delivery_date': delivery_date,
            'production_ready_date': production_ready_date,
            'halt_risk': 'high' if urgency_level == 'critical' else 'medium',
            'affected_orders': affected_orders,
            'customer_impact': f'{affected_orders} orders at risk',
            'revenue_risk': revenue_risk,
            'payment_terms': 'Net 15' if urgency_level == 'critical' else 'Net 30',
            'inspection_time': '4 hours'
        }

        return {
            'procurement_data': procurement_data,
            'approval_status': 'pending_emergency' if estimated_cost > self.config['emergency_procurement_threshold'] else 'auto_approved',
            'cost_estimate': estimated_cost
        }

    def _analyze_supplier_evaluation(self, content: str) -> Dict[str, Any]:
        """Analyze supplier evaluation request"""
        # Extract supplier information
        supplier_match = re.search(r'supplier[:\s]+([A-Za-z\s&]+)', content, re.IGNORECASE)
        supplier_name = supplier_match.group(1).strip() if supplier_match else 'New Supplier Co'

        # Determine materials offered
        materials_offered = []
        if 'button' in content or 'component' in content:
            materials_offered.append('Button Components')
        if 'packaging' in content:
            materials_offered.append('Packaging Materials')
        if 'equipment' in content:
            materials_offered.append('Equipment')
        if not materials_offered:
            materials_offered = ['General Materials']

        # Determine evaluation type
        if 'new' in content:
            evaluation_type = 'new_supplier'
        elif 'alternative' in content:
            evaluation_type = 'alternative_supplier'
        else:
            evaluation_type = 'supplier_assessment'

        # Estimate pricing
        pricing_estimate = 25000 if 'equipment' in materials_offered[0].lower() else 15000

        # Generate timeline
        assessment_timeline = '1 week'
        testing_timeline = '2 weeks'
        decision_timeline = '1 month'

        supplier_data = {
            'supplier_name': supplier_name,
            'materials_offered': ', '.join(materials_offered),
            'evaluation_type': evaluation_type,
            'pricing_estimate': pricing_estimate,
            'certifications_required': 'ISO 9001, ISO 14001',
            'quality_standards': 'Company quality specifications',
            'testing_requirements': 'Material samples and performance testing',
            'assessment_timeline': assessment_timeline,
            'testing_timeline': testing_timeline,
            'decision_timeline': decision_timeline
        }

        return {
            'supplier_data': supplier_data,
            'approval_status': 'evaluation_required',
            'cost_estimate': pricing_estimate
        }

    def _analyze_inventory_restocking(self, content: str) -> Dict[str, Any]:
        """Analyze inventory restocking request"""
        # Determine materials to restock
        materials_to_order = []
        total_cost = 0

        for material, reorder_point in self.config['inventory_reorder_points'].items():
            if material.lower() in content or 'all' in content:
                order_quantity = reorder_point * 2  # Order double the reorder point
                unit_cost = {'BTN-001': 0.15, 'BTN-002': 0.18, 'BTN-003': 0.22, 'packaging': 0.05}.get(material, 0.15)
                material_cost = order_quantity * unit_cost
                total_cost += material_cost
                materials_to_order.append({
                    'material': material,
                    'quantity': order_quantity,
                    'unit_cost': unit_cost,
                    'total_cost': material_cost
                })

        if not materials_to_order:
            # Default restocking
            materials_to_order = [{
                'material': 'BTN-001',
                'quantity': 10000,
                'unit_cost': 0.15,
                'total_cost': 1500
            }]
            total_cost = 1500

        # Generate order summary
        order_summary = '\n'.join([
            f"- {item['material']}: {item['quantity']:,} units @ €{item['unit_cost']:.3f} = €{item['total_cost']:,.2f}"
            for item in materials_to_order
        ])

        # Generate delivery schedule
        delivery_schedule = '\n'.join([
            f"- {item['material']}: {(datetime.now() + timedelta(days=self.config['standard_lead_times'].get('button_components', 7))).date().isoformat()}"
            for item in materials_to_order
        ])

        inventory_data = {
            'order_summary': order_summary,
            'delivery_schedule': delivery_schedule,
            'total_volume': len(materials_to_order) * 50,  # m³
            'unloading_requirements': 'Forklift required',
            'storage_location': 'Warehouse Bay A',
            'inspection_requirements': 'Quality inspection area',
            'material_types': [item['material'] for item in materials_to_order]
        }

        return {
            'inventory_data': inventory_data,
            'approval_status': 'approved' if total_cost < self.config['auto_approve_threshold'] else 'pending_approval',
            'cost_estimate': total_cost,
            'procurement_plan': {
                'materials': materials_to_order,
                'total_cost': total_cost,
                'delivery_timeline': '7-10 days'
            }
        }

    def _analyze_cost_analysis(self, content: str) -> Dict[str, Any]:
        """Analyze cost analysis request"""
        current_month = datetime.now().strftime('%B %Y')

        # Simulate cost data
        total_spend = 85000
        budget_utilization = 87.5
        cost_variance = -2500
        variance_percentage = -2.9

        supplier_breakdown = """- ComponentSupply Co: €35,000 (41.2%)
- ButtonTech Industries: €28,500 (33.5%)
- PackagePro: €12,000 (14.1%)
- Premium Parts Ltd: €9,500 (11.2%)"""

        optimization_opportunities = """- Consolidate orders with ButtonTech Industries for volume discount
- Negotiate extended payment terms with ComponentSupply Co
- Evaluate alternative packaging suppliers for cost reduction
- Implement just-in-time delivery to reduce inventory costs"""

        recommendations = """- Renegotiate contracts with top 3 suppliers
- Implement supplier performance scorecards
- Explore long-term volume commitments for better pricing
- Consider dual-sourcing for critical materials"""

        budget_forecast = 92000

        cost_data = {
            'analysis_period': current_month,
            'total_spend': total_spend,
            'budget_utilization': budget_utilization,
            'cost_variance': cost_variance,
            'variance_percentage': variance_percentage,
            'supplier_breakdown': supplier_breakdown,
            'optimization_opportunities': optimization_opportunities,
            'recommendations': recommendations,
            'budget_forecast': budget_forecast
        }

        return {
            'cost_data': cost_data,
            'approval_status': 'informational',
            'cost_estimate': 0
        }

    def _analyze_contract_negotiation(self, content: str) -> Dict[str, Any]:
        """Analyze contract negotiation request"""
        # Extract contract value
        value_match = re.search(r'[€$]?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', content)
        contract_value = float(value_match.group(1).replace(',', '')) if value_match else 50000

        # Determine contract type
        if 'annual' in content or 'yearly' in content:
            contract_type = 'Annual Supply Agreement'
            duration = '12 months'
        elif 'framework' in content:
            contract_type = 'Framework Agreement'
            duration = '24 months'
        else:
            contract_type = 'Standard Purchase Contract'
            duration = '6 months'

        # Extract supplier
        supplier_match = re.search(r'supplier[:\s]+([A-Za-z\s&]+)', content, re.IGNORECASE)
        supplier = supplier_match.group(1).strip() if supplier_match else 'Supplier Name'

        # Determine materials
        materials = 'Button components and packaging materials'
        if 'button' in content:
            materials = 'Button components'
        elif 'packaging' in content:
            materials = 'Packaging materials'

        contract_data = {
            'supplier': supplier,
            'contract_type': contract_type,
            'value': contract_value,
            'duration': duration,
            'materials': materials,
            'negotiation_summary': f'Contract negotiation for {materials} supply',
            'key_terms': '- Volume commitments\n- Pricing structure\n- Delivery terms\n- Quality requirements',
            'risk_assessment': 'Low to medium risk - established supplier with good track record',
            'recommendation': 'Approve with standard terms and conditions'
        }

        return {
            'contract_data': contract_data,
            'approval_status': 'pending_management' if contract_value > self.config['management_approval_threshold'] else 'approved',
            'cost_estimate': contract_value
        }

    def _analyze_purchase_approval(self, content: str) -> Dict[str, Any]:
        """Analyze general purchase approval request"""
        # Extract purchase amount
        amount_match = re.search(r'[€$]?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', content)
        purchase_amount = float(amount_match.group(1).replace(',', '')) if amount_match else 1000

        # Determine approval status
        if purchase_amount < self.config['auto_approve_threshold']:
            approval_status = 'auto_approved'
        elif purchase_amount > self.config['management_approval_threshold']:
            approval_status = 'pending_management'
        else:
            approval_status = 'approved'

        return {
            'approval_status': approval_status,
            'cost_estimate': purchase_amount,
            'procurement_plan': {
                'amount': purchase_amount,
                'approval_level': approval_status,
                'processing_time': '1-2 days'
            }
        }

    def _select_purchasing_reply(self, analysis: Dict) -> str:
        """Select appropriate auto-reply template"""
        if analysis['type'] == 'urgent_procurement':
            return 'purchasing_urgent_ack'
        elif analysis['type'] == 'supplier_evaluation':
            return 'purchasing_supplier_ack'
        elif analysis['type'] == 'inventory_restocking':
            return 'purchasing_inventory_ack'
        elif analysis['type'] == 'cost_analysis':
            return 'purchasing_analysis_ack'
        elif analysis['type'] == 'contract_negotiation':
            return 'purchasing_contract_ack'
        else:
            return 'purchasing_ack'

    def _determine_purchasing_actions(self, analysis: Dict) -> List[str]:
        """Determine next actions based on purchasing analysis"""
        actions = []

        if analysis['type'] == 'urgent_procurement':
            actions.extend([
                "Contact preferred suppliers immediately",
                "Request emergency quotes",
                "Coordinate expedited delivery"
            ])
        elif analysis['type'] == 'supplier_evaluation':
            actions.extend([
                "Schedule supplier assessment meeting",
                "Request supplier documentation",
                "Coordinate quality evaluation"
            ])
        elif analysis['type'] == 'inventory_restocking':
            actions.extend([
                "Generate purchase orders",
                "Coordinate delivery schedule",
                "Prepare warehouse for receipt"
            ])
        elif analysis['type'] == 'cost_analysis':
            actions.extend([
                "Compile procurement data",
                "Analyze spending patterns",
                "Prepare cost optimization report"
            ])
        elif analysis['type'] == 'contract_negotiation':
            if analysis['contract_data']['value'] > self.config['management_approval_threshold']:
                actions.extend([
                    "Submit contract for management approval",
                    "Prepare detailed contract analysis",
                    "Schedule management review"
                ])
            else:
                actions.extend([
                    "Finalize contract terms",
                    "Coordinate legal review",
                    "Execute supplier agreement"
                ])

        # Common actions
        actions.append("Update procurement records")
        if analysis.get('cost_estimate', 0) > 5000:
            actions.append("Monitor budget impact")

        return actions

    def get_agent_capabilities(self) -> Dict[str, Any]:
        return {
            'procurement_management': True,
            'supplier_relations': True,
            'inventory_restocking': True,
            'cost_analysis': True,
            'contract_negotiation': True,
            'emergency_procurement': True,
            'purchase_approvals': True,
            'auto_approve_threshold': self.config['auto_approve_threshold'],
            'management_approval_threshold': self.config['management_approval_threshold'],
            'preferred_suppliers': self.config['preferred_suppliers'],
            'standard_lead_times': self.config['standard_lead_times']
        }

    def validate_email_for_agent(self, parsed_email: ParsedEmail) -> bool:
        content = f"{parsed_email.subject} {parsed_email.body}".lower()
        purchasing_keywords = [
            'purchase', 'procurement', 'supplier', 'vendor', 'order',
            'material', 'inventory', 'stock', 'contract', 'quote',
            'rfq', 'cost', 'pricing', 'buy'
        ]
        return any(keyword in content for keyword in purchasing_keywords)


if __name__ == "__main__":
    # Test the purchasing agent
    async def test_purchasing_agent():
        agent = PurchasingAgent()
        print(f"Purchasing Agent: {agent.agent_id}")
        print(f"Capabilities: {agent.get_agent_capabilities()}")

    asyncio.run(test_purchasing_agent())