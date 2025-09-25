#!/usr/bin/env python3
"""
History Seeder for Happy Buttons Release 2
Generates realistic 30-day order simulation data with proper state transitions
Creates comprehensive business simulation with multiple customer profiles
"""

import sys
import os
import time
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import asdict

sys.path.insert(0, '/home/pi/happy_button/src')
from services.order.state_machine import OrderStateMachine, OrderState, OrderItem

class HistorySeeder:
    """Generates realistic business simulation data for 30-day period"""

    def __init__(self, config_path: str = "src/sim/config/company_release2.yaml"):
        self.state_machine = OrderStateMachine(config_path)
        self.customers = self._load_customer_profiles()
        self.products = self._load_product_catalog()
        self.agents = self._load_agent_profiles()

        # Simulation parameters
        self.simulation_days = 30
        self.orders_per_day_range = (5, 15)  # Realistic order volume
        self.completion_probability = 0.8   # 80% orders reach CLOSED state

    def _load_customer_profiles(self) -> List[Dict]:
        """Load realistic customer profiles for simulation"""
        return [
            {
                "name": "BMW Manufacturing GmbH",
                "email": "orders@bmw-manufacturing.com",
                "type": "OEM",
                "priority": 1,
                "order_frequency": 3,  # Orders per week
                "avg_order_value": 15000,
                "product_preferences": ["BTN-PREM-", "BTN-GOLD-"]
            },
            {
                "name": "Mercedes-Benz Parts Division",
                "email": "procurement@mercedes-benz.com",
                "type": "OEM",
                "priority": 1,
                "order_frequency": 2,
                "avg_order_value": 12000,
                "product_preferences": ["BTN-PLAT-", "BTN-PREM-"]
            },
            {
                "name": "Audi AG Production",
                "email": "parts@audi.de",
                "type": "OEM",
                "priority": 1,
                "order_frequency": 4,
                "avg_order_value": 18000,
                "product_preferences": ["BTN-GOLD-", "BTN-DIAM-"]
            },
            {
                "name": "Volkswagen Group Services",
                "email": "orders@vw-group.com",
                "type": "Enterprise",
                "priority": 2,
                "order_frequency": 2,
                "avg_order_value": 8000,
                "product_preferences": ["BTN-STD-", "BTN-PREM-"]
            },
            {
                "name": "Bosch GmbH",
                "email": "purchasing@bosch.com",
                "type": "Supplier",
                "priority": 2,
                "order_frequency": 3,
                "avg_order_value": 5500,
                "product_preferences": ["BTN-STD-", "BTN-IND-"]
            },
            {
                "name": "Siemens AG",
                "email": "procurement@siemens.com",
                "type": "Enterprise",
                "priority": 2,
                "order_frequency": 1,
                "avg_order_value": 7200,
                "product_preferences": ["BTN-IND-", "BTN-TECH-"]
            },
            {
                "name": "Continental Automotive",
                "email": "orders@continental.com",
                "type": "Supplier",
                "priority": 2,
                "order_frequency": 2,
                "avg_order_value": 4800,
                "product_preferences": ["BTN-STD-", "BTN-AUTO-"]
            },
            {
                "name": "ZF Friedrichshafen AG",
                "email": "purchasing@zf.com",
                "type": "Enterprise",
                "priority": 3,
                "order_frequency": 1,
                "avg_order_value": 3200,
                "product_preferences": ["BTN-STD-", "BTN-MECH-"]
            },
            {
                "name": "MAHLE GmbH",
                "email": "orders@mahle.com",
                "type": "SME",
                "priority": 3,
                "order_frequency": 2,
                "avg_order_value": 2800,
                "product_preferences": ["BTN-STD-", "BTN-BASIC-"]
            },
            {
                "name": "Schaeffler Group",
                "email": "procurement@schaeffler.com",
                "type": "Enterprise",
                "priority": 3,
                "order_frequency": 1,
                "avg_order_value": 3800,
                "product_preferences": ["BTN-IND-", "BTN-BEAR-"]
            }
        ]

    def _load_product_catalog(self) -> List[Dict]:
        """Load comprehensive product catalog"""
        return [
            {"sku": "BTN-PREM-001", "name": "Premium Royal Blue Button", "price": 3.50, "category": "Premium"},
            {"sku": "BTN-GOLD-002", "name": "Gold Plated Button", "price": 8.00, "category": "Luxury"},
            {"sku": "BTN-PLAT-003", "name": "Platinum Elite Button", "price": 12.00, "category": "Luxury"},
            {"sku": "BTN-DIAM-004", "name": "Diamond Accent Button", "price": 25.00, "category": "Luxury"},
            {"sku": "BTN-STD-101", "name": "Standard Black Button", "price": 1.50, "category": "Standard"},
            {"sku": "BTN-STD-102", "name": "Standard White Button", "price": 1.50, "category": "Standard"},
            {"sku": "BTN-STD-103", "name": "Standard Silver Button", "price": 1.80, "category": "Standard"},
            {"sku": "BTN-IND-201", "name": "Industrial Heavy Duty Button", "price": 4.20, "category": "Industrial"},
            {"sku": "BTN-TECH-301", "name": "Tech Series Smart Button", "price": 15.50, "category": "Technology"},
            {"sku": "BTN-AUTO-401", "name": "Automotive Grade Button", "price": 6.80, "category": "Automotive"},
            {"sku": "BTN-MECH-501", "name": "Mechanical Switch Button", "price": 9.20, "category": "Mechanical"},
            {"sku": "BTN-BASIC-001", "name": "Basic Economy Button", "price": 0.95, "category": "Economy"},
            {"sku": "BTN-BEAR-601", "name": "Bearing Integrated Button", "price": 11.30, "category": "Specialized"}
        ]

    def _load_agent_profiles(self) -> List[str]:
        """Load agent profiles for realistic state transitions"""
        return [
            "SalesAgent", "ProductionAgent", "QualityAgent", "LogisticsAgent",
            "FinanceAgent", "CustomerService", "ProductionPlanning",
            "QualityInspector", "ShippingCoordinator", "AccountsReceivable"
        ]

    def generate_order_items(self, customer: Dict, order_value: float) -> List[OrderItem]:
        """Generate realistic order items for a customer"""
        items = []
        remaining_value = order_value
        preferences = customer["product_preferences"]

        while remaining_value > 50 and len(items) < 8:  # Max 8 items per order
            # Select product based on customer preferences
            available_products = [p for p in self.products if any(pref in p["sku"] for pref in preferences)]
            if not available_products:
                available_products = self.products

            product = random.choice(available_products)

            # Calculate realistic quantity
            max_quantity = min(int(remaining_value / product["price"]), 2000)
            if max_quantity < 50:  # Minimum viable order
                break

            # Ensure minimum quantity is at least 50 but not more than max_quantity
            min_quantity = min(50, max_quantity)
            quantity = random.randint(min_quantity, max_quantity)
            total_price = quantity * product["price"]

            item = OrderItem(
                sku=product["sku"],
                name=product["name"],
                quantity=quantity,
                unit_price=product["price"],
                total_price=total_price
            )

            items.append(item)
            remaining_value -= total_price

        return items

    def simulate_state_transitions(self, order_id: str, start_time: float, should_complete: bool) -> List[Dict]:
        """Simulate realistic state transitions with proper timing"""
        transitions = []
        current_time = start_time

        # Define realistic transition timing (in hours)
        transition_timings = {
            OrderState.CONFIRMED: random.uniform(0.5, 4),      # 30min - 4h
            OrderState.PLANNED: random.uniform(2, 12),         # 2h - 12h
            OrderState.IN_PRODUCTION: random.uniform(4, 48),   # 4h - 48h
            OrderState.PRODUCED: random.uniform(1, 8),         # 1h - 8h
            OrderState.PACKED: random.uniform(0.5, 4),         # 30min - 4h
            OrderState.SHIPPED: random.uniform(1, 6),          # 1h - 6h
            OrderState.DELIVERED: random.uniform(24, 72),      # 1-3 days
            OrderState.INVOICED: random.uniform(2, 24),        # 2h - 24h
            OrderState.CLOSED: random.uniform(240, 720)        # 10-30 days
        }

        # Define state-specific agents and reasons
        state_handlers = {
            OrderState.CONFIRMED: ("SalesAgent", "Customer confirmed order via email"),
            OrderState.PLANNED: ("ProductionPlanning", "Production scheduled and materials reserved"),
            OrderState.IN_PRODUCTION: ("ProductionAgent", "Manufacturing commenced"),
            OrderState.PRODUCED: ("QualityInspector", "Quality inspection passed"),
            OrderState.PACKED: ("LogisticsAgent", "Order packed and labeled"),
            OrderState.SHIPPED: ("ShippingCoordinator", "Shipped via DHL Express"),
            OrderState.DELIVERED: ("LogisticsAgent", "Delivery confirmed by recipient"),
            OrderState.INVOICED: ("AccountsReceivable", "Invoice generated and sent"),
            OrderState.CLOSED: ("FinanceAgent", "Payment received and processed")
        }

        # Execute transitions
        order_states = list(OrderState)
        for i, target_state in enumerate(order_states[1:], 1):  # Skip CREATED
            if not should_complete and i >= 7 and random.random() > 0.3:  # Some orders don't complete
                break

            # Add time delay
            delay_hours = transition_timings.get(target_state, 2)
            current_time += delay_hours * 3600  # Convert to seconds

            agent, reason = state_handlers.get(target_state, ("SystemAgent", "Automated transition"))

            # Generate realistic metadata
            metadata = self._generate_transition_metadata(target_state, current_time)

            success = self.state_machine.transition_order(order_id, target_state, agent, reason, metadata)
            if success:
                transitions.append({
                    "state": target_state.value,
                    "timestamp": current_time,
                    "agent": agent,
                    "reason": reason,
                    "metadata": metadata
                })
            else:
                break  # Stop if transition fails

        return transitions

    def _generate_transition_metadata(self, state: OrderState, timestamp: float) -> Dict[str, Any]:
        """Generate realistic metadata for each state transition"""
        metadata = {"simulation_generated": True, "timestamp": timestamp}

        if state == OrderState.CONFIRMED:
            metadata.update({
                "confirmation_method": random.choice(["email_reply", "phone_call", "portal_confirmation"]),
                "delivery_address": random.choice(["Main Plant", "Distribution Center", "Regional Office"]),
                "special_instructions": random.choice([None, "Urgent delivery", "Quality critical", "Prototype order"])
            })
        elif state == OrderState.PLANNED:
            metadata.update({
                "production_slot": f"2025-01-{random.randint(10, 28)} {random.randint(8, 16)}:00",
                "assigned_line": random.choice(["Line A", "Line B", "Line C", "Special Line"]),
                "estimated_duration": f"{random.randint(8, 72)} hours"
            })
        elif state == OrderState.IN_PRODUCTION:
            metadata.update({
                "batch_number": f"BATCH_2025_{random.randint(100, 999)}",
                "quality_inspector": random.choice(["Hans Weber", "Maria Schmidt", "Klaus Mueller"]),
                "materials_reserved": True,
                "production_notes": random.choice([None, "Rush order", "Extra QC required"])
            })
        elif state == OrderState.PRODUCED:
            metadata.update({
                "qa_inspector": random.choice(["Maria Schmidt", "Thomas Klein", "Andrea Wagner"]),
                "quality_score": random.choice(["A+", "A", "A-", "B+"]),
                "defect_rate": f"{random.uniform(0, 0.1):.3f}%",
                "batch_test_results": "PASSED"
            })
        elif state == OrderState.PACKED:
            metadata.update({
                "package_id": f"PKG_2025_{random.randint(1000, 9999)}",
                "weight_kg": round(random.uniform(5, 50), 1),
                "dimensions": f"{random.randint(20, 80)}x{random.randint(15, 60)}x{random.randint(10, 30)}cm",
                "packaging_type": random.choice(["Standard Box", "Reinforced Box", "Protective Foam"])
            })
        elif state == OrderState.SHIPPED:
            metadata.update({
                "tracking_number": f"DHL{random.randint(100000000, 999999999)}",
                "carrier": random.choice(["DHL Express", "DHL Standard", "UPS", "FedEx"]),
                "shipping_cost": round(random.uniform(15, 150), 2),
                "estimated_delivery": f"2025-01-{random.randint(15, 31)}"
            })
        elif state == OrderState.DELIVERED:
            metadata.update({
                "delivery_timestamp": f"2025-01-{random.randint(15, 31)} {random.randint(9, 17)}:{random.randint(0, 59):02d}",
                "recipient": random.choice(["Receiving Dept", "Warehouse Manager", "Production Manager"]),
                "signature": random.choice(["J. Mueller", "A. Schmidt", "K. Weber", "M. Klein"])
            })
        elif state == OrderState.INVOICED:
            metadata.update({
                "invoice_number": f"INV-2025-{random.randint(1000, 9999)}",
                "payment_terms": random.choice(["Net 30", "Net 14", "Net 7", "Immediate"]),
                "discount_applied": random.choice([0, 2, 5, 10]) if random.random() > 0.7 else 0
            })
        elif state == OrderState.CLOSED:
            metadata.update({
                "payment_date": f"2025-{random.randint(2, 3)}-{random.randint(1, 28):02d}",
                "payment_method": random.choice(["Bank Transfer", "Credit Card", "Check", "Wire Transfer"]),
                "transaction_id": f"TXN_{random.randint(100000, 999999)}"
            })

        return metadata

    def seed_historical_data(self) -> Dict[str, Any]:
        """Generate 30 days of realistic order history"""
        print("🌱 Starting Historical Data Seeding")
        print("=" * 50)

        # Clear existing orders for clean simulation
        self.state_machine.orders.clear()

        stats = {
            "total_orders": 0,
            "completed_orders": 0,
            "total_value": 0,
            "orders_by_customer": {},
            "orders_by_state": {state.value: 0 for state in OrderState},
            "daily_stats": []
        }

        # Generate orders for each day
        start_date = datetime.now() - timedelta(days=self.simulation_days)

        for day in range(self.simulation_days):
            current_date = start_date + timedelta(days=day)
            day_timestamp = current_date.timestamp()

            # Determine number of orders for this day (more on weekdays)
            is_weekend = current_date.weekday() >= 5
            order_multiplier = 0.3 if is_weekend else 1.0
            min_orders = max(1, int(self.orders_per_day_range[0] * order_multiplier))
            max_orders = int(self.orders_per_day_range[1] * order_multiplier)
            daily_orders = random.randint(min_orders, max_orders)

            day_stats = {
                "date": current_date.strftime("%Y-%m-%d"),
                "orders_created": daily_orders,
                "total_value": 0
            }

            print(f"📅 Day {day + 1}/{self.simulation_days}: {current_date.strftime('%Y-%m-%d')} - {daily_orders} orders")

            for order_num in range(daily_orders):
                # Select customer (weighted by order frequency)
                customer_weights = [c["order_frequency"] for c in self.customers]
                customer = random.choices(self.customers, weights=customer_weights)[0]

                # Generate order value with some variation
                base_value = customer["avg_order_value"]
                order_value = base_value * random.uniform(0.7, 1.5)  # ±50% variation

                # Generate order items
                items = self.generate_order_items(customer, order_value)
                if not items:
                    continue

                # Create order with historical timestamp
                order = self.state_machine.create_order(
                    customer_email=customer["email"],
                    customer_name=customer["name"],
                    items=items,
                    priority=customer["priority"],
                    metadata={
                        "customer_type": customer["type"],
                        "simulation_day": day + 1,
                        "historical_seed": True,
                        "original_timestamp": day_timestamp + (order_num * 1800)  # 30min intervals
                    }
                )

                # Override created_at to historical timestamp
                order.created_at = day_timestamp + (order_num * 1800)

                # Simulate state transitions
                should_complete = random.random() < self.completion_probability
                transitions = self.simulate_state_transitions(order.id, order.created_at, should_complete)

                # Update statistics
                stats["total_orders"] += 1
                stats["total_value"] += order.total_amount
                stats["orders_by_customer"][customer["name"]] = stats["orders_by_customer"].get(customer["name"], 0) + 1
                stats["orders_by_state"][order.current_state.value] += 1

                day_stats["total_value"] += order.total_amount

                if order.current_state == OrderState.CLOSED:
                    stats["completed_orders"] += 1

                print(f"  📦 {order.id}: {customer['name']} - €{order.total_amount:,.2f} - {order.current_state.value}")

            stats["daily_stats"].append(day_stats)

        # Save comprehensive simulation report
        self._save_simulation_report(stats)

        print("\n🎯 HISTORICAL DATA SEEDING COMPLETE")
        print("=" * 40)
        print(f"✅ Generated {stats['total_orders']} orders over {self.simulation_days} days")
        print(f"💰 Total Value: €{stats['total_value']:,.2f}")
        print(f"📊 Completion Rate: {(stats['completed_orders']/stats['total_orders']*100):.1f}%")
        print(f"🏭 Orders by State: {stats['orders_by_state']}")

        return stats

    def _save_simulation_report(self, stats: Dict[str, Any]):
        """Save detailed simulation report"""
        report_dir = "data/simulation"
        os.makedirs(report_dir, exist_ok=True)

        report_file = f"{report_dir}/history_seed_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)

        print(f"📄 Simulation report saved: {report_file}")

# Wiederholbares Tagesskript (Repeatable Daily Script)
class DailyOrderGenerator:
    """Daily order generation script for ongoing simulation"""

    def __init__(self):
        self.seeder = HistorySeeder()

    def generate_daily_orders(self, target_date: datetime = None) -> Dict[str, Any]:
        """Generate orders for a specific day"""
        if target_date is None:
            target_date = datetime.now()

        print(f"🏭 Generating daily orders for {target_date.strftime('%Y-%m-%d')}")

        # Determine daily order count
        is_weekend = target_date.weekday() >= 5
        base_range = (3, 8) if is_weekend else (5, 12)
        daily_orders = random.randint(*base_range)

        orders_created = []
        total_value = 0

        for i in range(daily_orders):
            # Select customer
            customer = random.choice(self.seeder.customers)

            # Generate order
            base_value = customer["avg_order_value"]
            order_value = base_value * random.uniform(0.8, 1.3)
            items = self.seeder.generate_order_items(customer, order_value)

            if items:
                order = self.seeder.state_machine.create_order(
                    customer_email=customer["email"],
                    customer_name=customer["name"],
                    items=items,
                    priority=customer["priority"],
                    metadata={"daily_generation": True, "generation_date": target_date.isoformat()}
                )

                orders_created.append({
                    "order_id": order.id,
                    "customer": customer["name"],
                    "value": order.total_amount,
                    "priority": order.priority
                })
                total_value += order.total_amount

        result = {
            "date": target_date.strftime('%Y-%m-%d'),
            "orders_generated": len(orders_created),
            "total_value": total_value,
            "orders": orders_created
        }

        print(f"✅ Generated {len(orders_created)} orders worth €{total_value:,.2f}")
        return result

# Demo execution
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    print("🚀 HAPPY BUTTONS HISTORY SEEDER")
    print("=" * 60)

    # Generate 30-day historical data
    seeder = HistorySeeder()
    historical_stats = seeder.seed_historical_data()

    print("\n" + "=" * 60)
    print("🎯 SEEDING SUMMARY")
    print(f"📈 Total Orders: {historical_stats['total_orders']}")
    print(f"💰 Total Revenue: €{historical_stats['total_value']:,.2f}")
    print(f"🏭 Completion Rate: {(historical_stats['completed_orders']/historical_stats['total_orders']*100):.1f}%")

    # Test daily generation
    print("\n🔄 Testing Daily Generator")
    daily_gen = DailyOrderGenerator()
    today_orders = daily_gen.generate_daily_orders()

    print("\n✅ HISTORY SEEDER COMPLETE - READY FOR DASHBOARD INTEGRATION!")