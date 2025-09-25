"""
Release 2 Main Orchestrator
Coordinates the complete Happy Buttons classic company simulation
Email → Order → Production → Logistics → Delivery → Invoice
"""

import asyncio
import logging
import time
import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Import Release 2 services
from services.email.imap_service import IMAPService
from services.email.smtp_service import SMTPService, EmailToSend
from services.order.state_machine import OrderStateMachine, OrderState
from parsers.pdf.pdf_parser import PDFParser

# Import agents
from agents.business.base_agent_v2 import BaseAgent, AgentTask, TaskPriority
from agents.business.info_agent import InfoAgent
from agents.business.sales_agent import SalesAgent

@dataclass
class SystemMetrics:
    """System-wide performance metrics"""
    emails_processed: int = 0
    orders_created: int = 0
    orders_completed: int = 0
    avg_processing_time: float = 0.0
    auto_handled_rate: float = 0.0
    active_agents: int = 0
    system_uptime: float = 0.0

class Release2Orchestrator:
    """
    Main orchestrator for Release 2 - Classic Company Simulation

    Coordinates:
    - Email ingestion (IMAP) → Processing → Response (SMTP)
    - Order lifecycle management
    - Agent coordination and task distribution
    - KPI tracking and dashboard integration
    - Event-driven workflow orchestration
    """

    def __init__(self, config_path: str = "sim/config/company_release2.yaml"):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.start_time = time.time()

        # Initialize services
        self.imap_service = IMAPService(config_path)
        self.smtp_service = SMTPService(config_path)
        self.order_machine = OrderStateMachine(config_path)
        self.pdf_parser = PDFParser()

        # Initialize agents
        self.agents: Dict[str, BaseAgent] = {}
        self.active_tasks: Dict[str, AgentTask] = {}

        # System state
        self.is_running = False
        self.metrics = SystemMetrics()

        # Event system
        self.event_handlers = {}
        self.pending_events = []

        # Storage setup
        self._setup_storage()

        self.logger.info("Release 2 Orchestrator initialized")

    def _setup_storage(self):
        """Setup storage directories for orchestrator"""
        directories = [
            "data/orchestrator",
            "data/events",
            "data/metrics",
            "data/dashboard"
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    async def start_system(self):
        """Start the complete Release 2 system"""
        try:
            self.logger.info("Starting Release 2 Classic Company Simulation...")

            # Step 1: Initialize agents
            await self._initialize_agents()

            # Step 2: Start email services
            await self._start_email_services()

            # Step 3: Start orchestration loop
            self.is_running = True
            self.logger.info("🚀 Release 2 system started successfully!")

            # Start main orchestration loop
            await self._run_orchestration_loop()

        except Exception as e:
            self.logger.error(f"Error starting system: {e}")
            await self.shutdown_system()

    async def _initialize_agents(self):
        """Initialize and register all business agents"""
        self.logger.info("Initializing business agents...")

        # Create core agents
        agents_to_create = [
            ("InfoAgent", InfoAgent),
            ("SalesAgent", SalesAgent),
            # Add more agents as they are implemented
        ]

        for agent_name, agent_class in agents_to_create:
            try:
                agent = agent_class()
                self.agents[agent_name] = agent

                # Register event handlers
                await self._register_agent_events(agent)

                self.logger.info(f"✓ {agent_name} initialized")

            except Exception as e:
                self.logger.error(f"Error initializing {agent_name}: {e}")

        self.metrics.active_agents = len(self.agents)
        self.logger.info(f"Initialized {len(self.agents)} business agents")

    async def _register_agent_events(self, agent: BaseAgent):
        """Register agent with orchestrator event system"""
        # Register common event handlers
        if agent.agent_id == "InfoAgent":
            self.event_handlers['email_received'] = agent._handle_email_received
        elif agent.agent_id == "SalesAgent":
            self.event_handlers['order_created'] = agent._handle_order_created

    async def _start_email_services(self):
        """Start email ingestion and sending services"""
        self.logger.info("Starting email services...")

        # Start SMTP service for outbound email
        self.smtp_service.start_service()

        # In production, would connect to real mailboxes
        # For demo, we'll simulate email connections
        self.logger.info("✓ Email services started (demo mode)")

    async def _run_orchestration_loop(self):
        """Main orchestration loop - coordinates all system activities"""
        self.logger.info("Starting orchestration loop...")

        loop_count = 0
        while self.is_running:
            try:
                loop_start = time.time()

                # Core orchestration tasks
                await self._process_incoming_emails()
                await self._process_agent_tasks()
                await self._process_order_state_machine()
                await self._update_system_metrics()
                await self._emit_dashboard_events()

                # Periodic tasks
                loop_count += 1
                if loop_count % 10 == 0:  # Every 10 loops
                    await self._periodic_maintenance()

                # Calculate loop time and sleep
                loop_time = time.time() - loop_start
                sleep_time = max(0.1, 1.0 - loop_time)  # Target 1-second loops
                await asyncio.sleep(sleep_time)

            except Exception as e:
                self.logger.error(f"Error in orchestration loop: {e}")
                await asyncio.sleep(5)  # Back off on error

    async def _process_incoming_emails(self):
        """Process incoming emails from all mailboxes"""
        try:
            # In production, would poll IMAP for new emails
            # For demo, we'll simulate email processing

            # Check for demo emails (from file system or test data)
            demo_emails = await self._get_demo_emails()

            for email_data in demo_emails:
                await self._handle_incoming_email(email_data)

        except Exception as e:
            self.logger.error(f"Error processing incoming emails: {e}")

    async def _get_demo_emails(self) -> List[Dict[str, Any]]:
        """Get demo emails for simulation"""
        # In a real implementation, this would call imap_service.poll_all_mailboxes()
        # For demo, return sample emails periodically

        demo_emails = []

        # Generate a demo email every 30 seconds
        if int(time.time()) % 30 == 0 and hasattr(self, '_last_demo_email'):
            current_time = time.time()
            if current_time - getattr(self, '_last_demo_email', 0) > 25:
                demo_emails.append(self._create_demo_email())
                self._last_demo_email = current_time

        return demo_emails

    def _create_demo_email(self) -> Dict[str, Any]:
        """Create a demo email for testing"""
        import random

        email_types = [
            {
                'from': 'customer@oem1.com',
                'to': 'info@h-bu.de',
                'subject': 'Urgent Order Request - Premium Buttons',
                'body': 'Dear Happy Buttons, we need 5000 premium buttons for our production line. Please send quotation ASAP.',
                'type': 'order_request'
            },
            {
                'from': 'support@customer.com',
                'to': 'support@h-bu.de',
                'subject': 'Question about button specifications',
                'body': 'Hello, we need technical specifications for BTN-001 buttons. Can you help?',
                'type': 'support_inquiry'
            },
            {
                'from': 'finance@bigcorp.com',
                'to': 'finance@h-bu.de',
                'subject': 'Invoice inquiry - Order #12345',
                'body': 'Dear finance team, we have a question about invoice #INV-2024-001.',
                'type': 'billing_inquiry'
            }
        ]

        selected_email = random.choice(email_types)
        email_id = f"demo_{int(time.time())}_{random.randint(1000, 9999)}"

        return {
            'id': email_id,
            'from': selected_email['from'],
            'to': selected_email['to'],
            'subject': selected_email['subject'],
            'body': selected_email['body'],
            'timestamp': time.time(),
            'attachments': [],
            'type': selected_email['type']
        }

    async def _handle_incoming_email(self, email_data: Dict[str, Any]):
        """Handle a single incoming email"""
        try:
            self.logger.info(f"Processing email {email_data['id']} from {email_data['from']}")

            # Route to InfoAgent for initial processing
            if "InfoAgent" in self.agents:
                info_agent = self.agents["InfoAgent"]

                # Create processing task
                task = AgentTask(
                    id=f"email_{email_data['id']}",
                    type='process_email',
                    priority=TaskPriority.NORMAL,
                    data=email_data
                )

                await info_agent.assign_task(task)
                self.active_tasks[task.id] = task

            # Emit email received event
            await self._emit_event('email_received', email_data)

            self.metrics.emails_processed += 1

        except Exception as e:
            self.logger.error(f"Error handling email {email_data.get('id')}: {e}")

    async def _process_agent_tasks(self):
        """Process pending tasks across all agents"""
        try:
            for agent_name, agent in self.agents.items():
                # Process next task if agent is available
                if agent.status.value == "idle" and agent.task_queue:
                    result = await agent.process_next_task()

                    if result:
                        await self._handle_task_completion(agent_name, result)

        except Exception as e:
            self.logger.error(f"Error processing agent tasks: {e}")

    async def _handle_task_completion(self, agent_name: str, result: Dict[str, Any]):
        """Handle completion of agent task"""
        try:
            task_type = result.get('task_type', 'unknown')
            self.logger.info(f"{agent_name} completed {task_type} task")

            # Handle specific task completions
            if task_type == 'process_email' and result.get('order_created'):
                await self._handle_order_creation(result)

            elif task_type == 'process_order':
                await self._handle_order_processing(result)

            # Update metrics
            await self._update_task_metrics(agent_name, result)

        except Exception as e:
            self.logger.error(f"Error handling task completion: {e}")

    async def _handle_order_creation(self, result: Dict[str, Any]):
        """Handle new order creation"""
        order_id = result.get('order_created')
        if order_id:
            self.metrics.orders_created += 1
            self.logger.info(f"Order {order_id} created from email processing")

            # Emit order creation event for SalesAgent
            await self._emit_event('order_created', {'order_id': order_id})

    async def _handle_order_processing(self, result: Dict[str, Any]):
        """Handle order processing completion"""
        order_id = result.get('order_id')
        if order_id and result.get('auto_approved'):
            self.logger.info(f"Order {order_id} auto-approved by SalesAgent")

    async def _process_order_state_machine(self):
        """Process order state transitions"""
        try:
            # Get orders that need state transitions
            pending_orders = self.order_machine.get_orders_by_state(OrderState.CREATED)

            for order in pending_orders:
                # Check if order has been in CREATED state too long
                time_in_state = time.time() - order.created_at
                if time_in_state > 300:  # 5 minutes demo timeout
                    # Auto-transition for demo
                    success = self.order_machine.transition_order(
                        order.id,
                        OrderState.CONFIRMED,
                        "SystemOrchestrator",
                        "Auto-confirmed for demo"
                    )
                    if success:
                        self.logger.info(f"Auto-confirmed order {order.id}")

            # Check for completed orders
            completed_orders = self.order_machine.get_orders_by_state(OrderState.CLOSED)
            self.metrics.orders_completed = len(completed_orders)

        except Exception as e:
            self.logger.error(f"Error processing order state machine: {e}")

    async def _update_system_metrics(self):
        """Update system-wide metrics"""
        try:
            # Calculate uptime
            self.metrics.system_uptime = time.time() - self.start_time

            # Calculate auto-handled rate
            if self.metrics.emails_processed > 0:
                # In real system, would calculate based on human intervention
                self.metrics.auto_handled_rate = 85.0  # Demo value

            # Get order statistics
            order_stats = self.order_machine.get_order_statistics()
            if order_stats:
                self.metrics.avg_processing_time = order_stats.get('avg_processing_time', 0)

            # Save metrics to file for dashboard
            await self._save_metrics_to_file()

        except Exception as e:
            self.logger.error(f"Error updating system metrics: {e}")

    async def _save_metrics_to_file(self):
        """Save current metrics to file for dashboard"""
        try:
            metrics_data = {
                'timestamp': time.time(),
                'emails_processed': self.metrics.emails_processed,
                'orders_created': self.metrics.orders_created,
                'orders_completed': self.metrics.orders_completed,
                'auto_handled_rate': self.metrics.auto_handled_rate,
                'avg_processing_time': self.metrics.avg_processing_time,
                'active_agents': self.metrics.active_agents,
                'system_uptime': self.metrics.system_uptime,
                'agent_status': {name: agent.get_status() for name, agent in self.agents.items()}
            }

            metrics_file = "data/metrics/current_metrics.json"
            with open(metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving metrics: {e}")

    async def _emit_dashboard_events(self):
        """Emit events for dashboard consumption"""
        try:
            # Create dashboard update event
            dashboard_event = {
                'type': 'system_status_update',
                'timestamp': time.time(),
                'metrics': {
                    'emails_processed': self.metrics.emails_processed,
                    'orders_created': self.metrics.orders_created,
                    'auto_handled_rate': self.metrics.auto_handled_rate,
                    'active_agents': self.metrics.active_agents,
                    'uptime': self.metrics.system_uptime
                },
                'agents': {name: agent.status.value for name, agent in self.agents.items()}
            }

            # Save dashboard event
            event_file = f"data/dashboard/status_update_{int(time.time())}.json"
            with open(event_file, 'w') as f:
                json.dump(dashboard_event, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error emitting dashboard events: {e}")

    async def _periodic_maintenance(self):
        """Periodic maintenance tasks"""
        try:
            self.logger.debug("Running periodic maintenance...")

            # Clean up old event files (keep last 100)
            await self._cleanup_old_events()

            # Update agent coordination state
            await self._update_agent_coordination()

            # Check system health
            await self._check_system_health()

        except Exception as e:
            self.logger.error(f"Error in periodic maintenance: {e}")

    async def _cleanup_old_events(self):
        """Clean up old event files to prevent disk space issues"""
        try:
            events_dir = "data/events"
            if os.path.exists(events_dir):
                event_files = sorted([f for f in os.listdir(events_dir) if f.endswith('.json')])

                # Keep only the most recent 100 events
                if len(event_files) > 100:
                    files_to_remove = event_files[:-100]
                    for filename in files_to_remove:
                        os.remove(f"{events_dir}/{filename}")

        except Exception as e:
            self.logger.error(f"Error cleaning up events: {e}")

    async def _update_agent_coordination(self):
        """Update agent coordination and load balancing"""
        try:
            # Simple load balancing - distribute tasks to least busy agents
            for agent_name, agent in self.agents.items():
                if len(agent.task_queue) > 10:  # High load
                    self.logger.warning(f"{agent_name} has high task queue ({len(agent.task_queue)})")

        except Exception as e:
            self.logger.error(f"Error updating agent coordination: {e}")

    async def _check_system_health(self):
        """Check overall system health"""
        try:
            health_status = {
                'status': 'healthy',
                'agents_healthy': all(agent.status.value != 'error' for agent in self.agents.values()),
                'services_running': self.smtp_service.is_running,
                'uptime': self.metrics.system_uptime,
                'last_check': time.time()
            }

            # Save health status
            health_file = "data/orchestrator/health_status.json"
            with open(health_file, 'w') as f:
                json.dump(health_status, f, indent=2)

            if not health_status['agents_healthy']:
                self.logger.warning("Some agents are in error state")

        except Exception as e:
            self.logger.error(f"Error checking system health: {e}")

    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit system event"""
        try:
            event = {
                'type': event_type,
                'timestamp': time.time(),
                'data': data,
                'source': 'Release2Orchestrator'
            }

            # Call registered event handlers
            if event_type in self.event_handlers:
                handler = self.event_handlers[event_type]
                # Create a simple event object for the handler
                class SimpleEvent:
                    def __init__(self, data):
                        self.data = data

                await handler(SimpleEvent(data))

            # Save event to file
            event_file = f"data/events/orchestrator_event_{int(time.time())}.json"
            with open(event_file, 'w') as f:
                json.dump(event, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error emitting event {event_type}: {e}")

    async def _update_task_metrics(self, agent_name: str, result: Dict[str, Any]):
        """Update task completion metrics"""
        # Implementation would track task completion rates, times, etc.
        pass

    async def shutdown_system(self):
        """Gracefully shutdown the entire system"""
        try:
            self.logger.info("Shutting down Release 2 system...")

            # Stop orchestration loop
            self.is_running = False

            # Shutdown agents
            for agent_name, agent in self.agents.items():
                await agent.shutdown()

            # Stop email services
            self.smtp_service.stop_service()

            # Save final metrics
            await self._save_final_state()

            self.logger.info("✓ Release 2 system shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    async def _save_final_state(self):
        """Save final system state"""
        try:
            final_state = {
                'shutdown_time': time.time(),
                'total_uptime': self.metrics.system_uptime,
                'final_metrics': {
                    'emails_processed': self.metrics.emails_processed,
                    'orders_created': self.metrics.orders_created,
                    'orders_completed': self.metrics.orders_completed,
                    'auto_handled_rate': self.metrics.auto_handled_rate
                },
                'agent_final_status': {name: agent.get_status() for name, agent in self.agents.items()}
            }

            state_file = "data/orchestrator/final_state.json"
            with open(state_file, 'w') as f:
                json.dump(final_state, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving final state: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'is_running': self.is_running,
            'uptime': time.time() - self.start_time,
            'metrics': {
                'emails_processed': self.metrics.emails_processed,
                'orders_created': self.metrics.orders_created,
                'orders_completed': self.metrics.orders_completed,
                'auto_handled_rate': self.metrics.auto_handled_rate,
                'active_agents': self.metrics.active_agents
            },
            'agents': {name: agent.get_status() for name, agent in self.agents.items()},
            'services': {
                'smtp_running': self.smtp_service.is_running,
                'order_machine_active': len(self.order_machine.orders) > 0
            }
        }

# Main entry point for Release 2
async def main():
    """Main entry point for Release 2 orchestrator"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    orchestrator = Release2Orchestrator()

    try:
        # Start the system
        await orchestrator.start_system()

    except KeyboardInterrupt:
        logging.info("Received shutdown signal...")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
    finally:
        await orchestrator.shutdown_system()

if __name__ == "__main__":
    asyncio.run(main())