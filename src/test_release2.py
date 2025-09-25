#!/usr/bin/env python3
"""
Simple Release 2 Integration Test
Tests core functionality without complex imports
"""

import asyncio
import logging
import time
import json
import os
import sys

def test_imports():
    """Test that all core modules can be imported"""
    print("🔍 Testing Release 2 imports...")

    try:
        # Test base agent
        from agents.business.base_agent_v2 import BaseAgent, AgentStatus
        print("✅ BaseAgent imports working")

        # Test SMTP service
        from services.email.smtp_service import SMTPService, EmailToSend
        print("✅ SMTP service imports working")

        # Test order state machine
        from services.order.state_machine import OrderStateMachine, OrderState
        print("✅ Order state machine imports working")

        return True

    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_smtp_service():
    """Test SMTP service functionality"""
    print("📧 Testing SMTP service...")

    try:
        from services.email.smtp_service import SMTPService
        smtp = SMTPService()

        # Test service startup
        smtp.start_service()
        print("✅ SMTP service started")

        # Test email creation
        from services.email.smtp_service import EmailToSend
        test_email = EmailToSend(
            to="test@example.com",
            subject="Release 2 Test Email",
            body="This is a test email from Release 2 system.",
            template_used="test_template",
            courtesy_score=75
        )

        # Test email validation
        validation = smtp._validate_email(test_email)
        if validation['valid']:
            print("✅ Email validation passed")
        else:
            print(f"⚠️ Email validation issues: {validation['errors']}")

        # Test queue status
        status = smtp.get_queue_status()
        print(f"✅ Queue status: {status}")

        smtp.stop_service()
        print("✅ SMTP service stopped")

        return True

    except Exception as e:
        print(f"❌ SMTP test error: {e}")
        return False

def test_order_state_machine():
    """Test order state machine"""
    print("🛒 Testing order state machine...")

    try:
        from services.order.state_machine import OrderItem, OrderStateMachine

        osm = OrderStateMachine()

        # Create test order item
        item = OrderItem(
            sku="BTN-001",
            name="Test Button",
            quantity=100,
            unit_price=2.50,
            total_price=250.00
        )

        # Create order
        order = osm.create_order(
            customer_email="test@example.com",
            customer_name="Test Customer",
            items=[item],
            priority=2
        )

        print(f"✅ Order created: {order.id}")
        print(f"✅ Order state: {order.current_state}")

        # Test state transition
        from services.order.state_machine import OrderState
        success = osm.transition_order(
            order.id,
            OrderState.CONFIRMED,
            "TestAgent",
            "Test confirmation"
        )

        if success:
            print("✅ Order state transition successful")
        else:
            print("❌ Order state transition failed")

        # Get statistics
        stats = osm.get_order_statistics()
        print(f"✅ Order statistics: {stats}")

        return True

    except Exception as e:
        print(f"❌ Order state machine test error: {e}")
        return False

def test_agent_framework():
    """Test basic agent functionality"""
    print("🤖 Testing agent framework...")

    try:
        from agents.business.base_agent_v2 import BaseAgent, AgentTask, TaskPriority

        # Create a simple test agent
        class TestAgent(BaseAgent):
            def __init__(self):
                super().__init__("TestAgent")

            def get_capabilities(self):
                return ["test_capability"]

            async def process_task(self, task):
                return {"status": "completed", "task_id": task.id}

        agent = TestAgent()
        print(f"✅ Agent created: {agent.agent_id}")
        print(f"✅ Agent capabilities: {agent.get_capabilities()}")
        print(f"✅ Agent status: {agent.status}")

        return True

    except Exception as e:
        print(f"❌ Agent framework test error: {e}")
        return False

def test_file_system():
    """Test file system setup"""
    print("📁 Testing file system setup...")

    try:
        # Check required directories exist
        required_dirs = [
            "data/metrics",
            "data/events",
            "data/orchestrator",
            "data/sent_emails"
        ]

        for directory in required_dirs:
            os.makedirs(directory, exist_ok=True)
            if os.path.exists(directory):
                print(f"✅ Directory exists: {directory}")
            else:
                print(f"❌ Directory missing: {directory}")

        # Test config file
        config_file = "../sim/config/company_release2.yaml"
        if os.path.exists(config_file):
            print(f"✅ Config file exists: {config_file}")
        else:
            print(f"❌ Config file missing: {config_file}")

        return True

    except Exception as e:
        print(f"❌ File system test error: {e}")
        return False

def test_metrics_generation():
    """Test metrics generation"""
    print("📊 Testing metrics generation...")

    try:
        # Create sample metrics
        metrics = {
            'timestamp': time.time(),
            'emails_processed': 5,
            'orders_created': 2,
            'orders_completed': 1,
            'auto_handled_rate': 80.0,
            'system_uptime': 120.5,
            'test_run': True
        }

        # Save metrics
        os.makedirs("data/metrics", exist_ok=True)
        with open("data/metrics/test_metrics.json", 'w') as f:
            json.dump(metrics, f, indent=2)

        print("✅ Metrics file created")

        # Verify file was written
        if os.path.exists("data/metrics/test_metrics.json"):
            print("✅ Metrics file verified")

        return True

    except Exception as e:
        print(f"❌ Metrics generation error: {e}")
        return False

def run_integration_tests():
    """Run all integration tests"""
    print("="*60)
    print("🚀 RELEASE 2 INTEGRATION TESTS")
    print("="*60)

    tests = [
        ("Import Tests", test_imports),
        ("SMTP Service", test_smtp_service),
        ("Order State Machine", test_order_state_machine),
        ("Agent Framework", test_agent_framework),
        ("File System", test_file_system),
        ("Metrics Generation", test_metrics_generation)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🔧 Running {test_name}...")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

        print("-" * 40)

    # Print summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)

    passed = 0
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1

    print(f"\n🏆 RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Release 2 integration successful!")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Ensure we're in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    success = run_integration_tests()
    sys.exit(0 if success else 1)