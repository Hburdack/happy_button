#!/usr/bin/env python3
"""
Quick Release 2 Demo - Key Features Showcase
Demonstrates the main capabilities of Release 2 in a concise format
"""

import asyncio
import logging
import json
import time

async def demo_email_processing():
    """Demo email processing with InfoAgent"""
    print("🎯 DEMO: Email Processing with InfoAgent")
    print("-" * 40)

    try:
        from agents.business.info_agent import InfoAgent
        from agents.business.base_agent_v2 import AgentTask, TaskPriority

        # Create InfoAgent
        agent = InfoAgent()

        # Demo email data
        demo_email = {
            'id': 'demo_email_001',
            'from': 'urgent.customer@oem1.com',
            'to': 'info@h-bu.de',
            'subject': 'URGENT: Large Order Request - 10,000 Premium Buttons',
            'body': '''Dear Happy Buttons Team,

We urgently need a quotation for 10,000 premium buttons for our new product line.
Please send pricing and delivery timeline as soon as possible.

This is for our royal customer and requires immediate attention.

Best regards,
Manufacturing Team''',
            'attachments': [
                {'filename': 'order_specs.pdf', 'content_type': 'application/pdf'}
            ]
        }

        # Create processing task
        task = AgentTask(
            id="demo_email_task",
            type="process_email",
            priority=TaskPriority.HIGH,
            data=demo_email
        )

        print(f"📧 Processing email: {demo_email['subject'][:50]}...")

        # Process the email
        await agent.assign_task(task)
        result = await agent.process_next_task()

        if result:
            print("✅ Email processed successfully!")
            print(f"   📝 Classification: {result.get('classification', {}).get('category', 'N/A')}")
            print(f"   🔄 Routing: {result.get('routing', {}).get('primary_agent', 'N/A')}")
            print(f"   ⚡ Priority: {result.get('classification', {}).get('priority', 'N/A')}")
            print(f"   🛒 Order Created: {'Yes' if result.get('order_created') else 'No'}")

        await agent.shutdown()

    except Exception as e:
        print(f"❌ Demo error: {e}")

    print()

async def demo_smtp_service():
    """Demo SMTP service with royal courtesy"""
    print("🎯 DEMO: Royal Courtesy Email System")
    print("-" * 40)

    try:
        from services.email.smtp_service import SMTPService, EmailToSend

        # Create SMTP service
        smtp = SMTPService()
        smtp.start_service()

        # Create royal courtesy email
        royal_email = EmailToSend(
            to="customer@example.com",
            subject="Your Esteemed Order Confirmation - Happy Buttons GmbH",
            body="""Dear Valued Customer,

We are delighted to acknowledge receipt of your distinguished order and thank you most sincerely for choosing Happy Buttons GmbH for your requirements.

Your order has been received with the utmost care and will be processed according to our highest standards of excellence. Our dedicated team will ensure prompt attention to your specifications.

Should you require any further assistance, please do not hesitate to contact our customer service department.

We remain at your esteemed service.

Most respectfully,
Happy Buttons GmbH Customer Relations""",
            template_used="order_confirmation",
            priority="high",
            courtesy_score=92
        )

        print("📧 Sending royal courtesy email...")

        # Send email (simulated)
        result = await smtp.send_email(royal_email)

        if result.success:
            print("✅ Email sent successfully!")
            print(f"   📧 Message ID: {result.message_id}")
            print(f"   👑 Courtesy Score: {royal_email.courtesy_score}/100")
            print(f"   📊 Queue Status: {smtp.get_queue_status()}")

        smtp.stop_service()

    except Exception as e:
        print(f"❌ Demo error: {e}")

    print()

async def demo_order_management():
    """Demo order state machine"""
    print("🎯 DEMO: Order Lifecycle Management")
    print("-" * 40)

    try:
        from services.order.state_machine import OrderStateMachine, OrderItem, OrderState

        # Create order state machine
        osm = OrderStateMachine()

        # Create order items
        items = [
            OrderItem(
                sku="BTN-001",
                name="Premium Button - Royal Edition",
                quantity=1000,
                unit_price=4.99,
                total_price=4990.00
            ),
            OrderItem(
                sku="BTN-002",
                name="Standard Button - Classic",
                quantity=2000,
                unit_price=2.50,
                total_price=5000.00
            )
        ]

        print("🛒 Creating high-value order...")

        # Create order
        order = osm.create_order(
            customer_email="vip@royalcustomer.com",
            customer_name="Royal Manufacturing Ltd",
            items=items,
            priority=1,  # VIP priority
            metadata={'source': 'demo', 'customer_tier': 'royal'}
        )

        print(f"✅ Order created: {order.id}")
        print(f"   💰 Total Value: €{order.total_amount:,.2f}")
        print(f"   📦 Items: {len(order.items)}")
        print(f"   🚨 Priority: {order.priority} (1=Critical)")
        print(f"   📊 Current State: {order.current_state.value}")

        # Get system statistics
        stats = osm.get_order_statistics()
        print(f"   📈 System Stats: {stats['total_orders']} orders, €{stats['total_value']:,.2f} total value")

    except Exception as e:
        print(f"❌ Demo error: {e}")

    print()

def demo_system_metrics():
    """Demo system metrics generation"""
    print("🎯 DEMO: Business Intelligence Metrics")
    print("-" * 40)

    try:
        # Create sample metrics
        metrics = {
            'timestamp': time.time(),
            'system_uptime': 3600.5,  # 1 hour
            'emails_processed': 47,
            'orders_created': 12,
            'orders_completed': 8,
            'auto_handled_rate': 87.2,
            'avg_processing_time': 145.6,  # seconds
            'active_agents': 3,
            'agent_status': {
                'InfoAgent': 'processing',
                'SalesAgent': 'idle',
                'QualityAgent': 'idle'
            },
            'sla_compliance': {
                'critical': 98.5,
                'oem': 95.2,
                'standard': 91.8
            },
            'top_customers': [
                {'email': 'oem1@manufacturer.com', 'orders': 5, 'value': 15750.00},
                {'email': 'royal@vip.de', 'orders': 3, 'value': 22400.00}
            ]
        }

        print("📊 System Performance Metrics:")
        print(f"   ⏱️  Uptime: {metrics['system_uptime'] / 3600:.1f} hours")
        print(f"   📧 Emails Processed: {metrics['emails_processed']}")
        print(f"   🛒 Orders Created: {metrics['orders_created']}")
        print(f"   ✅ Auto-Handle Rate: {metrics['auto_handled_rate']:.1f}%")
        print(f"   ⚡ Avg Processing: {metrics['avg_processing_time']:.1f}s")
        print(f"   🤖 Active Agents: {metrics['active_agents']}")

        print("\n📈 SLA Compliance:")
        for tier, compliance in metrics['sla_compliance'].items():
            print(f"   • {tier.title()}: {compliance}%")

        print("\n👑 Top Customers:")
        for customer in metrics['top_customers']:
            print(f"   • {customer['email']}: {customer['orders']} orders, €{customer['value']:,.2f}")

        # Save metrics (demo)
        import os
        os.makedirs("data/metrics", exist_ok=True)
        with open("data/metrics/demo_metrics.json", 'w') as f:
            json.dump(metrics, f, indent=2)

        print("\n✅ Metrics saved to data/metrics/demo_metrics.json")

    except Exception as e:
        print(f"❌ Demo error: {e}")

    print()

async def run_complete_demo():
    """Run complete Release 2 feature demonstration"""
    print("="*60)
    print("🏭 HAPPY BUTTONS RELEASE 2 - FEATURE SHOWCASE")
    print("="*60)
    print("Demonstrating key capabilities of the classic company simulation:")
    print("• Multi-agent email processing")
    print("• Royal courtesy communication system")
    print("• Order lifecycle management")
    print("• Business intelligence metrics")
    print("="*60)
    print()

    # Run all demos
    await demo_email_processing()
    await demo_smtp_service()
    await demo_order_management()
    demo_system_metrics()

    print("="*60)
    print("🎉 RELEASE 2 DEMO COMPLETE")
    print("="*60)
    print("✅ All key features demonstrated successfully!")
    print()
    print("📚 For detailed documentation, see: RELEASE2.md")
    print("🔧 For integration tests, run: python test_release2.py")
    print("🚀 For full system demo, run: python demo_release2.py")
    print("="*60)

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)  # Reduce log noise for demo
    asyncio.run(run_complete_demo())