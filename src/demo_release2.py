#!/usr/bin/env python3
"""
Release 2 Demo Script
Demonstrates the complete Happy Buttons Release 2 system with agents and orchestration
"""

import asyncio
import logging
import time
import json
import os
import sys
from typing import Dict, Any

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from release2_orchestrator import Release2Orchestrator

class Release2Demo:
    """Demo runner for Release 2 system"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.orchestrator = None

    async def run_demo(self, duration_minutes: int = 5):
        """Run the Release 2 demo for specified duration"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("🏭 HAPPY BUTTONS RELEASE 2 - CLASSIC COMPANY SIMULATION")
            self.logger.info("=" * 60)
            self.logger.info(f"Demo will run for {duration_minutes} minutes")
            self.logger.info("Features demonstrated:")
            self.logger.info("• Multi-agent email processing")
            self.logger.info("• Order lifecycle management")
            self.logger.info("• Royal courtesy communications")
            self.logger.info("• Real-time system monitoring")
            self.logger.info("• Event-driven orchestration")
            self.logger.info("-" * 60)

            # Initialize orchestrator
            self.orchestrator = Release2Orchestrator()

            # Start system in background
            orchestrator_task = asyncio.create_task(self.orchestrator.start_system())

            # Run demo monitoring
            await self._run_demo_monitoring(duration_minutes * 60)

            # Shutdown gracefully
            await self.orchestrator.shutdown_system()
            orchestrator_task.cancel()

        except Exception as e:
            self.logger.error(f"Demo error: {e}")
            if self.orchestrator:
                await self.orchestrator.shutdown_system()

    async def _run_demo_monitoring(self, duration_seconds: int):
        """Monitor and report demo progress"""
        start_time = time.time()
        last_report = 0

        while time.time() - start_time < duration_seconds:
            try:
                # Wait for system to be running
                await asyncio.sleep(2)

                if self.orchestrator and self.orchestrator.is_running:
                    current_time = time.time() - start_time

                    # Report every 30 seconds
                    if current_time - last_report >= 30:
                        await self._print_system_status()
                        last_report = current_time

                    # Inject demo emails periodically
                    if int(current_time) % 45 == 0:  # Every 45 seconds
                        await self._inject_demo_email()

            except Exception as e:
                self.logger.error(f"Error in demo monitoring: {e}")
                await asyncio.sleep(5)

    async def _print_system_status(self):
        """Print current system status"""
        try:
            if not self.orchestrator:
                return

            status = self.orchestrator.get_system_status()

            self.logger.info("📊 SYSTEM STATUS UPDATE:")
            self.logger.info(f"   ⏱️ Uptime: {status['uptime']:.0f} seconds")
            self.logger.info(f"   📧 Emails Processed: {status['metrics']['emails_processed']}")
            self.logger.info(f"   🛒 Orders Created: {status['metrics']['orders_created']}")
            self.logger.info(f"   ✅ Orders Completed: {status['metrics']['orders_completed']}")
            self.logger.info(f"   🤖 Active Agents: {status['metrics']['active_agents']}")
            self.logger.info(f"   📈 Auto-Handle Rate: {status['metrics']['auto_handled_rate']:.1f}%")

            # Agent status
            self.logger.info("   👥 Agent Status:")
            for agent_name, agent_status in status['agents'].items():
                self.logger.info(f"      • {agent_name}: {agent_status}")

            self.logger.info("-" * 40)

        except Exception as e:
            self.logger.error(f"Error printing status: {e}")

    async def _inject_demo_email(self):
        """Inject a demo email for processing"""
        try:
            if not self.orchestrator or not self.orchestrator.is_running:
                return

            demo_email = self.orchestrator._create_demo_email()
            await self.orchestrator._handle_incoming_email(demo_email)

            self.logger.info(f"💌 Injected demo email: {demo_email['subject'][:50]}...")

        except Exception as e:
            self.logger.error(f"Error injecting demo email: {e}")

    async def _generate_sample_data(self):
        """Generate sample data for demo"""
        # This could create sample orders, emails, etc.
        pass

def print_demo_summary():
    """Print demo completion summary"""
    print("\n" + "=" * 60)
    print("🎯 RELEASE 2 DEMO COMPLETED")
    print("=" * 60)
    print("📁 Generated data files:")

    data_dirs = ["data/metrics", "data/events", "data/orchestrator", "data/dashboard"]
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            file_count = len([f for f in os.listdir(data_dir) if f.endswith('.json')])
            print(f"   • {data_dir}: {file_count} files")

    print("\n📊 To view dashboard:")
    print("   cd dashboard && python app.py")
    print("   Visit: http://localhost:80")

    print("\n📈 To check metrics:")
    if os.path.exists("data/metrics/current_metrics.json"):
        try:
            with open("data/metrics/current_metrics.json", 'r') as f:
                metrics = json.load(f)
            print(f"   • Final emails processed: {metrics.get('emails_processed', 0)}")
            print(f"   • Final orders created: {metrics.get('orders_created', 0)}")
            print(f"   • Auto-handle rate: {metrics.get('auto_handled_rate', 0):.1f}%")
        except:
            print("   • Metrics file available for review")

    print("\n🔍 For detailed logs, check the console output above")
    print("=" * 60)

async def main():
    """Main demo entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/release2_demo.log')
        ]
    )

    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)

    demo = Release2Demo()

    try:
        # Run demo for 3 minutes by default
        demo_duration = 3
        if len(sys.argv) > 1:
            demo_duration = int(sys.argv[1])

        await demo.run_demo(demo_duration)

    except KeyboardInterrupt:
        logging.info("Demo interrupted by user")
    except Exception as e:
        logging.error(f"Demo failed: {e}")
    finally:
        print_demo_summary()

if __name__ == "__main__":
    asyncio.run(main())