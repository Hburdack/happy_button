"""
Order State Machine for Happy Buttons Release 2
Manages the complete order lifecycle from creation to closure
"""

import time
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import json
import os

class OrderState(Enum):
    """Order states from company configuration"""
    CREATED = "CREATED"
    CONFIRMED = "CONFIRMED"
    PLANNED = "PLANNED"
    IN_PRODUCTION = "IN_PRODUCTION"
    PRODUCED = "PRODUCED"
    PACKED = "PACKED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    INVOICED = "INVOICED"
    CLOSED = "CLOSED"

@dataclass
class OrderItem:
    sku: str
    name: str
    quantity: int
    unit_price: float
    total_price: float

@dataclass
class StateTransition:
    from_state: OrderState
    to_state: OrderState
    timestamp: float
    agent: str
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Order:
    id: str
    customer_email: str
    customer_name: str
    items: List[OrderItem]
    total_amount: float
    priority: int
    sla_hours: int
    current_state: OrderState
    history: List[StateTransition] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_transition(self, to_state: OrderState, agent: str, reason: str, metadata: Dict = None):
        """Add a state transition to order history"""
        transition = StateTransition(
            from_state=self.current_state,
            to_state=to_state,
            timestamp=time.time(),
            agent=agent,
            reason=reason,
            metadata=metadata or {}
        )
        self.history.append(transition)
        self.current_state = to_state

class OrderStateMachine:
    """Manages order state transitions and business logic"""

    def __init__(self, config_path: str = "sim/config/company_release2.yaml"):
        self.logger = logging.getLogger(__name__)
        self.orders: Dict[str, Order] = {}
        self.config = self._load_config(config_path)

        # Storage setup
        self.storage_dir = "data/orders"
        os.makedirs(self.storage_dir, exist_ok=True)

        # State transition rules from config
        self.state_rules = self._load_state_rules()

    def _load_config(self, config_path: str) -> dict:
        """Load company configuration"""
        try:
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.error(f"Config file not found: {config_path}")
            return {}

    def _load_state_rules(self) -> Dict[OrderState, Dict]:
        """Load state transition rules from configuration"""
        rules = {}

        if 'order_states' in self.config:
            for state_name, state_config in self.config['order_states'].items():
                try:
                    state = OrderState(state_name)
                    rules[state] = {
                        'description': state_config.get('description', ''),
                        'next_states': [OrderState(s) for s in state_config.get('next_states', [])],
                        'sla_hours': state_config.get('sla_hours', 24)
                    }
                except ValueError:
                    self.logger.warning(f"Unknown order state: {state_name}")

        return rules

    def create_order(self, customer_email: str, customer_name: str, items: List[OrderItem],
                    priority: int = 3, metadata: Dict = None) -> Order:
        """Create a new order"""
        order_id = f"ORD_{int(time.time())}_{len(self.orders) + 1}"

        # Calculate total amount
        total_amount = sum(item.total_price for item in items)

        # Determine SLA based on priority and amount
        sla_hours = self._calculate_sla(priority, total_amount)

        order = Order(
            id=order_id,
            customer_email=customer_email,
            customer_name=customer_name,
            items=items,
            total_amount=total_amount,
            priority=priority,
            sla_hours=sla_hours,
            current_state=OrderState.CREATED,
            metadata=metadata or {}
        )

        # Add creation transition
        order.add_transition(
            OrderState.CREATED,
            "OrderSystem",
            "Order created from email/PDF",
            {"source": "email_processing", "total_amount": total_amount}
        )

        # Store order
        self.orders[order_id] = order
        self._save_order(order)

        self.logger.info(f"Created order {order_id} for {customer_name} (€{total_amount:.2f})")
        return order

    def _calculate_sla(self, priority: int, amount: float) -> int:
        """Calculate SLA hours based on priority and order value"""
        # High-value orders get priority treatment
        if amount > 10000:
            return 4  # 4 hours for high-value
        elif priority == 1:
            return 2  # 2 hours for critical
        elif priority == 2:
            return 12  # 12 hours for high
        else:
            return 24  # 24 hours for normal

    def transition_order(self, order_id: str, to_state: OrderState, agent: str,
                        reason: str, metadata: Dict = None) -> bool:
        """Transition an order to a new state"""
        if order_id not in self.orders:
            self.logger.error(f"Order not found: {order_id}")
            return False

        order = self.orders[order_id]
        current_state = order.current_state

        # Validate transition
        if not self._is_valid_transition(current_state, to_state):
            self.logger.error(f"Invalid transition from {current_state.value} to {to_state.value}")
            return False

        # Perform transition
        order.add_transition(to_state, agent, reason, metadata)
        self._save_order(order)

        # Emit event for other systems
        self._emit_state_change_event(order, current_state, to_state)

        self.logger.info(f"Order {order_id} transitioned from {current_state.value} to {to_state.value}")
        return True

    def _is_valid_transition(self, from_state: OrderState, to_state: OrderState) -> bool:
        """Check if state transition is valid according to business rules"""
        if from_state not in self.state_rules:
            return False

        valid_next_states = self.state_rules[from_state]['next_states']
        return to_state in valid_next_states

    def _emit_state_change_event(self, order: Order, from_state: OrderState, to_state: OrderState):
        """Emit event for state change (for dashboard and other systems)"""
        event = {
            'type': 'order_state_change',
            'order_id': order.id,
            'from_state': from_state.value,
            'to_state': to_state.value,
            'timestamp': time.time(),
            'customer': order.customer_name,
            'total_amount': order.total_amount,
            'priority': order.priority
        }

        # Save event to events directory for dashboard
        events_dir = "data/events"
        os.makedirs(events_dir, exist_ok=True)

        event_file = f"{events_dir}/order_event_{int(time.time())}.json"
        with open(event_file, 'w') as f:
            json.dump(event, f, indent=2)

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self.orders.get(order_id)

    def get_orders_by_state(self, state: OrderState) -> List[Order]:
        """Get all orders in a specific state"""
        return [order for order in self.orders.values() if order.current_state == state]

    def get_overdue_orders(self) -> List[Order]:
        """Get orders that are overdue based on SLA"""
        overdue = []
        current_time = time.time()

        for order in self.orders.values():
            if order.current_state == OrderState.CLOSED:
                continue

            # Check if order is overdue
            time_in_current_state = current_time - order.created_at
            if len(order.history) > 0:
                time_in_current_state = current_time - order.history[-1].timestamp

            state_sla = self.state_rules.get(order.current_state, {}).get('sla_hours', 24)
            if time_in_current_state > (state_sla * 3600):  # Convert hours to seconds
                overdue.append(order)

        return overdue

    def get_order_statistics(self) -> Dict[str, Any]:
        """Get order processing statistics"""
        stats = {
            'total_orders': len(self.orders),
            'by_state': {},
            'by_priority': {1: 0, 2: 0, 3: 0, 4: 0},
            'overdue_count': len(self.get_overdue_orders()),
            'avg_processing_time': 0,
            'total_value': 0
        }

        # Count by state
        for state in OrderState:
            stats['by_state'][state.value] = len(self.get_orders_by_state(state))

        # Count by priority and calculate totals
        processing_times = []
        for order in self.orders.values():
            stats['by_priority'][order.priority] += 1
            stats['total_value'] += order.total_amount

            # Calculate processing time for completed orders
            if order.current_state == OrderState.CLOSED and order.history:
                processing_time = order.history[-1].timestamp - order.created_at
                processing_times.append(processing_time)

        # Calculate average processing time
        if processing_times:
            stats['avg_processing_time'] = sum(processing_times) / len(processing_times) / 3600  # Hours

        return stats

    def _save_order(self, order: Order):
        """Save order to persistent storage"""
        try:
            order_file = f"{self.storage_dir}/{order.id}.json"

            order_data = {
                'id': order.id,
                'customer_email': order.customer_email,
                'customer_name': order.customer_name,
                'items': [
                    {
                        'sku': item.sku,
                        'name': item.name,
                        'quantity': item.quantity,
                        'unit_price': item.unit_price,
                        'total_price': item.total_price
                    } for item in order.items
                ],
                'total_amount': order.total_amount,
                'priority': order.priority,
                'sla_hours': order.sla_hours,
                'current_state': order.current_state.value,
                'created_at': order.created_at,
                'history': [
                    {
                        'from_state': t.from_state.value,
                        'to_state': t.to_state.value,
                        'timestamp': t.timestamp,
                        'agent': t.agent,
                        'reason': t.reason,
                        'metadata': t.metadata
                    } for t in order.history
                ],
                'metadata': order.metadata
            }

            with open(order_file, 'w') as f:
                json.dump(order_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving order {order.id}: {e}")

    def load_orders(self):
        """Load orders from persistent storage"""
        try:
            if not os.path.exists(self.storage_dir):
                return

            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    with open(f"{self.storage_dir}/{filename}", 'r') as f:
                        order_data = json.load(f)

                        # Reconstruct OrderItem objects
                        items = []
                        for item_data in order_data.get('items', []):
                            item = OrderItem(
                                sku=item_data['sku'],
                                name=item_data['name'],
                                quantity=item_data['quantity'],
                                unit_price=item_data['unit_price'],
                                total_price=item_data['total_price']
                            )
                            items.append(item)

                        # Reconstruct StateTransition objects
                        history = []
                        for transition_data in order_data.get('history', []):
                            transition = StateTransition(
                                from_state=OrderState(transition_data['from_state']),
                                to_state=OrderState(transition_data['to_state']),
                                timestamp=transition_data['timestamp'],
                                agent=transition_data['agent'],
                                reason=transition_data['reason'],
                                metadata=transition_data.get('metadata', {})
                            )
                            history.append(transition)

                        # Reconstruct Order object
                        order = Order(
                            id=order_data['id'],
                            customer_email=order_data['customer_email'],
                            customer_name=order_data['customer_name'],
                            items=items,
                            total_amount=order_data['total_amount'],
                            priority=order_data['priority'],
                            sla_hours=order_data['sla_hours'],
                            current_state=OrderState(order_data['current_state']),
                            history=history,
                            created_at=order_data['created_at'],
                            metadata=order_data.get('metadata', {})
                        )

                        # Add to in-memory storage
                        self.orders[order.id] = order

            self.logger.info(f"Loaded {len(self.orders)} orders from storage")
        except Exception as e:
            self.logger.error(f"Error loading orders: {e}")

# Demo usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create state machine
    state_machine = OrderStateMachine()

    # Demo order creation
    items = [
        OrderItem("BTN-001", "Premium Red Button", 100, 2.50, 250.00),
        OrderItem("BTN-002", "Blue Royal Button", 50, 5.00, 250.00)
    ]

    order = state_machine.create_order(
        "customer@example.com",
        "Demo Customer",
        items,
        priority=2
    )

    print(f"Created order: {order.id}")
    print(f"Current state: {order.current_state.value}")

    # Demo state transitions
    state_machine.transition_order(order.id, OrderState.CONFIRMED, "SalesAgent", "Customer confirmed order")
    state_machine.transition_order(order.id, OrderState.PLANNED, "ProductionAgent", "Production scheduled")

    # Show statistics
    stats = state_machine.get_order_statistics()
    print(f"Order statistics: {stats}")