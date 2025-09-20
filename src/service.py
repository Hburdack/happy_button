#!/usr/bin/env python3
"""
Happy Buttons Email Service
Service mode for the email processing system with health checks
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from flask import Flask, jsonify
from threading import Thread
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import email processing modules (with fallback to mock)
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", "/home/pi/happy_button/src/main.py")
    main_module = importlib.util.module_from_spec(spec)
    sys.modules["main_module"] = main_module
    spec.loader.exec_module(main_module)
    HappyButtonsEmailSystem = main_module.HappyButtonsEmailSystem
except Exception as e:
    logger.warning(f"Could not import main system, using mock: {e}")

    class MockHappyButtonsEmailSystem:
        async def initialize(self):
            pass

        async def shutdown(self):
            pass

        async def process_email(self, sender):
            return {
                'status': 'success',
                'routing': {'destination': 'support@h-bu.de'},
                'agent': 'mock',
                'response': 'Mock auto-reply generated'
            }

        def get_system_status(self):
            return {
                'system_metrics': {'cpu': 5.0, 'memory': 45.2},
                'agents': {'mock_agent': {'status': 'active'}},
                'parser_stats': {'parsed': 10},
                'router_stats': {'routed': 10}
            }

    HappyButtonsEmailSystem = MockHappyButtonsEmailSystem

# Flask app for health checks
app = Flask(__name__)

class EmailService:
    """Email processing service with health monitoring"""

    def __init__(self):
        self.email_system = None
        self.running = False
        self.stats = {
            'start_time': None,
            'emails_processed': 0,
            'last_activity': None,
            'status': 'stopped'
        }

    async def start(self):
        """Start the email service"""
        try:
            logger.info("🚀 Starting Happy Buttons Email Service...")

            self.email_system = HappyButtonsEmailSystem()
            await self.email_system.initialize()

            self.running = True
            self.stats['start_time'] = datetime.now()
            self.stats['status'] = 'running'

            logger.info("✅ Email service started successfully")

            # Start processing loop
            await self.process_emails()

        except Exception as e:
            logger.error(f"❌ Failed to start email service: {str(e)}")
            self.stats['status'] = 'error'
            raise

    async def stop(self):
        """Stop the email service"""
        logger.info("🛑 Stopping email service...")
        self.running = False
        self.stats['status'] = 'stopped'

        if self.email_system:
            await self.email_system.shutdown()

        logger.info("✅ Email service stopped")

    async def process_emails(self):
        """Main email processing loop"""
        logger.info("📧 Starting email processing loop...")

        # Demo emails for continuous processing
        demo_emails = [
            {
                'sender': 'john@oem1.com',
                'subject': 'Urgent Order Request',
                'body': 'We need 5000 buttons urgently. Budget $10,000.',
                'interval': 30
            },
            {
                'sender': 'customer@email.com',
                'subject': 'Button Order',
                'body': 'I need 100 blue buttons for my project.',
                'interval': 45
            },
            {
                'sender': 'supplier@materials.com',
                'subject': 'Delivery Confirmation',
                'body': 'Your raw materials have been delivered.',
                'interval': 60
            },
            {
                'sender': 'unhappy@customer.com',
                'subject': 'Quality Issue',
                'body': 'The buttons I received are defective.',
                'interval': 120
            }
        ]

        last_processed = {}

        while self.running:
            try:
                current_time = time.time()

                # Process demo emails based on their intervals
                for i, email_data in enumerate(demo_emails):
                    if i not in last_processed or (current_time - last_processed[i]) >= email_data['interval']:

                        # Process the email
                        result = await self.email_system.process_email(email_data['sender'])

                        if result['status'] == 'success':
                            self.stats['emails_processed'] += 1
                            self.stats['last_activity'] = datetime.now()

                            logger.info(f"✅ Processed email from {email_data['sender']} → {result['routing']['destination']}")
                        else:
                            logger.error(f"❌ Failed to process email from {email_data['sender']}: {result.get('error')}")

                        last_processed[i] = current_time

                # Health check update
                self.stats['status'] = 'running'

                # Wait before next cycle
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error in processing loop: {str(e)}")
                self.stats['status'] = 'error'
                await asyncio.sleep(10)

    def get_status(self) -> Dict[str, Any]:
        """Get service status for health checks"""
        uptime = None
        if self.stats['start_time']:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()

        return {
            'status': self.stats['status'],
            'running': self.running,
            'uptime_seconds': uptime,
            'emails_processed': self.stats['emails_processed'],
            'last_activity': self.stats['last_activity'].isoformat() if self.stats['last_activity'] else None,
            'timestamp': datetime.now().isoformat()
        }

# Global service instance
email_service = EmailService()

@app.route('/health')
def health():
    """Health check endpoint"""
    status = email_service.get_status()
    http_status = 200 if status['status'] in ['running', 'starting'] else 503
    return jsonify(status), http_status

@app.route('/stats')
def stats():
    """Detailed statistics endpoint"""
    status = email_service.get_status()

    # Add system status if available
    if email_service.email_system:
        system_status = email_service.email_system.get_system_status()
        status.update({
            'system_metrics': system_status['system_metrics'],
            'agent_status': system_status['agents'],
            'parser_stats': system_status['parser_stats'],
            'router_stats': system_status['router_stats']
        })

    return jsonify(status)

@app.route('/metrics')
def metrics():
    """Prometheus-style metrics endpoint"""
    status = email_service.get_status()

    metrics = []
    metrics.append(f"happy_buttons_emails_processed_total {status['emails_processed']}")
    metrics.append(f"happy_buttons_service_up {1 if status['running'] else 0}")

    if status['uptime_seconds']:
        metrics.append(f"happy_buttons_uptime_seconds {status['uptime_seconds']}")

    return '\n'.join(metrics), 200, {'Content-Type': 'text/plain'}

def run_flask_app():
    """Run Flask app in a separate thread"""
    app.run(host='0.0.0.0', port=8081, debug=False, use_reloader=False)

async def main():
    """Main service entry point"""
    # Start Flask health check server in background thread
    flask_thread = Thread(target=run_flask_app, daemon=True)
    flask_thread.start()

    # Signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(email_service.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start email service
    try:
        await email_service.start()
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Service failed: {str(e)}")
    finally:
        await email_service.stop()

if __name__ == '__main__':
    asyncio.run(main())