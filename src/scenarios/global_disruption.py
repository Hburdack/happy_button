"""
Global Supply Chain Disruption Scenario Implementation
Release 3.0 - Weakness Injection System
Simulates major global disruption (Suez Canal blockage) affecting supply chains
"""

import asyncio
import logging
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .email_generator import scenario_email_generator

logger = logging.getLogger(__name__)

class DisruptionType(Enum):
    """Types of global disruptions"""
    SUEZ_CANAL_BLOCKAGE = "suez_canal_blockage"
    PORT_STRIKES = "port_strikes"
    NATURAL_DISASTERS = "natural_disasters"
    GEOPOLITICAL_TENSIONS = "geopolitical_tensions"
    PANDEMIC_RESTRICTIONS = "pandemic_restrictions"

class RouteType(Enum):
    """Supply route types"""
    PRIMARY_SUEZ = "asia_europe_suez"
    ALTERNATIVE_CAPE = "asia_europe_cape"
    OVERLAND_RAIL = "overland_rail"
    AIR_FREIGHT = "air_freight"
    LOCAL_SOURCING = "local_sourcing"

class OrderPriority(Enum):
    """Order priority levels"""
    STANDARD = "standard"
    EXPEDITE = "expedite"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class AffectedOrder:
    """Represents an order affected by supply chain disruption"""
    order_id: str
    customer_name: str
    original_route: RouteType
    alternative_route: Optional[RouteType]
    original_delivery_days: int
    new_delivery_days: int
    cost_increase_percent: float
    priority: OrderPriority
    customer_impact: str
    rerouting_possible: bool
    customer_notified: bool
    escalation_required: bool
    timestamp: datetime
    generated_email_path: Optional[str] = None

class GlobalDisruption:
    """
    Simulates global supply chain disruptions affecting delivery and costs
    Models realistic supply chain failures and business impact
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_active = False
        self.affected_orders = []
        self.total_orders_affected = 0
        self.total_delay_days = 0
        self.total_cost_increase = 0.0
        self.customer_complaints = 0
        self.rerouting_attempts = 0

        # Extract configuration
        self.disruption_config = config.get('configuration', {})
        self.disruption_types = self.disruption_config.get('disruption_types', {})
        self.supply_routes = self.disruption_config.get('supply_routes', {})
        self.impact_calculation = self.disruption_config.get('impact_calculation', {})

        # Current active disruption
        self.active_disruption = None
        self.disruption_severity = 1.0

        logger.info("Global Disruption scenario initialized")

    async def execute_scenario(self, duration_seconds: int, metrics_callback=None) -> Dict[str, Any]:
        """Execute the global disruption scenario"""
        logger.info(f"Starting Global Disruption scenario for {duration_seconds} seconds")

        self.is_active = True
        start_time = time.time()

        # Select and activate a disruption
        await self._activate_disruption()

        # Scenario execution metrics
        execution_metrics = {
            'total_orders_affected': 0,
            'average_delay_days': 0.0,
            'average_cost_increase_percent': 0.0,
            'customer_complaints': 0,
            'rerouting_success_rate': 0.0,
            'on_time_delivery_rate': 0.0,
            'disruption_type': self.active_disruption.value if self.active_disruption else 'none',
            'disruption_severity': self.disruption_severity
        }

        try:
            while time.time() - start_time < duration_seconds and self.is_active:
                # Simulate orders being affected by the disruption
                await self._process_affected_orders_batch(execution_metrics)

                # Update metrics if callback provided
                if metrics_callback:
                    await metrics_callback(execution_metrics)

                # Wait before next batch (orders process continuously during disruption)
                await asyncio.sleep(random.uniform(30, 90))  # 30-90 second intervals

        except Exception as e:
            logger.error(f"Error in global disruption execution: {e}")
        finally:
            self.is_active = False
            logger.info("Global Disruption scenario completed")

        return execution_metrics

    async def _activate_disruption(self):
        """Activate a specific type of global disruption"""
        # Select disruption type based on configuration
        enabled_disruptions = []
        for disruption_name, disruption_config in self.disruption_types.items():
            if disruption_config.get('enabled', False):
                enabled_disruptions.append(disruption_name)

        if not enabled_disruptions:
            # Default to Suez Canal blockage if none configured
            self.active_disruption = DisruptionType.SUEZ_CANAL_BLOCKAGE
        else:
            disruption_name = random.choice(enabled_disruptions)
            self.active_disruption = DisruptionType(disruption_name)

        # Set disruption severity based on type
        if self.active_disruption == DisruptionType.SUEZ_CANAL_BLOCKAGE:
            self.disruption_severity = self.disruption_types.get('suez_canal_blockage', {}).get('delay_multiplier', 3.5)
        elif self.active_disruption == DisruptionType.PORT_STRIKES:
            self.disruption_severity = self.disruption_types.get('port_strikes', {}).get('delay_multiplier', 2.0)
        elif self.active_disruption == DisruptionType.NATURAL_DISASTERS:
            self.disruption_severity = self.disruption_types.get('natural_disasters', {}).get('delay_multiplier', 4.0)
        else:
            self.disruption_severity = 2.5

        logger.critical(f"GLOBAL DISRUPTION ACTIVATED: {self.active_disruption.value} (severity: {self.disruption_severity}x)")

    async def _process_affected_orders_batch(self, metrics: Dict[str, Any]):
        """Process a batch of orders affected by the disruption"""
        # During major disruptions, many orders are affected
        batch_size = random.randint(3, 8)

        for _ in range(batch_size):
            await self._create_affected_order(metrics)

    async def _create_affected_order(self, metrics: Dict[str, Any]):
        """Create a single affected order"""
        # Generate order details
        order_id = f"order_{int(time.time())}_{random.randint(1000, 9999)}"
        customer_name = self._generate_customer_name()
        priority = self._determine_order_priority()

        # Determine original route and impact
        original_route = self._determine_original_route()
        route_affected = self._is_route_affected(original_route)

        if not route_affected:
            return  # This order is not affected by current disruption

        # Calculate disruption impact
        original_delivery_days = self._get_route_delivery_days(original_route)
        alternative_route, new_delivery_days, cost_increase = await self._calculate_disruption_impact(
            original_route, original_delivery_days, priority
        )

        # Determine customer impact
        customer_impact = self._calculate_customer_impact(new_delivery_days, original_delivery_days, priority)

        # Check if rerouting is possible and customer notification
        rerouting_possible = alternative_route is not None
        customer_notified = random.random() < 0.8  # 80% of customers get notified
        escalation_required = customer_impact in ['severe', 'critical'] or priority in [OrderPriority.CRITICAL, OrderPriority.EMERGENCY]

        # Create affected order record
        affected_order = AffectedOrder(
            order_id=order_id,
            customer_name=customer_name,
            original_route=original_route,
            alternative_route=alternative_route,
            original_delivery_days=original_delivery_days,
            new_delivery_days=new_delivery_days,
            cost_increase_percent=cost_increase,
            priority=priority,
            customer_impact=customer_impact,
            rerouting_possible=rerouting_possible,
            customer_notified=customer_notified,
            escalation_required=escalation_required,
            timestamp=datetime.now()
        )

        self.affected_orders.append(affected_order)

        # Update metrics
        metrics['total_orders_affected'] += 1
        self.total_orders_affected += 1

        delay_days = new_delivery_days - original_delivery_days
        self.total_delay_days += delay_days

        self.total_cost_increase += cost_increase

        if customer_impact in ['severe', 'critical']:
            metrics['customer_complaints'] += 1
            self.customer_complaints += 1

        if rerouting_possible:
            self.rerouting_attempts += 1

        # Update calculated metrics
        all_delays = [o.new_delivery_days - o.original_delivery_days for o in self.affected_orders]
        metrics['average_delay_days'] = sum(all_delays) / len(all_delays)

        all_cost_increases = [o.cost_increase_percent for o in self.affected_orders]
        metrics['average_cost_increase_percent'] = sum(all_cost_increases) / len(all_cost_increases)

        metrics['rerouting_success_rate'] = (self.rerouting_attempts / self.total_orders_affected) * 100

        # Calculate on-time delivery rate (orders delivered within original timeframe)
        on_time_orders = sum(1 for o in self.affected_orders if o.new_delivery_days <= o.original_delivery_days)
        metrics['on_time_delivery_rate'] = (on_time_orders / self.total_orders_affected) * 100

        logger.warning(f"Order affected: {order_id}, +{delay_days} days delay, +{cost_increase:.1f}% cost")

        # Generate scenario email for this affected order
        await self._generate_scenario_email(affected_order)

        # Simulate additional effects for critical orders
        if priority in [OrderPriority.CRITICAL, OrderPriority.EMERGENCY]:
            await self._handle_critical_order_impact(affected_order, metrics)

    async def _generate_scenario_email(self, affected_order: AffectedOrder):
        """Generate a visible scenario email for this affected order"""
        try:
            # Map affected order scenarios to email types based on severity
            delay_days = affected_order.new_delivery_days - affected_order.original_delivery_days

            if affected_order.priority in [OrderPriority.CRITICAL, OrderPriority.EMERGENCY]:
                email_type = 'complaint'  # Critical/Emergency orders generate complaints when delayed
            elif delay_days > 14:  # Major delays
                email_type = 'complaint'
            else:
                email_type = 'customer_inquiry'  # Regular inquiries about delays

            # Create delay information for email generation
            delay_info = {
                'delay_minutes': delay_days * 24 * 60,  # Convert days to minutes for template
                'sla_minutes': affected_order.original_delivery_days * 24 * 60,
                'delay_days': delay_days,
                'original_delivery_days': affected_order.original_delivery_days,
                'new_delivery_days': affected_order.new_delivery_days,
                'cost_increase_percent': affected_order.cost_increase_percent,
                'priority': affected_order.priority.value,
                'customer_impact': affected_order.customer_impact,
                'disruption_type': self.active_disruption.value,
                'disruption_severity': self.disruption_severity,
                'original_route': affected_order.original_route.value,
                'alternative_route': affected_order.alternative_route.value if affected_order.alternative_route else None,
                'rerouting_possible': affected_order.rerouting_possible,
                'escalation_required': affected_order.escalation_required,
                'scenario_id': affected_order.order_id
            }

            # Generate the scenario email
            scenario_email = scenario_email_generator.generate_scenario_email(
                scenario_type='late_triage',  # Reuse late_triage templates for disruption delays
                email_type=email_type,
                delay_info=delay_info
            )

            if scenario_email:
                # Save the email to filesystem for integration with email interfaces
                filepath = scenario_email_generator.save_scenario_email(scenario_email)

                if filepath:
                    logger.info(f"📧 Generated disruption scenario email for order {affected_order.order_id}: {scenario_email['subject'][:50]}...")

                    # Store reference in affected order record for tracking
                    affected_order.generated_email_path = filepath
                else:
                    logger.warning(f"Failed to save disruption scenario email for order {affected_order.order_id}")
            else:
                logger.warning(f"Failed to generate disruption scenario email for order {affected_order.order_id}")

        except Exception as e:
            logger.error(f"Error generating disruption scenario email for order {affected_order.order_id}: {e}")

    def _generate_customer_name(self) -> str:
        """Generate realistic customer name"""
        companies = [
            "Global Manufacturing Ltd", "International Trading Corp", "European Distribution",
            "Strategic Imports Inc", "Premium Supply Chain", "Executive Logistics",
            "Continental Partners", "Worldwide Sourcing", "Elite Manufacturing",
            "Advanced Industries Group", "Major Retailer Chain", "Critical Infrastructure Co"
        ]
        return random.choice(companies)

    def _determine_order_priority(self) -> OrderPriority:
        """Determine order priority based on realistic distribution"""
        # Most orders are standard, fewer are expedite/critical
        priorities = list(OrderPriority)
        weights = [60, 25, 12, 3]  # standard, expedite, critical, emergency
        return random.choices(priorities, weights=weights)[0]

    def _determine_original_route(self) -> RouteType:
        """Determine original shipping route"""
        # Most orders use primary Suez route before disruption
        routes = list(RouteType)
        weights = [70, 15, 10, 3, 2]  # primary_suez, alternative_cape, overland_rail, air_freight, local_sourcing
        return random.choices(routes, weights=weights)[0]

    def _is_route_affected(self, route: RouteType) -> bool:
        """Check if route is affected by current disruption"""
        if self.active_disruption == DisruptionType.SUEZ_CANAL_BLOCKAGE:
            return route == RouteType.PRIMARY_SUEZ
        elif self.active_disruption == DisruptionType.PORT_STRIKES:
            # Port strikes affect multiple routes
            affected_routes = [RouteType.PRIMARY_SUEZ, RouteType.ALTERNATIVE_CAPE]
            return route in affected_routes
        elif self.active_disruption == DisruptionType.NATURAL_DISASTERS:
            # Natural disasters can affect various routes
            return route in [RouteType.PRIMARY_SUEZ, RouteType.OVERLAND_RAIL]
        else:
            return route == RouteType.PRIMARY_SUEZ

    def _get_route_delivery_days(self, route: RouteType) -> int:
        """Get normal delivery days for a route"""
        route_days = {
            RouteType.PRIMARY_SUEZ: 14,
            RouteType.ALTERNATIVE_CAPE: 28,
            RouteType.OVERLAND_RAIL: 35,
            RouteType.AIR_FREIGHT: 3,
            RouteType.LOCAL_SOURCING: 7
        }
        return route_days.get(route, 14)

    async def _calculate_disruption_impact(self, original_route: RouteType, original_days: int, priority: OrderPriority) -> tuple[Optional[RouteType], int, float]:
        """Calculate the impact of disruption on delivery and cost"""
        # Try to find alternative route
        alternative_route = self._find_alternative_route(original_route, priority)

        if alternative_route:
            # Calculate new delivery time and cost
            base_days = self._get_route_delivery_days(alternative_route)

            # Add disruption delays
            disruption_delay = int(base_days * (self.disruption_severity - 1))
            new_delivery_days = base_days + disruption_delay

            # Calculate cost increase
            cost_increase = self._calculate_cost_increase(original_route, alternative_route)

        else:
            # No alternative route available - major delays
            new_delivery_days = int(original_days * self.disruption_severity * 1.5)
            cost_increase = random.uniform(50, 150)  # 50-150% cost increase

        return alternative_route, new_delivery_days, cost_increase

    def _find_alternative_route(self, original_route: RouteType, priority: OrderPriority) -> Optional[RouteType]:
        """Find alternative route based on priority and availability"""
        if original_route == RouteType.PRIMARY_SUEZ:
            if priority in [OrderPriority.EMERGENCY, OrderPriority.CRITICAL]:
                # High priority orders can use air freight
                if random.random() < 0.7:  # 70% chance air freight available
                    return RouteType.AIR_FREIGHT
                else:
                    return RouteType.ALTERNATIVE_CAPE
            else:
                # Standard orders use Cape route if available
                if random.random() < 0.6:  # 60% chance Cape route available
                    return RouteType.ALTERNATIVE_CAPE
                elif random.random() < 0.3:  # 30% chance overland rail
                    return RouteType.OVERLAND_RAIL
                else:
                    return None  # No alternative available

        elif original_route == RouteType.ALTERNATIVE_CAPE:
            # If Cape route affected, very limited options
            if priority == OrderPriority.EMERGENCY:
                return RouteType.AIR_FREIGHT
            else:
                return RouteType.OVERLAND_RAIL if random.random() < 0.4 else None

        return None

    def _calculate_cost_increase(self, original_route: RouteType, alternative_route: RouteType) -> float:
        """Calculate cost increase percentage for route change"""
        # Base cost increases for route changes
        cost_multipliers = {
            (RouteType.PRIMARY_SUEZ, RouteType.ALTERNATIVE_CAPE): random.uniform(25, 40),
            (RouteType.PRIMARY_SUEZ, RouteType.AIR_FREIGHT): random.uniform(200, 400),
            (RouteType.PRIMARY_SUEZ, RouteType.OVERLAND_RAIL): random.uniform(15, 30),
            (RouteType.ALTERNATIVE_CAPE, RouteType.AIR_FREIGHT): random.uniform(300, 500),
            (RouteType.ALTERNATIVE_CAPE, RouteType.OVERLAND_RAIL): random.uniform(20, 35)
        }

        route_pair = (original_route, alternative_route)
        return cost_multipliers.get(route_pair, random.uniform(30, 60))

    def _calculate_customer_impact(self, new_days: int, original_days: int, priority: OrderPriority) -> str:
        """Calculate customer impact level"""
        delay_ratio = new_days / original_days

        if delay_ratio <= 1.2:
            return 'minimal'
        elif delay_ratio <= 1.5:
            return 'moderate'
        elif delay_ratio <= 2.0:
            return 'significant'
        elif delay_ratio <= 3.0:
            return 'severe'
        else:
            return 'critical'

    async def _handle_critical_order_impact(self, affected_order: AffectedOrder, metrics: Dict[str, Any]):
        """Handle impact of critical orders being affected"""
        logger.critical(f"CRITICAL ORDER AFFECTED: {affected_order.order_id} - {affected_order.priority.value}")

        # Critical orders can trigger:
        # 1. Emergency escalation
        if affected_order.priority == OrderPriority.EMERGENCY:
            await self._trigger_emergency_escalation(affected_order)

        # 2. Customer relationship damage
        if affected_order.customer_impact in ['severe', 'critical']:
            await self._trigger_customer_relationship_damage(affected_order)

        # 3. Supply chain emergency protocols
        if affected_order.priority in [OrderPriority.CRITICAL, OrderPriority.EMERGENCY]:
            await self._activate_emergency_protocols(affected_order)

    async def _trigger_emergency_escalation(self, affected_order: AffectedOrder):
        """Trigger emergency escalation procedures"""
        logger.critical(f"EMERGENCY ESCALATION: {affected_order.order_id} requires immediate executive attention")

    async def _trigger_customer_relationship_damage(self, affected_order: AffectedOrder):
        """Handle customer relationship damage from severe delays"""
        logger.warning(f"CUSTOMER RELATIONSHIP DAMAGE: {affected_order.customer_name} experiencing {affected_order.customer_impact} impact")

    async def _activate_emergency_protocols(self, affected_order: AffectedOrder):
        """Activate emergency supply chain protocols"""
        logger.warning(f"EMERGENCY PROTOCOLS: Activating emergency procedures for {affected_order.order_id}")

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current scenario metrics"""
        if not self.affected_orders:
            return {
                'total_affected': 0,
                'average_delay': 0.0,
                'average_cost_increase': 0.0,
                'disruption_type': self.active_disruption.value if self.active_disruption else 'none',
                'active': self.is_active
            }

        delays = [o.new_delivery_days - o.original_delivery_days for o in self.affected_orders]
        cost_increases = [o.cost_increase_percent for o in self.affected_orders]

        return {
            'total_affected': len(self.affected_orders),
            'average_delay_days': sum(delays) / len(delays),
            'average_cost_increase_percent': sum(cost_increases) / len(cost_increases),
            'customer_complaints': self.customer_complaints,
            'rerouting_success_rate': (self.rerouting_attempts / self.total_orders_affected) * 100 if self.total_orders_affected > 0 else 0,
            'disruption_type': self.active_disruption.value if self.active_disruption else 'none',
            'disruption_severity': self.disruption_severity,
            'active': self.is_active
        }

    def get_kpi_impact(self) -> Dict[str, float]:
        """Calculate KPI degradation caused by global disruption"""
        if not self.affected_orders:
            return {}

        # On-time delivery calculation
        baseline_on_time = 95  # 95% baseline on-time delivery
        on_time_orders = sum(1 for o in self.affected_orders if o.new_delivery_days <= o.original_delivery_days)
        current_on_time = (on_time_orders / len(self.affected_orders)) * 100

        # Customer satisfaction impact
        baseline_satisfaction = 90
        satisfaction_drop = (self.customer_complaints * 15) + (self.total_orders_affected * 2)
        customer_satisfaction = max(40, baseline_satisfaction - satisfaction_drop)

        # Cost efficiency impact
        baseline_cost_efficiency = 85
        avg_cost_increase = sum(o.cost_increase_percent for o in self.affected_orders) / len(self.affected_orders)
        cost_efficiency = max(30, baseline_cost_efficiency - (avg_cost_increase / 2))

        # Supply chain resilience
        baseline_resilience = 80
        resilience_drop = (self.total_orders_affected * 3) + (self.customer_complaints * 10)
        supply_chain_resilience = max(20, baseline_resilience - resilience_drop)

        return {
            'on_time_delivery_percent': current_on_time,
            'customer_satisfaction_score': customer_satisfaction,
            'cost_efficiency_score': cost_efficiency,
            'supply_chain_resilience_score': supply_chain_resilience,
            'delivery_performance_score': max(30, 100 - (sum(o.new_delivery_days - o.original_delivery_days for o in self.affected_orders) / len(self.affected_orders) * 2)),
            'operational_efficiency_score': max(25, 85 - avg_cost_increase)
        }

    def stop_scenario(self):
        """Stop the running scenario"""
        logger.info("Stopping Global Disruption scenario")
        self.is_active = False

    def reset_scenario(self):
        """Reset scenario to initial state"""
        logger.info("Resetting Global Disruption scenario")
        self.is_active = False
        self.affected_orders = []
        self.total_orders_affected = 0
        self.total_delay_days = 0
        self.total_cost_increase = 0.0
        self.customer_complaints = 0
        self.rerouting_attempts = 0
        self.active_disruption = None
        self.disruption_severity = 1.0

    def get_detailed_report(self) -> Dict[str, Any]:
        """Generate detailed scenario report"""
        if not self.affected_orders:
            return {'message': 'No orders affected yet'}

        # Categorize orders by priority
        orders_by_priority = {}
        for order in self.affected_orders:
            priority = order.priority.value
            if priority not in orders_by_priority:
                orders_by_priority[priority] = []
            orders_by_priority[priority].append(order)

        # Calculate route distribution
        route_distribution = {}
        for order in self.affected_orders:
            route = order.original_route.value
            route_distribution[route] = route_distribution.get(route, 0) + 1

        # Calculate financial impact
        total_orders = len(self.affected_orders)
        delays = [o.new_delivery_days - o.original_delivery_days for o in self.affected_orders]
        cost_increases = [o.cost_increase_percent for o in self.affected_orders]

        return {
            'scenario_summary': {
                'disruption_type': self.active_disruption.value if self.active_disruption else 'none',
                'disruption_severity': self.disruption_severity,
                'total_orders_affected': total_orders,
                'customer_complaints': self.customer_complaints,
                'rerouting_attempts': self.rerouting_attempts
            },
            'priority_breakdown': {
                priority: len(orders) for priority, orders in orders_by_priority.items()
            },
            'route_impact': route_distribution,
            'delay_analysis': {
                'average_delay_days': sum(delays) / len(delays),
                'max_delay_days': max(delays),
                'total_delay_days': sum(delays)
            },
            'cost_analysis': {
                'average_cost_increase_percent': sum(cost_increases) / len(cost_increases),
                'max_cost_increase_percent': max(cost_increases),
                'orders_with_significant_cost_increase': sum(1 for c in cost_increases if c > 50)
            },
            'kpi_impact': self.get_kpi_impact(),
            'business_impact': {
                'supply_chain_recovery_time_weeks': max(4, self.disruption_severity * 2),
                'customer_retention_risk_percent': min(30, self.customer_complaints * 5),
                'operational_cost_increase_percent': sum(cost_increases) / len(cost_increases) if cost_increases else 0
            }
        }