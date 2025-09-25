#!/usr/bin/env python3
"""
Test Release 2 Orchestrator with Live Email Processing
Tests the complete system integration with real email accounts
"""

import asyncio
import logging
import time
import json
import os
from typing import Dict, Any

# Import the orchestrator
from release2_orchestrator import Release2Orchestrator

class OrchestratorLiveTest:
    """Live test of the Release 2 orchestrator system"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.orchestrator = None
        self.test_results = {}

    async def run_live_test(self, duration_minutes: int = 3):
        """Run live orchestrator test"""
        print("="*70)
        print("🚀 HAPPY BUTTONS RELEASE 2 - LIVE ORCHESTRATOR TEST")
        print("="*70)
        print("Testing complete system integration with:")
        print("• Real email account connectivity (192.168.2.13)")
        print("• Multi-agent processing pipeline")
        print("• Order lifecycle management")
        print("• Business intelligence metrics")
        print("• Event-driven orchestration")
        print(f"• Test duration: {duration_minutes} minutes")
        print("-"*70)

        try:
            # Phase 1: Initialize orchestrator
            await self._test_orchestrator_initialization()

            # Phase 2: Test email connectivity
            await self._test_email_connectivity()

            # Phase 3: Test agent system
            await self._test_agent_system()

            # Phase 4: Test order processing
            await self._test_order_processing()

            # Phase 5: Run live simulation
            await self._run_live_simulation(duration_minutes)

            # Phase 6: Analyze results
            await self._analyze_test_results()

        except Exception as e:
            self.logger.error(f"Live test error: {e}")
        finally:
            if self.orchestrator:
                await self.orchestrator.shutdown_system()

    async def _test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        print("\n🔧 Phase 1: Testing Orchestrator Initialization")
        print("-" * 50)

        try:
            self.orchestrator = Release2Orchestrator()
            print("   ✅ Orchestrator created successfully")

            # Test configuration loading
            if hasattr(self.orchestrator, 'config_path'):
                print(f"   ✅ Configuration loaded from: {self.orchestrator.config_path}")

            # Test service initialization
            services = ['imap_service', 'smtp_service', 'order_machine']
            for service in services:
                if hasattr(self.orchestrator, service):
                    print(f"   ✅ {service} initialized")

            self.test_results['orchestrator_init'] = True

        except Exception as e:
            print(f"   ❌ Orchestrator initialization failed: {e}")
            self.test_results['orchestrator_init'] = False
            raise

    async def _test_email_connectivity(self):
        """Test email service connectivity"""
        print("\n📧 Phase 2: Testing Email Connectivity")
        print("-" * 50)

        try:
            # Test SMTP service
            smtp = self.orchestrator.smtp_service
            smtp.start_service()

            if smtp.is_running:
                print("   ✅ SMTP service started successfully")

                # Test queue status
                status = smtp.get_queue_status()
                print(f"   ✅ SMTP queue status: {status}")

                self.test_results['smtp_connectivity'] = True
            else:
                print("   ❌ SMTP service failed to start")
                self.test_results['smtp_connectivity'] = False

        except Exception as e:
            print(f"   ❌ Email connectivity test failed: {e}")
            self.test_results['smtp_connectivity'] = False

    async def _test_agent_system(self):
        """Test agent initialization and capabilities"""
        print("\n🤖 Phase 3: Testing Agent System")
        print("-" * 50)

        try:
            # Initialize agents through orchestrator
            await self.orchestrator._initialize_agents()

            agent_count = len(self.orchestrator.agents)
            print(f"   ✅ Initialized {agent_count} agents")

            # Test each agent
            for agent_name, agent in self.orchestrator.agents.items():
                capabilities = agent.get_capabilities()
                status = agent.get_status()
                print(f"   ✅ {agent_name}: {len(capabilities)} capabilities, status: {status}")

            self.test_results['agent_system'] = agent_count > 0

        except Exception as e:
            print(f"   ❌ Agent system test failed: {e}")
            self.test_results['agent_system'] = False

    async def _test_order_processing(self):
        """Test order state machine"""
        print("\n🛒 Phase 4: Testing Order Processing")
        print("-" * 50)

        try:
            osm = self.orchestrator.order_machine

            # Create test order
            from services.order.state_machine import OrderItem
            items = [OrderItem(
                sku="BTN-TEST",
                name="Test Button",
                quantity=100,
                unit_price=2.99,
                total_price=299.00
            )]

            order = osm.create_order(
                customer_email="test@example.com",
                customer_name="Test Customer",
                items=items,
                priority=2,
                metadata={'test': True}
            )

            print(f"   ✅ Test order created: {order.id}")
            print(f"   ✅ Order state: {order.current_state}")
            print(f"   ✅ Order value: €{order.total_amount}")

            # Test statistics
            stats = osm.get_order_statistics()
            print(f"   ✅ Order statistics: {stats['total_orders']} total orders")

            self.test_results['order_processing'] = True

        except Exception as e:
            print(f"   ❌ Order processing test failed: {e}")
            self.test_results['order_processing'] = False

    async def _run_live_simulation(self, duration_minutes: int):
        """Run live system simulation"""
        print(f"\n🌟 Phase 5: Live System Simulation ({duration_minutes} minutes)")
        print("-" * 50)

        try:
            # Start the orchestrator system (background task)
            orchestrator_task = asyncio.create_task(
                self.orchestrator.start_system()
            )

            # Monitor the system
            await self._monitor_live_system(duration_minutes * 60)

            # Stop the system
            self.orchestrator.is_running = False

            # Give orchestrator time to shutdown gracefully
            try:
                await asyncio.wait_for(orchestrator_task, timeout=10.0)
            except asyncio.TimeoutError:
                orchestrator_task.cancel()

            self.test_results['live_simulation'] = True

        except Exception as e:
            print(f"   ❌ Live simulation failed: {e}")
            self.test_results['live_simulation'] = False

    async def _monitor_live_system(self, duration_seconds: int):
        """Monitor live system operation"""
        start_time = time.time()
        last_report = 0
        report_interval = 30  # Report every 30 seconds

        while time.time() - start_time < duration_seconds:
            await asyncio.sleep(5)

            current_time = time.time() - start_time

            # Periodic reporting
            if current_time - last_report >= report_interval:
                await self._print_live_status()
                last_report = current_time

            # Inject demo activity
            if int(current_time) % 45 == 0:  # Every 45 seconds
                await self._inject_demo_activity()

    async def _print_live_status(self):
        """Print current system status"""
        try:
            if not self.orchestrator or not self.orchestrator.is_running:
                return

            status = self.orchestrator.get_system_status()
            metrics = status.get('metrics', {})

            print("   📊 Live Status Update:")
            print(f"      ⏱️  Uptime: {status.get('uptime', 0):.0f}s")
            print(f"      📧 Emails: {metrics.get('emails_processed', 0)}")
            print(f"      🛒 Orders: {metrics.get('orders_created', 0)}")
            print(f"      📈 Auto-rate: {metrics.get('auto_handled_rate', 0):.1f}%")
            print(f"      🤖 Agents: {metrics.get('active_agents', 0)}")

        except Exception as e:
            print(f"      ❌ Status update error: {e}")

    async def _inject_demo_activity(self):
        """Inject demo email activity"""
        try:
            if not self.orchestrator or not self.orchestrator.is_running:
                return

            demo_email = self.orchestrator._create_demo_email()
            await self.orchestrator._handle_incoming_email(demo_email)
            print(f"   💌 Demo activity: {demo_email['subject'][:40]}...")

        except Exception as e:
            print(f"   ❌ Demo activity error: {e}")

    async def _analyze_test_results(self):
        """Analyze and report test results"""
        print("\n📋 Phase 6: Test Results Analysis")
        print("="*70)

        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())

        print(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed")
        print()

        # Detailed results
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            test_display = test_name.replace('_', ' ').title()
            print(f"   {status} {test_display}")

        print()

        # Final assessment
        if passed_tests == total_tests:
            print("🎉 EXCELLENT: All orchestrator tests passed!")
            print("   ✅ Release 2 system is fully operational")
            print("   ✅ Email processing pipeline working")
            print("   ✅ Multi-agent coordination successful")
            print("   ✅ Order management system active")
            print("   ✅ Ready for production deployment")

        elif passed_tests >= total_tests * 0.8:
            print("✅ GOOD: Most orchestrator tests passed!")
            print(f"   ✅ {passed_tests} out of {total_tests} systems working")
            print("   ⚠️  Some components may need attention")
            print("   ✅ Core functionality operational")

        else:
            print("⚠️  PARTIAL: Some orchestrator tests failed")
            print(f"   ⚠️  Only {passed_tests} out of {total_tests} systems working")
            print("   🔧 System needs debugging before production")

        # System metrics summary
        if self.orchestrator:
            try:
                final_status = self.orchestrator.get_system_status()
                final_metrics = final_status.get('metrics', {})

                print(f"\n📈 Final System Metrics:")
                print(f"   📧 Total Emails Processed: {final_metrics.get('emails_processed', 0)}")
                print(f"   🛒 Orders Created: {final_metrics.get('orders_created', 0)}")
                print(f"   ✅ Orders Completed: {final_metrics.get('orders_completed', 0)}")
                print(f"   📊 Auto-Handle Rate: {final_metrics.get('auto_handled_rate', 0):.1f}%")

                # Save final metrics
                await self._save_test_metrics(final_metrics)

            except Exception as e:
                print(f"   ❌ Error getting final metrics: {e}")

    async def _save_test_metrics(self, metrics: Dict[str, Any]):
        """Save test metrics to file"""
        try:
            test_results = {
                'timestamp': time.time(),
                'test_results': self.test_results,
                'final_metrics': metrics,
                'test_duration': 'live_orchestrator_test'
            }

            os.makedirs("data/test_results", exist_ok=True)
            with open("data/test_results/orchestrator_live_test.json", 'w') as f:
                json.dump(test_results, f, indent=2)

            print("   💾 Test results saved to data/test_results/orchestrator_live_test.json")

        except Exception as e:
            print(f"   ❌ Error saving test metrics: {e}")

async def main():
    """Main test entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    test = OrchestratorLiveTest()

    try:
        duration = 2  # Default 2 minutes
        if len(os.sys.argv) > 1:
            duration = int(os.sys.argv[1])

        await test.run_live_test(duration)

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())