#!/usr/bin/env python3
"""
Test Agent Email Coordination
Tests if agents can send and receive emails via real IMAP/SMTP
"""

import sys
import os
from pathlib import Path
import asyncio
import logging
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agents.agent_email_dispatcher import AgentEmailDispatcher, TaskTypes
from src.agents.production_agent import ProductionAgent
from src.agents.logistics_agent import LogisticsAgent
from src.agents.finance_agent import FinanceAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agent_email_coordination():
    """Test end-to-end agent email coordination"""

    print("🧪 TESTING AGENT EMAIL COORDINATION")
    print("=" * 60)

    try:
        # Initialize email dispatcher
        print("📧 Initializing email dispatcher...")
        dispatcher = AgentEmailDispatcher()

        # Initialize agents
        print("🤖 Initializing agents...")
        production_agent = ProductionAgent()
        logistics_agent = LogisticsAgent()
        finance_agent = FinanceAgent()

        print("✅ Agents initialized successfully")

        # Test 1: Create a coordination task
        print("\n🧪 TEST 1: Creating coordination task...")

        task = dispatcher.create_coordination_task(
            from_agent="production_agent",
            to_agent="logistics_agent",
            task_type=TaskTypes.INVENTORY_CHECK,
            content="URGENT: Need inventory check for BTN-001. Production halt imminent if stock below 1000 units. Customer order for 5000 units pending.",
            priority="critical",
            data={
                "product": "BTN-001",
                "required_quantity": 5000,
                "current_production": "halted",
                "customer_order": "ORD-2025-001"
            },
            due_hours=2
        )

        print(f"✅ Task created: {task.task_id}")
        print(f"   From: {task.from_agent} → To: {task.to_agent}")
        print(f"   Type: {task.task_type}")
        print(f"   Priority: {task.priority}")

        # Test 2: Send the task email
        print("\n🧪 TEST 2: Sending task email via SMTP...")

        success = dispatcher.send_task_email(task)

        if success:
            print("✅ Task email sent successfully!")
            print(f"   Email should appear in info@h-bu.de mailbox")
            print(f"   Subject: [AGENT-TASK] [PRODUCTION_AGENT→LOGISTICS_AGENT] Coordination: Inventory Check")
        else:
            print("❌ Failed to send task email")
            return False

        # Test 3: Wait and check for task in mailbox
        print("\n🧪 TEST 3: Checking for task in logistics agent mailbox...")
        print("   Waiting 5 seconds for email delivery...")

        await asyncio.sleep(5)

        # Check for incoming tasks
        incoming_tasks = dispatcher.check_for_agent_tasks("logistics_agent", limit=5)

        print(f"📥 Found {len(incoming_tasks)} tasks for logistics_agent")

        for i, received_task in enumerate(incoming_tasks):
            print(f"   Task {i+1}:")
            print(f"      ID: {received_task.task_id}")
            print(f"      From: {received_task.from_agent}")
            print(f"      Type: {received_task.task_type}")
            print(f"      Priority: {received_task.priority}")
            print(f"      Subject: {received_task.subject}")

        # Test 4: Test multiple agent coordination
        print("\n🧪 TEST 4: Testing multi-agent coordination chain...")

        # Production → Logistics → Finance coordination chain
        tasks_to_send = [
            {
                "from": "production_agent",
                "to": "logistics_agent",
                "type": TaskTypes.INVENTORY_CHECK,
                "content": "Check inventory for emergency production run",
                "data": {"product": "BTN-002", "quantity": 3000}
            },
            {
                "from": "logistics_agent",
                "to": "finance_agent",
                "type": TaskTypes.PRICING_REQUEST,
                "content": "Need expedited shipping cost approval for urgent order",
                "data": {"shipping_cost": 2500, "urgency": "critical"}
            },
            {
                "from": "finance_agent",
                "to": "production_agent",
                "type": TaskTypes.APPROVAL_REQUEST,
                "content": "Budget approval for overtime production",
                "data": {"overtime_cost": 5000, "approval_status": "approved"}
            }
        ]

        for i, task_config in enumerate(tasks_to_send):
            print(f"\n   Sending coordination task {i+1}/3...")

            coord_task = dispatcher.create_coordination_task(
                from_agent=task_config["from"],
                to_agent=task_config["to"],
                task_type=task_config["type"],
                content=task_config["content"],
                priority="high",
                data=task_config["data"],
                due_hours=4
            )

            success = dispatcher.send_task_email(coord_task)
            if success:
                print(f"      ✅ Task {coord_task.task_id} sent successfully")
            else:
                print(f"      ❌ Failed to send task {coord_task.task_id}")

        # Test 5: Check agent task statistics
        print("\n🧪 TEST 5: Agent task statistics...")

        for agent_type in ["production_agent", "logistics_agent", "finance_agent"]:
            stats = dispatcher.get_agent_task_stats(agent_type)
            print(f"\n   {agent_type.upper()}:")
            print(f"      Total tasks: {stats['total_tasks']}")
            print(f"      Pending: {stats['pending_tasks']}")
            print(f"      High priority: {stats['high_priority_tasks']}")
            print(f"      Task types: {stats['task_types']}")

            if 'error' in stats:
                print(f"      ⚠️ Error: {stats['error']}")

        print("\n✅ AGENT EMAIL COORDINATION TEST COMPLETED")
        print("=" * 60)
        print("📧 Check your email client at info@h-bu.de to see the coordination emails")
        print("🤖 Agents should now be able to communicate via real email system")

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.exception("Test failed")
        return False

async def test_simple_email_send():
    """Test simple email sending"""
    print("\n🧪 SIMPLE EMAIL SEND TEST")
    print("-" * 40)

    try:
        dispatcher = AgentEmailDispatcher()

        # Create simple test task
        test_task = dispatcher.create_coordination_task(
            from_agent="info_agent",
            to_agent="finance_agent",
            task_type="test_communication",
            content="This is a test email from the Happy Buttons agent system. If you receive this, the email coordination is working correctly!",
            priority="medium",
            data={"test": True, "timestamp": datetime.now().isoformat()}
        )

        print(f"📨 Sending test email...")
        print(f"   Task ID: {test_task.task_id}")
        print(f"   From: {test_task.from_agent}")
        print(f"   To: {test_task.to_agent}")

        success = dispatcher.send_task_email(test_task)

        if success:
            print("✅ Test email sent successfully!")
            print("📧 Check info@h-bu.de mailbox for the email")
        else:
            print("❌ Failed to send test email")

        return success

    except Exception as e:
        print(f"❌ Simple email test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 STARTING AGENT EMAIL SYSTEM TESTS")
    print("=" * 60)

    # Test 1: Simple email send
    simple_success = await test_simple_email_send()

    if simple_success:
        print("\n" + "=" * 60)
        # Test 2: Full coordination test
        coord_success = await test_agent_email_coordination()

        if coord_success:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Agent email coordination system is working")
        else:
            print("\n⚠️ Coordination test failed")
    else:
        print("\n❌ Basic email sending failed - check SMTP configuration")

    print("\n📋 NEXT STEPS:")
    print("1. Check your email client at info@h-bu.de")
    print("2. Look for emails with subject containing [AGENT-TASK]")
    print("3. Verify agents can receive and process task emails")
    print("4. Monitor logs/email-processor.log for processing activity")

if __name__ == "__main__":
    asyncio.run(main())