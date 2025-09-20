#!/usr/bin/env python3
"""
Happy Buttons System Controller
Advanced start/stop script with service management and dashboard
"""

import os
import sys
import time
import signal
import psutil
import asyncio
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import threading
from contextlib import contextmanager

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/happy_buttons.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ProcessManager:
    """Manages system processes and services"""

    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.base_dir = Path(__file__).parent
        self.logs_dir = self.base_dir / 'logs'
        self.logs_dir.mkdir(exist_ok=True)

        # Service configurations
        self.services = {
            'dashboard': {
                'name': 'Happy Buttons Dashboard',
                'command': [sys.executable, 'dashboard/app.py'],
                'port': 8080,
                'health_check': 'http://localhost:8080/health'
            },
            'email_processor': {
                'name': 'Email Processing Service',
                'command': [sys.executable, 'src/service.py'],
                'port': 8081,
                'health_check': 'http://localhost:8081/health'
            },
            'swarm_coordinator': {
                'name': 'Claude Flow Swarm Coordinator',
                'command': ['npx', 'claude-flow@alpha', 'swarm', 'coordinate', '--daemon'],
                'port': 8082,
                'health_check': None
            }
        }

    def start_service(self, service_name: str) -> bool:
        """Start a specific service"""
        if service_name not in self.services:
            logger.error(f"Unknown service: {service_name}")
            return False

        if service_name in self.processes:
            logger.warning(f"Service {service_name} already running")
            return True

        service = self.services[service_name]
        logger.info(f"Starting {service['name']}...")

        try:
            # Set up log files
            stdout_log = self.logs_dir / f"{service_name}_stdout.log"
            stderr_log = self.logs_dir / f"{service_name}_stderr.log"

            # Start process
            process = subprocess.Popen(
                service['command'],
                cwd=self.base_dir,
                stdout=open(stdout_log, 'w'),
                stderr=open(stderr_log, 'w'),
                env=os.environ.copy()
            )

            self.processes[service_name] = process

            # Wait a moment and check if process started successfully
            time.sleep(2)
            if process.poll() is None:
                logger.info(f"✅ {service['name']} started successfully (PID: {process.pid})")
                return True
            else:
                logger.error(f"❌ {service['name']} failed to start")
                return False

        except Exception as e:
            logger.error(f"Failed to start {service_name}: {str(e)}")
            return False

    def stop_service(self, service_name: str) -> bool:
        """Stop a specific service"""
        if service_name not in self.processes:
            logger.warning(f"Service {service_name} not running")
            return True

        process = self.processes[service_name]
        service = self.services[service_name]

        logger.info(f"Stopping {service['name']}...")

        try:
            # Try graceful shutdown first
            process.terminate()

            # Wait up to 10 seconds for graceful shutdown
            try:
                process.wait(timeout=10)
                logger.info(f"✅ {service['name']} stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown failed
                logger.warning(f"Force killing {service['name']}...")
                process.kill()
                process.wait()
                logger.info(f"✅ {service['name']} force stopped")

            del self.processes[service_name]
            return True

        except Exception as e:
            logger.error(f"Failed to stop {service_name}: {str(e)}")
            return False

    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get detailed status of a service"""
        service = self.services.get(service_name, {})
        status = {
            'name': service.get('name', service_name),
            'running': False,
            'pid': None,
            'memory_mb': 0,
            'cpu_percent': 0,
            'uptime_seconds': 0,
            'port': service.get('port'),
            'health': 'unknown'
        }

        if service_name in self.processes:
            process = self.processes[service_name]
            if process.poll() is None:  # Process is running
                try:
                    ps_process = psutil.Process(process.pid)
                    status.update({
                        'running': True,
                        'pid': process.pid,
                        'memory_mb': ps_process.memory_info().rss / 1024 / 1024,
                        'cpu_percent': ps_process.cpu_percent(),
                        'uptime_seconds': time.time() - ps_process.create_time()
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    status['running'] = False

        return status

    def start_all(self) -> bool:
        """Start all services"""
        logger.info("🚀 Starting Happy Buttons System...")

        success = True
        for service_name in self.services:
            if not self.start_service(service_name):
                success = False

        if success:
            logger.info("✅ All services started successfully!")
        else:
            logger.error("❌ Some services failed to start")

        return success

    def stop_all(self) -> bool:
        """Stop all services"""
        logger.info("🛑 Stopping Happy Buttons System...")

        success = True
        for service_name in list(self.processes.keys()):
            if not self.stop_service(service_name):
                success = False

        if success:
            logger.info("✅ All services stopped successfully!")
        else:
            logger.error("❌ Some services failed to stop properly")

        return success

    def restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        logger.info(f"🔄 Restarting {service_name}...")
        self.stop_service(service_name)
        time.sleep(1)
        return self.start_service(service_name)

    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'system': {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'uptime_seconds': time.time() - psutil.boot_time()
            }
        }

        for service_name in self.services:
            status['services'][service_name] = self.get_service_status(service_name)

        return status


class HappyButtonsController:
    """Main controller for Happy Buttons system"""

    def __init__(self):
        self.process_manager = ProcessManager()
        self.running = False

    def initialize_system(self):
        """Initialize system prerequisites"""
        logger.info("🔧 Initializing Happy Buttons System...")

        # Create necessary directories
        dirs = ['logs', 'samples', 'templates/replies', 'config/units']
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

        # Check dependencies
        missing_deps = []
        try:
            import flask
            import psutil
            import requests
        except ImportError as e:
            missing_deps.append(str(e))

        if missing_deps:
            logger.error(f"Missing dependencies: {missing_deps}")
            logger.info("Run: pip install flask psutil requests flask-socketio")
            return False

        # Initialize Claude Flow if not already done
        try:
            result = subprocess.run(
                ['npx', 'claude-flow@alpha', 'swarm', 'status'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                logger.info("Initializing Claude Flow...")
                subprocess.run(['npx', 'claude-flow@alpha', 'init', '--force'], check=True)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            logger.warning("Claude Flow initialization skipped (optional)")

        logger.info("✅ System initialization complete")
        return True

    def start(self):
        """Start the complete system"""
        if not self.initialize_system():
            return False

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.running = True
        return self.process_manager.start_all()

    def stop(self):
        """Stop the complete system"""
        self.running = False
        return self.process_manager.stop_all()

    def status(self):
        """Print system status"""
        status = self.process_manager.get_system_status()

        print("\n📊 Happy Buttons System Status")
        print("=" * 50)
        print(f"Timestamp: {status['timestamp']}")
        print(f"System CPU: {status['system']['cpu_percent']:.1f}%")
        print(f"System Memory: {status['system']['memory_percent']:.1f}%")
        print(f"System Disk: {status['system']['disk_percent']:.1f}%")

        print("\n🔧 Services:")
        for service_name, service_status in status['services'].items():
            status_icon = "🟢" if service_status['running'] else "🔴"
            print(f"  {status_icon} {service_status['name']}")
            if service_status['running']:
                print(f"    PID: {service_status['pid']}")
                print(f"    Memory: {service_status['memory_mb']:.1f} MB")
                print(f"    Uptime: {service_status['uptime_seconds']:.0f}s")
                if service_status['port']:
                    print(f"    Port: {service_status['port']}")

        print("\n🌐 Dashboard: http://localhost:8080")
        print("📧 Email Service: http://localhost:8081")

    def monitor(self):
        """Run continuous monitoring"""
        logger.info("🔍 Starting system monitor...")

        try:
            while self.running:
                status = self.process_manager.get_system_status()

                # Check for failed services and restart if needed
                for service_name, service_status in status['services'].items():
                    if not service_status['running'] and service_name in self.process_manager.processes:
                        logger.warning(f"Service {service_name} failed, restarting...")
                        self.process_manager.restart_service(service_name)

                time.sleep(10)  # Check every 10 seconds

        except KeyboardInterrupt:
            logger.info("Monitor interrupted")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Happy Buttons System Controller')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'monitor'],
                       help='Action to perform')
    parser.add_argument('--service', help='Specific service to control')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    controller = HappyButtonsController()

    try:
        if args.action == 'start':
            if args.service:
                success = controller.process_manager.start_service(args.service)
            else:
                success = controller.start()
            sys.exit(0 if success else 1)

        elif args.action == 'stop':
            if args.service:
                success = controller.process_manager.stop_service(args.service)
            else:
                success = controller.stop()
            sys.exit(0 if success else 1)

        elif args.action == 'restart':
            if args.service:
                success = controller.process_manager.restart_service(args.service)
            else:
                controller.stop()
                time.sleep(2)
                success = controller.start()
            sys.exit(0 if success else 1)

        elif args.action == 'status':
            controller.status()

        elif args.action == 'monitor':
            controller.start()
            controller.monitor()

    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        controller.stop()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Operation failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()