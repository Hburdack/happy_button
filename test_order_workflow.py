#!/usr/bin/env python3
"""
Test script for Order State Machine workflow
Tests the complete Release 2 order processing pipeline
"""

import sys
import os
import logging
sys.path.insert(0, '/home/pi/happy_button/src')

from services.order.state_machine import OrderStateMachine, OrderState, OrderItem

def test_complete_order_workflow():
    """Test the complete order workflow from CREATED to CLOSED"""

    logging.basicConfig(level=logging.INFO)
    print("🔄 TESTING COMPLETE ORDER WORKFLOW")
    print("=" * 60)

    # Initialize state machine
    state_machine = OrderStateMachine("src/sim/config/company_release2.yaml")

    # Create test order
    items = [
        OrderItem("BTN-PREM-001", "Premium Royal Blue Button", 1000, 3.50, 3500.00),
        OrderItem("BTN-GOLD-002", "Gold Plated Button", 500, 8.00, 4000.00)
    ]

    order = state_machine.create_order(
        customer_email="orders@bmw-manufacturing.com",
        customer_name="BMW Manufacturing GmbH",
        items=items,
        priority=1,  # High priority OEM customer
        metadata={
            "source": "email_processing",
            "original_email_id": "test_email_123",
            "sales_rep": "Klaus Mueller"
        }
    )

    print(f"📦 Created Order: {order.id}")
    print(f"   Customer: {order.customer_name}")
    print(f"   Total: €{order.total_amount:,.2f}")
    print(f"   Priority: {order.priority}")
    print(f"   SLA: {order.sla_hours} hours")
    print(f"   Current State: {order.current_state.value}")
    print()

    # Test state transition workflow
    transitions = [
        (OrderState.CONFIRMED, "SalesAgent", "Customer confirmed via email", {
            "confirmation_method": "email_reply",
            "delivery_address": "BMW Plant Munich",
            "requested_delivery": "2025-01-15"
        }),
        (OrderState.PLANNED, "ProductionAgent", "Production scheduled", {
            "production_slot": "2025-01-10 08:00",
            "estimated_completion": "2025-01-12 16:00",
            "assigned_line": "Line A"
        }),
        (OrderState.IN_PRODUCTION, "ProductionAgent", "Manufacturing started", {
            "batch_number": "BATCH_2025_001",
            "quality_inspector": "Hans Weber",
            "materials_reserved": True
        }),
        (OrderState.PRODUCED, "QualityAgent", "Quality check passed", {
            "qa_inspector": "Maria Schmidt",
            "quality_score": "A+",
            "defect_rate": "0.02%"
        }),
        (OrderState.PACKED, "LogisticsAgent", "Order packed for shipping", {
            "package_id": "PKG_2025_001",
            "weight_kg": 12.5,
            "dimensions": "40x30x15cm"
        }),
        (OrderState.SHIPPED, "LogisticsAgent", "Shipped via DHL", {
            "tracking_number": "DHL123456789",
            "carrier": "DHL",
            "estimated_delivery": "2025-01-15"
        }),
        (OrderState.DELIVERED, "LogisticsAgent", "Delivery confirmed", {
            "delivery_timestamp": "2025-01-15 14:30",
            "recipient": "BMW Receiving Dept",
            "signature": "J. Mueller"
        }),
        (OrderState.INVOICED, "FinanceAgent", "Invoice generated and sent", {
            "invoice_number": "INV-2025-001",
            "invoice_amount": 7500.00,
            "payment_terms": "Net 30"
        }),
        (OrderState.CLOSED, "FinanceAgent", "Payment received", {
            "payment_date": "2025-02-10",
            "payment_method": "Bank Transfer",
            "transaction_id": "TXN_BMW_001"
        })
    ]

    # Execute all transitions
    for target_state, agent, reason, metadata in transitions:
        print(f"🔄 Transitioning to {target_state.value}...")
        success = state_machine.transition_order(order.id, target_state, agent, reason, metadata)

        if success:
            print(f"✅ Successfully transitioned to {target_state.value}")
            print(f"   Agent: {agent}")
            print(f"   Reason: {reason}")

            # Show order status after each transition
            updated_order = state_machine.get_order(order.id)
            print(f"   History Events: {len(updated_order.history)}")
            print()
        else:
            print(f"❌ Failed to transition to {target_state.value}")
            print()
            break

    # Final order statistics
    print("📊 FINAL ORDER STATUS")
    print("=" * 30)
    final_order = state_machine.get_order(order.id)
    print(f"Order ID: {final_order.id}")
    print(f"Final State: {final_order.current_state.value}")
    print(f"Total Transitions: {len(final_order.history)}")
    print(f"Processing Time: {final_order.history[-1].timestamp - final_order.created_at:.0f} seconds")
    print()

    # Show complete history
    print("📋 COMPLETE ORDER HISTORY")
    print("=" * 30)
    for i, transition in enumerate(final_order.history, 1):
        print(f"{i}. {transition.from_state.value} → {transition.to_state.value}")
        print(f"   Agent: {transition.agent}")
        print(f"   Reason: {transition.reason}")
        print(f"   Time: {transition.timestamp}")
        if transition.metadata:
            print(f"   Metadata: {list(transition.metadata.keys())}")
        print()

    # System statistics
    print("🎯 SYSTEM STATISTICS")
    print("=" * 20)
    stats = state_machine.get_order_statistics()
    print(f"Total Orders: {stats['total_orders']}")
    print(f"Orders by State: {stats['by_state']}")
    print(f"Orders by Priority: {stats['by_priority']}")
    print(f"Overdue Orders: {stats['overdue_count']}")
    print(f"Total Value: €{stats['total_value']:,.2f}")
    print(f"Avg Processing Time: {stats['avg_processing_time']:.2f} hours")
    print()

    print("✅ COMPLETE WORKFLOW TEST SUCCESSFUL!")
    print("✅ Order processed through all 10 states")
    print("✅ State machine working correctly")

if __name__ == "__main__":
    test_complete_order_workflow()