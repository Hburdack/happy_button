"""
SalesAgent - Order Processing and Customer Sales
Handles sales inquiries, order processing, and customer confirmation
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from ..business.base_agent_v2 import BaseAgent, AgentTask, TaskPriority

try:
    from services.order.state_machine import OrderState, OrderStateMachine
except ImportError:  # pragma: no cover - allows package-relative imports
    from ...services.order.state_machine import OrderState, OrderStateMachine

class SalesAgent(BaseAgent):
    """
    SalesAgent handles sales inquiries and order processing
    Primary responsibilities:
    - Order processing and validation
    - Customer order confirmation
    - Pricing and quotation generation
    - Sales follow-up and customer communication
    - Order state management (CREATED → CONFIRMED)
    """

    def __init__(self):
        super().__init__("SalesAgent")
        self.order_machine = OrderStateMachine()

        # Sales thresholds from config
        self.thresholds = self._load_sales_thresholds()

        # Setup event handlers
        self.register_event_handler('order_created', self._handle_order_created)
        self.register_event_handler('customer_inquiry', self._handle_customer_inquiry)
        self.register_event_handler('price_request', self._handle_price_request)

    def _load_sales_thresholds(self) -> Dict[str, Any]:
        """Load sales processing thresholds from config"""
        return {
            'auto_approve_limit': 5000,  # Auto-approve orders under €5k
            'management_approval': 25000,  # Require management approval over €25k
            'oem_discount_rate': 0.15,  # 15% discount for OEM customers
            'bulk_discount_threshold': 1000,  # Bulk discount for 1000+ items
            'bulk_discount_rate': 0.10,  # 10% bulk discount
            'quote_validity_days': 30  # Quote valid for 30 days
        }

    def get_capabilities(self) -> List[str]:
        """Return SalesAgent capabilities"""
        return [
            'order_processing',
            'customer_confirmation',
            'pricing_calculation',
            'quotation_generation',
            'discount_management',
            'sales_follow_up',
            'order_validation',
            'inventory_checking',
            'customer_communication'
        ]

    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process SalesAgent tasks"""
        task_type = task.type

        if task_type == 'process_order':
            return await self._process_order(task.data)
        elif task_type == 'generate_quote':
            return await self._generate_quotation(task.data)
        elif task_type == 'confirm_order':
            return await self._confirm_order(task.data)
        elif task_type == 'calculate_pricing':
            return await self._calculate_pricing(task.data)
        elif task_type == 'validate_order':
            return await self._validate_order(task.data)
        elif task_type == 'follow_up':
            return await self._follow_up_customer(task.data)
        else:
            return {'error': f'Unknown task type: {task_type}'}

    async def _process_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main order processing workflow"""
        try:
            order_id = order_data.get('order_id')
            self.logger.info(f"Processing order {order_id}")

            # Step 1: Validate the order
            validation_result = await self._validate_order(order_data)
            if not validation_result.get('valid'):
                return {
                    'status': 'validation_failed',
                    'order_id': order_id,
                    'errors': validation_result.get('errors', [])
                }

            # Step 2: Calculate pricing and discounts
            pricing_result = await self._calculate_pricing(order_data)

            # Step 3: Check if auto-approval is possible
            approval_result = await self._check_approval_requirements(order_data, pricing_result)

            # Step 4: Generate customer confirmation
            confirmation_data = await self._generate_customer_confirmation(
                order_data, pricing_result, approval_result
            )

            # Step 5: Update order state if auto-approved
            if approval_result.get('auto_approved'):
                await self._transition_order_to_confirmed(order_id)

            # Step 6: Emit events for other systems
            await self._emit_sales_events(order_data, pricing_result, approval_result)

            return {
                'status': 'processed',
                'order_id': order_id,
                'validation': validation_result,
                'pricing': pricing_result,
                'approval': approval_result,
                'confirmation': confirmation_data,
                'auto_approved': approval_result.get('auto_approved', False)
            }

        except Exception as e:
            self.logger.error(f"Error processing order: {e}")
            return {'error': str(e)}

    async def _validate_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order data and business rules"""
        errors = []
        warnings = []

        # Get order from system
        order_id = order_data.get('order_id')
        order = self.order_machine.get_order(order_id) if order_id else None

        if not order:
            errors.append(f"Order {order_id} not found in system")
            return {'valid': False, 'errors': errors}

        # Validate customer information
        if not order.customer_email:
            errors.append("Customer email is required")

        if not order.customer_name:
            warnings.append("Customer name is missing")

        # Validate items
        if not order.items:
            errors.append("Order must contain at least one item")
        else:
            for i, item in enumerate(order.items):
                if item.quantity <= 0:
                    errors.append(f"Item {i+1}: Invalid quantity ({item.quantity})")

                if item.unit_price < 0:
                    errors.append(f"Item {i+1}: Invalid price ({item.unit_price})")

                # Check inventory (simulated)
                inventory_available = await self._check_inventory(item.sku, item.quantity)
                if not inventory_available:
                    warnings.append(f"Item {item.sku}: Limited inventory available")

        # Business rule validations
        if order.total_amount <= 0:
            errors.append("Order total must be greater than zero")

        if order.total_amount > 100000:
            warnings.append("Large order amount - may require special handling")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    async def _calculate_pricing(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate pricing, discounts, and totals"""
        order_id = order_data.get('order_id')
        order = self.order_machine.get_order(order_id)

        if not order:
            return {'error': 'Order not found'}

        # Base calculations
        subtotal = sum(item.total_price for item in order.items)
        total_quantity = sum(item.quantity for item in order.items)

        # Determine customer type
        customer_domain = order.customer_email.split('@')[-1] if '@' in order.customer_email else ''
        is_oem = customer_domain in self.config.get('oem_customers', [])

        # Calculate discounts
        discounts = []
        discount_amount = 0

        # OEM discount
        if is_oem:
            oem_discount = subtotal * self.thresholds['oem_discount_rate']
            discounts.append({
                'type': 'OEM Customer Discount',
                'rate': self.thresholds['oem_discount_rate'],
                'amount': oem_discount
            })
            discount_amount += oem_discount

        # Bulk discount
        if total_quantity >= self.thresholds['bulk_discount_threshold']:
            bulk_discount = subtotal * self.thresholds['bulk_discount_rate']
            discounts.append({
                'type': 'Bulk Order Discount',
                'rate': self.thresholds['bulk_discount_rate'],
                'amount': bulk_discount,
                'threshold': self.thresholds['bulk_discount_threshold']
            })
            discount_amount += bulk_discount

        # Calculate tax (19% VAT)
        discounted_subtotal = subtotal - discount_amount
        tax_rate = 0.19
        tax_amount = discounted_subtotal * tax_rate

        # Final total
        final_total = discounted_subtotal + tax_amount

        return {
            'subtotal': subtotal,
            'discounts': discounts,
            'discount_total': discount_amount,
            'discounted_subtotal': discounted_subtotal,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            'final_total': final_total,
            'customer_type': 'OEM' if is_oem else 'Standard',
            'total_quantity': total_quantity
        }

    async def _check_approval_requirements(self, order_data: Dict[str, Any],
                                         pricing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Check if order requires special approval"""
        final_total = pricing_result.get('final_total', 0)
        order_id = order_data.get('order_id')

        approval = {
            'auto_approved': False,
            'requires_approval': False,
            'approval_level': 'none',
            'reason': ''
        }

        # Auto-approval for small orders
        if final_total <= self.thresholds['auto_approve_limit']:
            approval['auto_approved'] = True
            approval['reason'] = f'Auto-approved (under €{self.thresholds["auto_approve_limit"]})'

        # Management approval for large orders
        elif final_total >= self.thresholds['management_approval']:
            approval['requires_approval'] = True
            approval['approval_level'] = 'management'
            approval['reason'] = f'Requires management approval (over €{self.thresholds["management_approval"]})'

        # Sales manager approval for medium orders
        else:
            approval['requires_approval'] = True
            approval['approval_level'] = 'sales_manager'
            approval['reason'] = 'Requires sales manager approval'

        return approval

    async def _generate_customer_confirmation(self, order_data: Dict[str, Any],
                                            pricing_result: Dict[str, Any],
                                            approval_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate customer order confirmation email"""
        order_id = order_data.get('order_id')
        order = self.order_machine.get_order(order_id)

        if not order:
            return {'error': 'Order not found'}

        # Generate order confirmation email
        customer_name = order.customer_name or order.customer_email.split('@')[0].title()

        # Email subject
        subject = f"Order Confirmation - {order_id} - Happy Buttons GmbH"

        # Email body with royal courtesy
        body = f"""Dear {customer_name},

We are delighted to confirm receipt of your esteemed order and thank you for choosing Happy Buttons GmbH for your button requirements.

ORDER DETAILS:
Order Number: {order_id}
Order Date: {time.strftime('%d/%m/%Y %H:%M')}
Customer: {order.customer_name}

ITEMS ORDERED:"""

        # Add items
        for item in order.items:
            body += f"""
- {item.name} (SKU: {item.sku})
  Quantity: {item.quantity} pieces
  Unit Price: €{item.unit_price:.2f}
  Total: €{item.total_price:.2f}"""

        # Add pricing summary
        body += f"""

PRICING SUMMARY:
Subtotal: €{pricing_result['subtotal']:.2f}"""

        # Add discounts if any
        if pricing_result.get('discounts'):
            for discount in pricing_result['discounts']:
                body += f"""
{discount['type']}: -€{discount['amount']:.2f}"""

        body += f"""
Tax (19% VAT): €{pricing_result['tax_amount']:.2f}
TOTAL: €{pricing_result['final_total']:.2f}"""

        # Add approval status
        if approval_result.get('auto_approved'):
            body += f"""

STATUS: Your order has been automatically approved and will proceed to production scheduling within 4 hours."""
        else:
            body += f"""

STATUS: Your order is currently under review. We shall notify you of approval within 24 hours."""

        body += f"""

Our production team will ensure your order meets our highest quality standards. You will receive regular updates on the progress of your order.

Should you have any questions, please do not hesitate to contact our sales team.

With our sincerest appreciation for your business,

Happy Buttons GmbH Sales Department
sales@h-bu.de
+49 (0) 123 456 789"""

        return {
            'to': order.customer_email,
            'subject': subject,
            'body': body,
            'template': 'order_confirmation',
            'courtesy_score': 92,
            'priority': 'high' if approval_result.get('auto_approved') else 'normal'
        }

    async def _transition_order_to_confirmed(self, order_id: str) -> bool:
        """Transition order from CREATED to CONFIRMED state"""
        try:
            success = self.order_machine.transition_order(
                order_id,
                OrderState.CONFIRMED,
                "SalesAgent",
                "Order confirmed and approved for production",
                {'confirmed_by': 'auto_approval', 'confirmed_at': time.time()}
            )

            if success:
                self.logger.info(f"Order {order_id} transitioned to CONFIRMED state")

            return success

        except Exception as e:
            self.logger.error(f"Error transitioning order {order_id}: {e}")
            return False

    async def _generate_quotation(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate formal quotation for customer inquiry"""
        try:
            customer_email = quote_data.get('customer_email')
            customer_name = quote_data.get('customer_name', customer_email.split('@')[0].title())
            requested_items = quote_data.get('items', [])

            # Calculate pricing for requested items
            quote_items = []
            subtotal = 0

            for item_request in requested_items:
                # Get current pricing (would come from pricing database)
                unit_price = await self._get_current_price(item_request.get('sku'))
                quantity = item_request.get('quantity', 1)
                total_price = unit_price * quantity

                quote_items.append({
                    'sku': item_request.get('sku'),
                    'name': item_request.get('name'),
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': total_price,
                    'lead_time': await self._get_lead_time(item_request.get('sku'))
                })

                subtotal += total_price

            # Apply discounts and calculate final pricing
            pricing_result = await self._calculate_pricing_for_quote(quote_data, subtotal)

            # Generate quotation document
            quote_id = f"QUO_{int(time.time())}"
            valid_until = time.time() + (self.thresholds['quote_validity_days'] * 24 * 3600)

            quotation = {
                'quote_id': quote_id,
                'customer_email': customer_email,
                'customer_name': customer_name,
                'items': quote_items,
                'pricing': pricing_result,
                'valid_until': valid_until,
                'terms': 'Net 30 days, FOB factory',
                'generated_by': self.agent_id,
                'generated_at': time.time()
            }

            # Save quotation
            await self._save_quotation(quotation)

            return quotation

        except Exception as e:
            self.logger.error(f"Error generating quotation: {e}")
            return {'error': str(e)}

    async def _check_inventory(self, sku: str, quantity: int) -> bool:
        """Check if inventory is available (simulated)"""
        # In real implementation, would query inventory system
        # For now, simulate availability
        return True

    async def _get_current_price(self, sku: str) -> float:
        """Get current price for SKU (simulated)"""
        # Simulated pricing based on SKU
        price_map = {
            'BTN-001': 2.50,
            'BTN-002': 5.00,
            'BTN-003': 3.75,
            'BTN-PREMIUM': 8.00
        }
        return price_map.get(sku, 2.50)  # Default price

    async def _get_lead_time(self, sku: str) -> str:
        """Get lead time for SKU (simulated)"""
        return "5-7 business days"

    async def _calculate_pricing_for_quote(self, quote_data: Dict[str, Any], subtotal: float) -> Dict[str, Any]:
        """Calculate pricing for quotation"""
        # Simplified version of pricing calculation
        tax_rate = 0.19
        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount

        return {
            'subtotal': subtotal,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            'total': total
        }

    async def _save_quotation(self, quotation: Dict[str, Any]):
        """Save quotation to storage"""
        # Save to agent memory and file system
        quote_id = quotation['quote_id']
        self.store_memory(f"quotation_{quote_id}", quotation, "quotations")

        # Also save to quotes directory for dashboard
        import json
        import os
        quotes_dir = "data/quotes"
        os.makedirs(quotes_dir, exist_ok=True)

        quote_file = f"{quotes_dir}/{quote_id}.json"
        with open(quote_file, 'w') as f:
            json.dump(quotation, f, indent=2)

    async def _follow_up_customer(self, follow_up_data: Dict[str, Any]) -> Dict[str, Any]:
        """Follow up with customer on pending orders or quotes"""
        # Implementation for customer follow-up
        return {'status': 'follow_up_sent'}

    async def _emit_sales_events(self, order_data: Dict[str, Any],
                                pricing_result: Dict[str, Any],
                                approval_result: Dict[str, Any]):
        """Emit sales-related events"""
        order_id = order_data.get('order_id')

        # Order processed event
        await self.emit_event('order_processed', {
            'order_id': order_id,
            'pricing': pricing_result,
            'approval': approval_result,
            'processed_by': self.agent_id
        })

        # If auto-approved, emit confirmation event
        if approval_result.get('auto_approved'):
            await self.emit_event('order_confirmed', {
                'order_id': order_id,
                'confirmed_by': 'auto_approval',
                'final_total': pricing_result.get('final_total')
            })

    # Event handlers
    async def _handle_order_created(self, event):
        """Handle order creation events"""
        order_data = event.data

        # Create task to process the order
        task = AgentTask(
            id=f"order_{order_data.get('order_id')}",
            type='process_order',
            priority=TaskPriority.HIGH,
            data=order_data
        )

        await self.assign_task(task)

    async def _handle_customer_inquiry(self, event):
        """Handle customer inquiry events"""
        inquiry_data = event.data

        # Create task to generate quotation
        task = AgentTask(
            id=f"inquiry_{inquiry_data.get('email_id')}",
            type='generate_quote',
            priority=TaskPriority.NORMAL,
            data=inquiry_data
        )

        await self.assign_task(task)

    async def _handle_price_request(self, event):
        """Handle price request events"""
        price_data = event.data

        # Create task to calculate pricing
        task = AgentTask(
            id=f"price_{int(time.time())}",
            type='calculate_pricing',
            priority=TaskPriority.NORMAL,
            data=price_data
        )

        await self.assign_task(task)

# Demo usage
if __name__ == "__main__":
    import asyncio
    import logging

    logging.basicConfig(level=logging.INFO)

    async def demo_sales_agent():
        agent = SalesAgent()

        # Demo order processing
        demo_order = {
            'order_id': 'ORD_DEMO_001',
            'customer_email': 'customer@oem1.com',
            'customer_name': 'Demo Customer'
        }

        task = AgentTask(
            id="demo_sales_task",
            type="process_order",
            priority=TaskPriority.HIGH,
            data=demo_order
        )

        await agent.assign_task(task)
        result = await agent.process_next_task()

        print("SalesAgent Demo Result:")
        print(f"Status: {agent.get_status()}")
        print(f"Processing Result: {result}")

        await agent.shutdown()

    asyncio.run(demo_sales_agent())
