#!/usr/bin/env python3
"""
Company-Wide Simulation Manager
Orchestrates all business simulations for continuous email generation

This manages:
1. Enhanced Business Week Simulation (complex scenarios)
2. TimeWarp Email Generation (accelerated timing)
3. Real Email Sending (actual emails to mailbox)
4. Continuous operation with restart capabilities
"""

import sys
import time
import logging
import threading
from datetime import datetime
import signal
import os

# Add src to path
sys.path.insert(0, 'src')

# Import all simulation components
from enhanced_business_simulation import get_enhanced_simulation
from real_email_sender import get_real_email_sender

# Initialize logger
logger = logging.getLogger(__name__)

class CompanySimulationManager:
    """Manages all company simulations for continuous email generation"""

    def __init__(self):
        self.running = False
        self.enhanced_simulation = get_enhanced_simulation()
        self.real_email_sender = get_real_email_sender()

        # Management thread
        self.management_thread = None

        # Statistics
        self.total_emails_sent = 0
        self.simulation_cycles = 0
        self.start_time = None

        # Configuration
        self.business_week_duration = 300  # 5 minutes = full business week
        self.inter_cycle_pause = 30  # 30 seconds between cycles
        self.emails_per_hour_target = 12  # Continuous email flow

        logger.info("Company Simulation Manager initialized")

    def start_continuous_simulation(self):
        """Start continuous company-wide business simulation"""
        if self.running:
            logger.warning("Simulation already running")
            return

        logger.info("🚀 STARTING CONTINUOUS COMPANY SIMULATION")
        logger.info("=" * 60)
        logger.info("📧 Target: Continuous email generation to info@h-bu.de")
        logger.info("🏢 Scenario: Complete business week cycles with issues")
        logger.info("⚡ Features: Real emails, complex scenarios, optimization opportunities")
        logger.info("=" * 60)

        self.running = True
        self.start_time = datetime.now()

        # Start real email sender
        if not self.real_email_sender.is_running:
            self.real_email_sender.start_service()
            logger.info("📧 Real Email Sender: STARTED")

        # Start management thread
        self.management_thread = threading.Thread(target=self._continuous_simulation_loop, daemon=True)
        self.management_thread.start()

        logger.info("✅ Continuous Company Simulation: ACTIVE")

    def _continuous_simulation_loop(self):
        """Main continuous simulation loop"""
        while self.running:
            try:
                logger.info(f"\n🔄 STARTING SIMULATION CYCLE #{self.simulation_cycles + 1}")
                logger.info(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                # Start enhanced business simulation
                if not self.enhanced_simulation.running:
                    # Reset simulation for new cycle
                    self.enhanced_simulation.day_number = 1
                    self.enhanced_simulation.hour = 9
                    self.enhanced_simulation.current_issues = []

                    # Start with moderate speed for continuous flow
                    self.enhanced_simulation.start_simulation(speed_multiplier=3)
                    logger.info("🏢 Enhanced Business Week Simulation: STARTED (3x speed)")

                # Monitor the simulation cycle
                cycle_start = time.time()
                while (time.time() - cycle_start < self.business_week_duration and
                       self.running and
                       self.enhanced_simulation.running):

                    # Status update every 30 seconds
                    if int(time.time() - cycle_start) % 30 == 0:
                        self._log_simulation_status()

                    time.sleep(1)

                # Stop current simulation cycle
                if self.enhanced_simulation.running:
                    self.enhanced_simulation.stop_simulation()

                self.simulation_cycles += 1

                # Final cycle status
                self._log_cycle_completion()

                # Pause between cycles if still running
                if self.running:
                    logger.info(f"⏸️  Pause between cycles: {self.inter_cycle_pause} seconds")
                    time.sleep(self.inter_cycle_pause)

            except Exception as e:
                logger.error(f"Error in simulation cycle: {e}")
                time.sleep(10)  # Wait before retry

    def _log_simulation_status(self):
        """Log current simulation status"""
        try:
            # Enhanced simulation status
            sim_status = self.enhanced_simulation.get_simulation_status()

            # Email sender status
            email_status = self.real_email_sender.get_status()

            # Update total
            self.total_emails_sent = email_status['emails_sent']

            # Runtime
            runtime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            runtime_str = f"{int(runtime//3600)}h {int((runtime%3600)//60)}m {int(runtime%60)}s"

            logger.info(f"\n📊 SIMULATION STATUS (Runtime: {runtime_str})")
            logger.info(f"   🏢 Business Day: {sim_status['day_name']} (Day {sim_status['day_number']})")
            logger.info(f"   🕐 Business Hour: {sim_status['hour']:02d}:00")
            logger.info(f"   🎭 Current Theme: {sim_status['theme']}")
            logger.info(f"   📧 Display Emails Today: {sim_status['total_emails_today']}")
            logger.info(f"   📨 Real Emails Sent: {self.total_emails_sent}")
            logger.info(f"   ⚠️  Active Issues: {sim_status['current_issues']}")
            logger.info(f"   🎯 Optimization Opportunities: {sim_status['optimization_opportunities']}")
            logger.info(f"   🔁 Completed Cycles: {self.simulation_cycles}")

            # Show recent issues for context
            if sim_status.get('issues'):
                logger.info("   📋 Recent Issues:")
                for issue in sim_status['issues'][-2:]:  # Last 2 issues
                    logger.info(f"      - {issue.get('title', 'Unknown Issue')}")

        except Exception as e:
            logger.error(f"Error logging status: {e}")

    def _log_cycle_completion(self):
        """Log completion of a simulation cycle"""
        email_status = self.real_email_sender.get_status()
        self.total_emails_sent = email_status['emails_sent']

        logger.info(f"\n✅ SIMULATION CYCLE #{self.simulation_cycles + 1} COMPLETED")
        logger.info(f"   📧 Total Real Emails Sent: {self.total_emails_sent}")
        logger.info(f"   📊 Email Success Rate: {((self.total_emails_sent / max(1, self.total_emails_sent + email_status['errors_count'])) * 100):.1f}%")
        logger.info(f"   ⏱️  Cycle Duration: {self.business_week_duration} seconds")

    def stop_simulation(self):
        """Stop all simulations"""
        logger.info("\n🛑 STOPPING CONTINUOUS COMPANY SIMULATION")
        self.running = False

        # Stop enhanced simulation
        if self.enhanced_simulation.running:
            self.enhanced_simulation.stop_simulation()
            logger.info("🏢 Enhanced Business Simulation: STOPPED")

        # Stop email sender
        if self.real_email_sender.is_running:
            self.real_email_sender.stop_service()
            logger.info("📧 Real Email Sender: STOPPED")

        # Wait for management thread
        if self.management_thread and self.management_thread.is_alive():
            self.management_thread.join(timeout=5)

        logger.info("✅ All simulations stopped")

    def get_overall_status(self):
        """Get comprehensive status of all simulations"""
        try:
            sim_status = self.enhanced_simulation.get_simulation_status()
            email_status = self.real_email_sender.get_status()

            runtime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0

            return {
                'running': self.running,
                'runtime_seconds': runtime,
                'simulation_cycles_completed': self.simulation_cycles,
                'total_real_emails_sent': email_status['emails_sent'],
                'email_errors': email_status['errors_count'],
                'current_business_day': sim_status.get('day_name', 'N/A'),
                'current_business_hour': sim_status.get('hour', 0),
                'current_theme': sim_status.get('theme', 'N/A'),
                'active_issues': sim_status.get('current_issues', 0),
                'optimization_opportunities': sim_status.get('optimization_opportunities', 0),
                'email_queue_size': email_status['queue_size'],
                'start_time': self.start_time.isoformat() if self.start_time else None
            }
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {'error': str(e)}

# Global manager instance
simulation_manager = CompanySimulationManager()

def get_simulation_manager():
    """Get the global simulation manager"""
    return simulation_manager

# Signal handler for graceful shutdown
def signal_handler(signum, frame):
    logger.info(f"\n📡 Received signal {signum}")
    simulation_manager.stop_simulation()
    sys.exit(0)

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/company_simulation.log')
        ]
    )

    logger = logging.getLogger(__name__)

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("🏢 HAPPY BUTTONS COMPANY SIMULATION")
    print("=" * 60)
    print("🎯 Purpose: Continuous email generation for optimization testing")
    print("📧 Target: info@h-bu.de mailbox")
    print("⚡ Features: Complex business scenarios, real emails, issues")
    print("=" * 60)

    try:
        # Start the continuous simulation
        manager = get_simulation_manager()
        manager.start_continuous_simulation()

        print("\n✅ Simulation started successfully!")
        print("💡 Monitor logs/company_simulation.log for detailed progress")
        print("🔄 The simulation will run continuously until stopped")
        print("⏹️  Press Ctrl+C to stop")
        print("\n📊 REAL-TIME STATUS:")
        print("-" * 40)

        # Keep main thread alive and show status
        last_status_time = 0
        while manager.running:
            current_time = time.time()

            # Show status every 60 seconds
            if current_time - last_status_time >= 60:
                status = manager.get_overall_status()

                if 'error' not in status:
                    runtime_hours = int(status['runtime_seconds'] // 3600)
                    runtime_minutes = int((status['runtime_seconds'] % 3600) // 60)

                    print(f"\n📈 Runtime: {runtime_hours}h {runtime_minutes}m")
                    print(f"📧 Emails sent: {status['total_real_emails_sent']}")
                    print(f"🔁 Cycles completed: {status['simulation_cycles_completed']}")
                    print(f"🏢 Current: {status['current_business_day']} {status['current_business_hour']}:00")
                    print(f"⚠️  Issues: {status['active_issues']}")
                    print("-" * 40)

                last_status_time = current_time

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Stopping simulation...")
        manager.stop_simulation()
        print("✅ Simulation stopped gracefully")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        manager.stop_simulation()
        sys.exit(1)