"""
Finance Agent for Happy Buttons Release 2
Handles pricing, billing, cost analysis, payment tracking, and financial approvals
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


class FinanceAgent(BaseAgent):
    """
    Finance Agent - Handles finance@h-bu.de
    Manages pricing, billing, payments, cost analysis, and financial approvals
    """

    def __init__(self, agent_id: str = "finance-001"):
        super().__init__(agent_id, "finance_agent", {
            'auto_approve_threshold': 1000,     # Auto-approve costs under €1000
            'management_approval_threshold': 10000,  # Require management approval over €10000
            'standard_margins': {
                'BTN-001': 0.65,  # 65% margin
                'BTN-002': 0.70,  # 70% margin
                'BTN-003': 0.75   # 75% margin for premium
            },
            'volume_discount_tiers': {
                1000: 0.05,    # 5% discount for 1000+ units
                5000: 0.10,    # 10% discount for 5000+ units
                10000: 0.15    # 15% discount for 10000+ units
            },
            'payment_terms': {
                'standard': 30,  # 30 days
                'oem': 45,       # 45 days for OEM
                'new_customer': 15  # 15 days for new customers
            },
            'currency_rates': {
                'EUR': 1.0,
                'USD': 1.08,
                'GBP': 0.87
            }
        })

    async def _process_email_impl(self, parsed_email: ParsedEmail,
                                 routing_decision: RoutingDecision,
                                 task: AgentTask) -> AgentResponse:
        """Process finance-related emails"""

        finance_analysis = await self._analyze_finance_request(parsed_email)

        response_data = {
            'action': 'finance_processed',
            'request_type': finance_analysis['type'],
            'financial_analysis': finance_analysis['analysis'],
            'approval_status': finance_analysis['approval_status'],
            'cost_impact': finance_analysis.get('cost_impact', 0)
        }

        coordination_notes = []

        # Handle different types of finance requests
        if finance_analysis['type'] == 'pricing_request':
            quote_data = finance_analysis['quote_data']

            # Generate detailed quote
            success = await self.send_task_email(
                to_agent='info_agent',
                task_type=TaskTypes.CUSTOMER_RESPONSE,
                content=f"Custom Pricing Quote Generated\n\nCustomer: {finance_analysis['customer']}\nQuote ID: {quote_data['quote_id']}\nValid Until: {quote_data['valid_until']}\n\nPricing Details:\n- Product: {quote_data['product_type']}\n- Quantity: {quote_data['quantity']:,} units\n- Unit Price: €{quote_data['unit_price']:.3f}\n- Subtotal: €{quote_data['subtotal']:,.2f}\n- Volume Discount: {quote_data['discount_percentage']:.1f}% (€{quote_data['discount_amount']:,.2f})\n- Total Price: €{quote_data['total_price']:,.2f}\n\nPayment Terms: {quote_data['payment_terms']} days\nDelivery: {quote_data['delivery_estimate']}\n\nPlease send this quote to the customer and follow up within 48 hours.",
                priority="high",
                data={
                    'quote_id': quote_data['quote_id'],
                    'customer': finance_analysis['customer'],
                    'total_value': quote_data['total_price'],
                    'follow_up_required': True
                },
                due_hours=4
            )
            if success:
                coordination_notes.append("Generated and sent custom pricing quote")

        elif finance_analysis['type'] == 'cost_approval':
            approval_data = finance_analysis['approval_data']

            if approval_data['requires_management']:
                success = await self.send_task_email(
                    to_agent='management_agent',
                    task_type=TaskTypes.FINANCIAL_APPROVAL,
                    content=f"HIGH-VALUE COST APPROVAL REQUIRED\n\nCost Type: {approval_data['cost_type']}\nAmount: €{approval_data['amount']:,.2f}\nRequesting Department: {approval_data['requesting_agent']}\nJustification: {approval_data['justification']}\n\nFinancial Impact Analysis:\n- Budget Category: {approval_data['budget_category']}\n- Current Budget Utilization: {approval_data['budget_utilization']:.1f}%\n- Remaining Budget: €{approval_data['remaining_budget']:,.2f}\n- ROI Estimate: {approval_data['roi_estimate']}\n\nRecommendation: {approval_data['recommendation']}\n\nManagement approval required due to amount exceeding €{self.config['management_approval_threshold']:,} threshold.",
                    priority="high",
                    data={
                        'approval_type': 'high_value_cost',
                        'amount': approval_data['amount'],
                        'cost_type': approval_data['cost_type'],
                        'requires_executive_approval': True
                    },
                    due_hours=4
                )
                if success:
                    coordination_notes.append("Escalated high-value cost approval to management")
            else:
                # Auto-approve or standard approval
                success = await self.send_task_email(
                    to_agent=approval_data['requesting_agent'],
                    task_type=TaskTypes.APPROVAL_RESPONSE,
                    content=f"Cost Approval: {approval_data['status'].upper()}\n\nCost Type: {approval_data['cost_type']}\nAmount: €{approval_data['amount']:,.2f}\nApproval ID: {approval_data['approval_id']}\n\nFinance Notes:\n{approval_data['finance_notes']}\n\nYou may proceed with the approved expenditure. Please ensure proper documentation and receipts are submitted for accounting.",
                    priority="medium",
                    data={
                        'approval_id': approval_data['approval_id'],
                        'approved_amount': approval_data['amount'],
                        'approval_status': approval_data['status']
                    },
                    due_hours=2
                )
                if success:
                    coordination_notes.append(f"Sent cost approval response: {approval_data['status']}")

        elif finance_analysis['type'] == 'payment_issue':
            payment_data = finance_analysis['payment_data']

            if payment_data['severity'] == 'critical':
                success = await self.send_task_email(
                    to_agent='management_agent',
                    task_type=TaskTypes.ESCALATION,
                    content=f"CRITICAL PAYMENT ISSUE - IMMEDIATE ATTENTION REQUIRED\n\nCustomer: {payment_data['customer']}\nOutstanding Amount: €{payment_data['outstanding_amount']:,.2f}\nDays Overdue: {payment_data['days_overdue']}\nPayment History: {payment_data['payment_history']}\n\nRisk Assessment:\n- Credit Risk Level: {payment_data['credit_risk']}\n- Collection Difficulty: {payment_data['collection_difficulty']}\n- Recommended Action: {payment_data['recommended_action']}\n\nThis account requires immediate management attention to prevent write-off.",
                    priority="critical",
                    data={
                        'customer': payment_data['customer'],
                        'outstanding_amount': payment_data['outstanding_amount'],
                        'risk_level': payment_data['credit_risk']
                    },
                    due_hours=2
                )
                if success:
                    coordination_notes.append("Escalated critical payment issue to management")

        elif finance_analysis['type'] == 'budget_analysis':
            budget_data = finance_analysis['budget_data']

            success = await self.send_task_email(
                to_agent='management_agent',
                task_type=TaskTypes.BUDGET_REPORT,
                content=f"Monthly Budget Analysis Report\n\nReporting Period: {budget_data['period']}\nTotal Budget: €{budget_data['total_budget']:,.2f}\nActual Spend: €{budget_data['actual_spend']:,.2f}\nBudget Utilization: {budget_data['utilization_percentage']:.1f}%\nVariance: €{budget_data['variance']:,.2f} ({budget_data['variance_percentage']:+.1f}%)\n\nDepartment Breakdown:\n{budget_data['department_breakdown']}\n\nKey Insights:\n{budget_data['key_insights']}\n\nRecommendations:\n{budget_data['recommendations']}",
                priority="medium",
                data={
                    'period': budget_data['period'],
                    'utilization': budget_data['utilization_percentage'],
                    'variance': budget_data['variance']
                },
                due_hours=24
            )
            if success:
                coordination_notes.append("Sent budget analysis report to management")

        # Determine auto-reply
        auto_reply = self._select_finance_reply(finance_analysis)

        return AgentResponse(
            task_id=task.id,
            agent_id=self.agent_id,
            status="success",
            response_data=response_data,
            auto_reply=auto_reply,
            next_actions=self._determine_finance_actions(finance_analysis),
            coordination_notes=coordination_notes
        )

    async def _analyze_finance_request(self, parsed_email: ParsedEmail) -> Dict[str, Any]:
        """Analyze finance request and determine type and requirements"""
        content = f"{parsed_email.subject} {parsed_email.body}".lower()

        # Determine request type
        if any(word in content for word in ['quote', 'pricing', 'price', 'cost', 'estimate']):
            request_type = 'pricing_request'
        elif any(word in content for word in ['approval', 'approve', 'budget', 'expense', 'purchase']):
            request_type = 'cost_approval'
        elif any(word in content for word in ['payment', 'invoice', 'overdue', 'collection']):
            request_type = 'payment_issue'
        elif any(word in content for word in ['budget', 'analysis', 'report', 'forecast']):
            request_type = 'budget_analysis'
        elif any(word in content for word in ['discount', 'volume', 'bulk']):
            request_type = 'discount_request'
        else:
            request_type = 'general_inquiry'

        # Base analysis
        analysis = {
            'type': request_type,
            'customer': parsed_email.sender.email,
            'customer_domain': parsed_email.sender.domain,
            'timestamp': datetime.now().isoformat()
        }

        # Add type-specific analysis
        if request_type == 'pricing_request':
            analysis.update(self._analyze_pricing_request(content, parsed_email))
        elif request_type == 'cost_approval':
            analysis.update(self._analyze_cost_approval(content, parsed_email))
        elif request_type == 'payment_issue':
            analysis.update(self._analyze_payment_issue(content, parsed_email))
        elif request_type == 'budget_analysis':
            analysis.update(self._analyze_budget_request(content))

        return analysis

    def _analyze_pricing_request(self, content: str, parsed_email: ParsedEmail) -> Dict[str, Any]:
        """Analyze pricing/quote request"""
        # Extract quantity
        qty_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*(?:pieces|pcs|units|buttons)', content)
        quantity = int(qty_match.group(1).replace(',', '')) if qty_match else 1000

        # Determine product type
        product_type = 'BTN-001'  # Default
        if 'blue' in content:
            product_type = 'BTN-002'
        elif 'premium' in content or 'royal' in content:
            product_type = 'BTN-003'

        # Calculate pricing
        base_price = 2.50  # Base price per unit
        if product_type == 'BTN-002':
            base_price = 3.00
        elif product_type == 'BTN-003':
            base_price = 4.00

        # Apply volume discounts
        discount_percentage = 0
        for min_qty, discount in sorted(self.config['volume_discount_tiers'].items(), reverse=True):
            if quantity >= min_qty:
                discount_percentage = discount
                break

        unit_price = base_price * (1 - discount_percentage)
        subtotal = quantity * base_price
        discount_amount = subtotal * discount_percentage
        total_price = subtotal - discount_amount

        # Determine payment terms
        is_oem = parsed_email.metadata.is_oem if hasattr(parsed_email.metadata, 'is_oem') else False
        payment_terms = self.config['payment_terms']['oem'] if is_oem else self.config['payment_terms']['standard']

        # Generate quote
        quote_id = f"QUO-{datetime.now().strftime('%Y%m%d')}-{parsed_email.id[:6]}"
        valid_until = (datetime.now() + timedelta(days=14)).date().isoformat()

        quote_data = {
            'quote_id': quote_id,
            'product_type': product_type,
            'quantity': quantity,
            'base_price': base_price,
            'unit_price': unit_price,
            'subtotal': subtotal,
            'discount_percentage': discount_percentage * 100,
            'discount_amount': discount_amount,
            'total_price': total_price,
            'payment_terms': payment_terms,
            'valid_until': valid_until,
            'delivery_estimate': '5-7 business days',
            'margin_percentage': self.config['standard_margins'].get(product_type, 0.65) * 100
        }

        return {
            'analysis': f'Custom pricing quote generated for {quantity:,} units of {product_type}',
            'quote_data': quote_data,
            'approval_status': 'auto_approved',
            'cost_impact': 0
        }

    def _analyze_cost_approval(self, content: str, parsed_email: ParsedEmail) -> Dict[str, Any]:
        """Analyze cost approval request"""
        # Extract cost amount
        amount_match = re.search(r'[€$]?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', content)
        amount = float(amount_match.group(1).replace(',', '')) if amount_match else 500

        # Determine cost type
        if 'shipping' in content or 'expedite' in content:
            cost_type = 'expedited_shipping'
            budget_category = 'logistics'
        elif 'material' in content or 'procurement' in content:
            cost_type = 'material_procurement'
            budget_category = 'procurement'
        elif 'equipment' in content or 'machinery' in content:
            cost_type = 'equipment_purchase'
            budget_category = 'capex'
        else:
            cost_type = 'operational_expense'
            budget_category = 'opex'

        # Determine approval requirements
        requires_management = amount > self.config['management_approval_threshold']
        auto_approve = amount < self.config['auto_approve_threshold']

        if auto_approve:
            approval_status = 'approved'
        elif requires_management:
            approval_status = 'pending_management'
        else:
            approval_status = 'approved'

        # Generate approval data
        approval_id = f"APP-{datetime.now().strftime('%Y%m%d')}-{parsed_email.id[:6]}"

        # Simulate budget data
        total_budget = 50000  # Monthly budget
        current_spend = 35000  # Current utilization
        remaining_budget = total_budget - current_spend
        budget_utilization = (current_spend / total_budget) * 100

        # Determine ROI and recommendation
        if cost_type == 'expedited_shipping':
            roi_estimate = 'Customer satisfaction and retention'
            recommendation = 'Approve - maintains customer satisfaction'
        elif cost_type == 'equipment_purchase':
            roi_estimate = '18-24 months payback period'
            recommendation = 'Approve with depreciation schedule'
        else:
            roi_estimate = 'Operational efficiency improvement'
            recommendation = 'Approve within budget guidelines'

        approval_data = {
            'approval_id': approval_id,
            'amount': amount,
            'cost_type': cost_type,
            'budget_category': budget_category,
            'requires_management': requires_management,
            'status': approval_status,
            'requesting_agent': 'logistics_agent',  # Assume from context
            'justification': f'Requested {cost_type} for business operations',
            'budget_utilization': budget_utilization,
            'remaining_budget': remaining_budget,
            'roi_estimate': roi_estimate,
            'recommendation': recommendation,
            'finance_notes': f'Amount within {budget_category} budget allocation. Standard approval process followed.'
        }

        return {
            'analysis': f'Cost approval request for €{amount:,.2f} - {cost_type}',
            'approval_data': approval_data,
            'approval_status': approval_status,
            'cost_impact': amount
        }

    def _analyze_payment_issue(self, content: str, parsed_email: ParsedEmail) -> Dict[str, Any]:
        """Analyze payment-related issue"""
        # Extract payment amount
        amount_match = re.search(r'[€$]?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', content)
        outstanding_amount = float(amount_match.group(1).replace(',', '')) if amount_match else 2500

        # Determine severity
        if any(word in content for word in ['overdue', 'late', 'collection']):
            severity = 'critical' if outstanding_amount > 5000 else 'high'
        else:
            severity = 'medium'

        # Simulate payment history
        days_overdue = 45 if 'overdue' in content else 0
        payment_history = 'Generally reliable' if (hasattr(parsed_email.metadata, 'is_oem') and parsed_email.metadata.is_oem) else 'Mixed payment history'

        # Risk assessment
        if outstanding_amount > 10000 and days_overdue > 60:
            credit_risk = 'high'
            collection_difficulty = 'difficult'
            recommended_action = 'Legal collection action'
        elif outstanding_amount > 5000 and days_overdue > 30:
            credit_risk = 'medium'
            collection_difficulty = 'moderate'
            recommended_action = 'Formal collection notice'
        else:
            credit_risk = 'low'
            collection_difficulty = 'easy'
            recommended_action = 'Standard follow-up'

        payment_data = {
            'customer': parsed_email.sender.email,
            'outstanding_amount': outstanding_amount,
            'days_overdue': days_overdue,
            'severity': severity,
            'payment_history': payment_history,
            'credit_risk': credit_risk,
            'collection_difficulty': collection_difficulty,
            'recommended_action': recommended_action
        }

        return {
            'analysis': f'Payment issue: €{outstanding_amount:,.2f} outstanding, {days_overdue} days overdue',
            'payment_data': payment_data,
            'approval_status': 'review_required',
            'cost_impact': outstanding_amount  # Potential loss
        }

    def _analyze_budget_request(self, content: str) -> Dict[str, Any]:
        """Analyze budget analysis request"""
        current_month = datetime.now().strftime('%B %Y')

        # Simulate budget data
        total_budget = 100000
        actual_spend = 87500
        variance = actual_spend - total_budget
        variance_percentage = (variance / total_budget) * 100
        utilization_percentage = (actual_spend / total_budget) * 100

        department_breakdown = """- Operations: €35,000 (87.5% of allocation)
- Production: €28,500 (95.0% of allocation)
- Logistics: €12,000 (80.0% of allocation)
- Marketing: €8,000 (66.7% of allocation)
- Administration: €4,000 (100.0% of allocation)"""

        key_insights = """- Operations spending on track
- Production slightly over budget due to material costs
- Logistics under budget due to shipping optimization
- Marketing spending below target - may need campaign boost"""

        recommendations = """- Monitor production material costs closely
- Consider reallocating unused logistics budget
- Increase marketing spend to hit quarterly targets
- Implement cost controls for next month"""

        budget_data = {
            'period': current_month,
            'total_budget': total_budget,
            'actual_spend': actual_spend,
            'variance': variance,
            'variance_percentage': variance_percentage,
            'utilization_percentage': utilization_percentage,
            'department_breakdown': department_breakdown,
            'key_insights': key_insights,
            'recommendations': recommendations
        }

        return {
            'analysis': f'Budget analysis for {current_month} - {utilization_percentage:.1f}% utilization',
            'budget_data': budget_data,
            'approval_status': 'informational',
            'cost_impact': variance
        }

    def _select_finance_reply(self, analysis: Dict) -> str:
        """Select appropriate auto-reply template"""
        if analysis['type'] == 'pricing_request':
            return 'finance_quote_ack'
        elif analysis['type'] == 'cost_approval':
            return 'finance_approval_ack'
        elif analysis['type'] == 'payment_issue':
            return 'finance_payment_ack'
        elif analysis['type'] == 'budget_analysis':
            return 'finance_budget_ack'
        else:
            return 'finance_ack'

    def _determine_finance_actions(self, analysis: Dict) -> List[str]:
        """Determine next actions based on finance analysis"""
        actions = []

        if analysis['type'] == 'pricing_request':
            actions.extend([
                "Generate detailed pricing quote",
                "Send quote to customer",
                "Schedule follow-up in 48 hours"
            ])
        elif analysis['type'] == 'cost_approval':
            if analysis['approval_data']['requires_management']:
                actions.extend([
                    "Escalate to management for approval",
                    "Prepare detailed cost justification",
                    "Monitor approval timeline"
                ])
            else:
                actions.extend([
                    "Process cost approval",
                    "Update budget tracking",
                    "Notify requesting department"
                ])
        elif analysis['type'] == 'payment_issue':
            if analysis['payment_data']['severity'] == 'critical':
                actions.extend([
                    "Escalate to management immediately",
                    "Consider collection agency",
                    "Review credit terms for customer"
                ])
            else:
                actions.extend([
                    "Send payment reminder",
                    "Schedule follow-up call",
                    "Update customer payment history"
                ])
        elif analysis['type'] == 'budget_analysis':
            actions.extend([
                "Generate comprehensive budget report",
                "Schedule management review meeting",
                "Update budget tracking dashboard"
            ])

        # Common actions
        actions.append("Update financial records")
        if analysis.get('cost_impact', 0) > 1000:
            actions.append("Monitor financial impact closely")

        return actions

    def get_agent_capabilities(self) -> Dict[str, Any]:
        return {
            'pricing_and_quotes': True,
            'cost_approvals': True,
            'budget_analysis': True,
            'payment_tracking': True,
            'financial_reporting': True,
            'volume_discounts': True,
            'margin_analysis': True,
            'auto_approve_threshold': self.config['auto_approve_threshold'],
            'management_approval_threshold': self.config['management_approval_threshold'],
            'supported_currencies': list(self.config['currency_rates'].keys()),
            'volume_discount_tiers': self.config['volume_discount_tiers']
        }

    def validate_email_for_agent(self, parsed_email: ParsedEmail) -> bool:
        content = f"{parsed_email.subject} {parsed_email.body}".lower()
        finance_keywords = [
            'price', 'cost', 'quote', 'payment', 'invoice', 'budget',
            'approval', 'finance', 'billing', 'discount', 'margin'
        ]
        return any(keyword in content for keyword in finance_keywords)


if __name__ == "__main__":
    # Test the finance agent
    async def test_finance_agent():
        agent = FinanceAgent()
        print(f"Finance Agent: {agent.agent_id}")
        print(f"Capabilities: {agent.get_agent_capabilities()}")

    asyncio.run(test_finance_agent())