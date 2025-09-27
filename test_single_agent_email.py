#!/usr/bin/env python3
"""
Simple test to send a single agent task email and verify it works
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from agents.agent_email_dispatcher import AgentEmailDispatcher, TaskTypes


async def test_single_email():
    """Test sending a single agent email to support mailbox"""

    print("📧 TESTING SINGLE AGENT EMAIL TO SUPPORT")
    print("=" * 50)

    # Initialize dispatcher
    dispatcher = AgentEmailDispatcher()
    print("✅ Email dispatcher initialized")

    # Create a test task for quality agent (support@h-bu.de)
    task = dispatcher.create_coordination_task(
        from_agent="orders_agent",
        to_agent="quality_agent",
        task_type=TaskTypes.ESCALATION,
        content="URGENT: Product quality issue reported by customer. Order #TEST-001 has defective buttons. Please investigate immediately.",
        priority="critical",
        data={
            'order_id': 'TEST-001',
            'product': 'BTN-001',
            'issue': 'defective_buttons',
            'customer': 'test-customer@example.com',
            'severity': 'critical'
        },
        due_hours=2
    )

    print(f"📋 Created task: {task.task_id}")
    print(f"   From: {task.from_agent}")
    print(f"   To: {task.to_agent}")
    print(f"   Type: {task.task_type}")
    print(f"   Priority: {task.priority}")

    # Send the email
    print(f"\n📤 Sending email to support@h-bu.de...")
    success = dispatcher.send_task_email(task)

    if success:
        print("✅ Email sent successfully!")
        print(f"📧 Subject: [AGENT-TASK] [{task.from_agent.upper()}→{task.to_agent.upper()}] {task.subject}")
        print(f"📬 Destination: support@h-bu.de")

        print(f"\n⏳ Waiting 10 seconds for email delivery...")
        time.sleep(10)

        # Try to check if the email arrived
        print(f"\n📥 Checking for task in quality_agent mailbox...")
        tasks = dispatcher.check_for_agent_tasks('quality_agent', limit=5)

        if tasks:
            print(f"✅ Found {len(tasks)} task(s) in quality_agent mailbox:")
            for found_task in tasks:
                print(f"   📋 {found_task.task_id}: {found_task.task_type} ({found_task.priority})")
                if found_task.task_id == task.task_id:
                    print(f"   🎯 FOUND OUR TEST TASK!")
        else:
            print("❌ No tasks found in quality_agent mailbox")
            print("   This might be due to:")
            print("   • Email delivery delay")
            print("   • IMAP authentication issues")
            print("   • Email filtering")

    else:
        print("❌ Failed to send email")
        print("   Possible issues:")
        print("   • SMTP rate limiting")
        print("   • Authentication problems")
        print("   • Network connectivity")

    # Check overall stats
    print(f"\n📊 Overall email task statistics:")
    stats = dispatcher.get_agent_task_stats('quality_agent')
    print(f"   Total tasks: {stats['total_tasks']}")
    print(f"   Pending tasks: {stats['pending_tasks']}")
    print(f"   High priority: {stats['high_priority_tasks']}")

    print(f"\n" + "=" * 50)
    print("🏁 Single email test completed")


if __name__ == "__main__":
    try:
        asyncio.run(test_single_email())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()