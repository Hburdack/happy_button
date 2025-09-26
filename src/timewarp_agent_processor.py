"""
TimeWarp Agent Processor - Intelligent Email Processing with Time Scaling
Happy Buttons Release 2.1 - TimeWarp Professional

Manages agent-based email processing with TimeWarp time acceleration and configurable behavior
"""

import threading
import time
import queue
import random
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .timewarp_config import get_timewarp_config, AgentConfig, MailboxConfig
from .timewarp_engine import get_timewarp

logger = logging.getLogger(__name__)

class ProcessingStatus(Enum):
    """Email processing status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    FAILED = "failed"
    ON_HOLD = "on_hold"

@dataclass
class EmailProcessingTask:
    """Email processing task"""
    email_id: str
    email_data: Dict[str, Any]
    assigned_agent: str
    priority: str
    queue_time: datetime
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    status: ProcessingStatus = ProcessingStatus.QUEUED
    processing_notes: List[str] = None
    escalation_reason: Optional[str] = None
    response_generated: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.processing_notes is None:
            self.processing_notes = []

class TimeWarpAgentProcessor:
    """
    TimeWarp Agent Processor - Intelligent Email Processing System

    Features:
    - Multi-agent email processing with configurable behavior
    - TimeWarp time scaling for processing speeds
    - Intelligent routing based on email content and type
    - Escalation handling with configurable rules
    - Response generation with templates
    - Failure simulation for testing workflows
    - Comprehensive processing analytics
    """

    def __init__(self):
        self.config = get_timewarp_config()
        self.timewarp = get_timewarp()

        # Processing queues for each agent
        self.agent_queues: Dict[str, queue.PriorityQueue] = {}

        # Active processing tasks
        self.active_tasks: Dict[str, EmailProcessingTask] = {}

        # Agent threads
        self.agent_threads: Dict[str, threading.Thread] = {}

        # Processing statistics
        self.processing_stats = {
            'total_processed': 0,
            'total_failed': 0,
            'total_escalated': 0,
            'average_processing_time': 0,
            'agent_performance': {}
        }

        # System state
        self.is_running = False
        self.stop_event = threading.Event()

        # Response templates
        self.response_templates = self._load_response_templates()

        # Output directory for processed emails and responses
        self.output_dir = "data/agent_processing"
        self._ensure_output_directory()

        # Initialize agent queues
        self._initialize_agent_queues()

        logger.info("TimeWarp Agent Processor initialized")

    def _initialize_agent_queues(self):
        """Initialize processing queues for all configured agents"""
        agents = self.config.get_all_agents()

        for agent_id, agent_config in agents.items():
            self.agent_queues[agent_id] = queue.PriorityQueue()
            self.processing_stats['agent_performance'][agent_id] = {
                'emails_processed': 0,
                'average_processing_time': 0,
                'success_rate': 100.0,
                'escalation_rate': 0.0,
                'current_queue_size': 0
            }

    def _load_response_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load response templates for different email types"""
        return {
            'customer_inquiry': {
                'subject_template': 'Re: {original_subject}',
                'body_template': """Dear {customer_name},

Thank you for your inquiry regarding our button products.

We have received your request and our technical team is reviewing your specifications:
- {inquiry_summary}

{specific_response}

We will provide a detailed quotation and technical specifications within {response_timeframe}.

If you have any urgent questions, please don't hesitate to contact us directly.

Best regards,
{agent_name}
Happy Buttons GmbH
Customer Service Department

---
Reference: {email_id}
Response generated at: {response_time}""",
                'standard_responses': {
                    'pricing_request': "Our pricing team will prepare a competitive quotation based on your volume requirements.",
                    'technical_specs': "Our engineering team will provide detailed technical specifications for your application.",
                    'delivery_timeline': "We will confirm delivery schedules based on current production capacity.",
                    'quality_certification': "All required quality certificates and test reports will be included with your quotation."
                }
            },

            'oem_order': {
                'subject_template': 'Re: {original_subject} - Order Confirmation',
                'body_template': """Dear {customer_name},

Thank you for your order. We confirm receipt and immediate processing:

Order Details:
- Reference: {order_reference}
- Quantity: {quantity}
- Delivery Required: {delivery_date}
- Priority Level: HIGH (OEM Customer)

{specific_response}

Our OEM account manager will contact you within {response_timeframe} to confirm all details.

Best regards,
{agent_name}
Happy Buttons GmbH
OEM Account Management

---
Order Reference: {email_id}
Processing Priority: URGENT""",
                'standard_responses': {
                    'order_confirmation': "Order confirmed and entered into our priority production schedule.",
                    'capacity_check': "Production capacity verified - no delays expected.",
                    'quality_assurance': "Quality standards as per your specifications will be strictly maintained.",
                    'delivery_commitment': "Delivery commitment will be confirmed with detailed schedule."
                }
            },

            'quality_complaint': {
                'subject_template': 'Re: {original_subject} - Quality Investigation Initiated',
                'body_template': """Dear {customer_name},

We have received your quality concern and have immediately initiated investigation:

Issue Details:
- Batch/Order: {batch_reference}
- Issue Type: {issue_type}
- Investigation ID: INV-{investigation_id}

{specific_response}

Our Quality Control team will provide a comprehensive report within {response_timeframe}.

We apologize for any inconvenience and are committed to immediate resolution.

Best regards,
{agent_name}
Happy Buttons GmbH
Quality Control Department

---
Investigation Reference: {email_id}
Priority: URGENT""",
                'standard_responses': {
                    'investigation_started': "Quality investigation has been initiated with immediate priority.",
                    'root_cause_analysis': "Root cause analysis will be conducted by our quality experts.",
                    'corrective_action': "Corrective and preventive action plan will be implemented.",
                    'customer_compensation': "Appropriate compensation measures will be discussed with management."
                }
            },

            'supplier_update': {
                'subject_template': 'Re: {original_subject} - Acknowledged',
                'body_template': """Dear {supplier_name},

Thank you for your update. Information received and processed:

Update Details:
- Reference: {supplier_reference}
- Material: {material_type}
- Status: {update_status}

{specific_response}

Our logistics team will coordinate accordingly.

Best regards,
{agent_name}
Happy Buttons GmbH
Logistics Department

---
Reference: {email_id}""",
                'standard_responses': {
                    'delivery_acknowledged': "Delivery schedule acknowledged and updated in our system.",
                    'quality_certificate': "Quality certificate received and validated.",
                    'logistics_coordination': "Logistics team will coordinate receipt and inspection.",
                    'payment_processing': "Payment will be processed according to agreed terms."
                }
            },

            'internal_coordination': {
                'subject_template': 'Re: {original_subject} - Response',
                'body_template': """Hi {sender_name},

Thank you for your coordination request.

{specific_response}

Let me know if you need any additional information or support.

Best regards,
{agent_name}
{department_name}

---
Internal Reference: {email_id}""",
                'standard_responses': {
                    'meeting_confirmed': "Meeting attendance confirmed. I'll prepare the required materials.",
                    'status_update': "Status update prepared and will be shared at the meeting.",
                    'resource_availability': "Resource availability confirmed for the requested period.",
                    'collaboration_agreed': "Collaboration plan agreed. Will coordinate with involved teams."
                }
            }
        }

    def _ensure_output_directory(self):
        """Create output directory structure"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "processed"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "responses"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "escalated"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "failed"), exist_ok=True)

    def start_processing(self):
        """Start agent processing threads"""
        if self.is_running:
            logger.warning("Agent processor already running")
            return

        self.is_running = True
        self.stop_event.clear()

        # Start processing thread for each agent
        agents = self.config.get_all_agents()

        for agent_id, agent_config in agents.items():
            thread = threading.Thread(
                target=self._agent_processing_loop,
                args=(agent_id, agent_config),
                daemon=True,
                name=f"Agent-{agent_id}"
            )
            self.agent_threads[agent_id] = thread
            thread.start()

        logger.info(f"Started {len(self.agent_threads)} agent processing threads")

    def stop_processing(self):
        """Stop agent processing threads"""
        self.is_running = False
        self.stop_event.set()

        # Wait for threads to complete
        for agent_id, thread in self.agent_threads.items():
            if thread.is_alive():
                thread.join(timeout=2.0)
                logger.info(f"Stopped agent thread: {agent_id}")

        self.agent_threads.clear()
        logger.info("All agent processing threads stopped")

    def process_email(self, email: Dict[str, Any]) -> bool:
        """Process an email through the agent system"""
        try:
            # Determine appropriate agent based on email content and routing rules
            agent_id = self._route_email_to_agent(email)

            if not agent_id:
                logger.warning(f"No agent found for email {email.get('id', 'unknown')}")
                return False

            # Create processing task
            task = EmailProcessingTask(
                email_id=email.get('id', f"email_{int(time.time())}"),
                email_data=email,
                assigned_agent=agent_id,
                priority=email.get('priority', 'medium'),
                queue_time=datetime.now()
            )

            # Add to agent's queue with priority
            priority_value = self._get_priority_value(task.priority)
            self.agent_queues[agent_id].put((priority_value, task))

            # Update queue size statistics
            self.processing_stats['agent_performance'][agent_id]['current_queue_size'] = \
                self.agent_queues[agent_id].qsize()

            logger.debug(f"Email {task.email_id} queued for agent {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return False

    def _route_email_to_agent(self, email: Dict[str, Any]) -> Optional[str]:
        """Route email to appropriate agent based on type and configuration"""
        email_type = email.get('type', 'customer_inquiry')
        recipient = email.get('to', 'info@h-bu.de')

        # Get mailbox configuration
        mailbox_id = self.config.get_mailbox_for_email(recipient)
        if mailbox_id:
            # Get agents assigned to this mailbox
            agents = self.config.get_agents_for_mailbox(mailbox_id)
            if agents:
                # Select agent based on current queue sizes (load balancing)
                return self._select_best_agent(agents, email_type)

        # Fallback: find agents that can handle this email type
        available_agents = self.config.get_agents_for_email_type(email_type)
        if available_agents:
            return self._select_best_agent(available_agents, email_type)

        return None

    def _select_best_agent(self, available_agents: List[str], email_type: str) -> Optional[str]:
        """Select the best agent based on queue size and specialization"""
        if not available_agents:
            return None

        # Calculate score for each agent
        agent_scores = []

        for agent_id in available_agents:
            if agent_id not in self.agent_queues:
                continue

            agent_config = self.config.get_agent_config(agent_id)
            if not agent_config:
                continue

            # Base score (higher is better)
            score = 100

            # Penalize based on current queue size
            queue_size = self.agent_queues[agent_id].qsize()
            score -= queue_size * 10

            # Bonus if agent specializes in this email type
            if email_type in agent_config.email_types:
                score += 50

            # Bonus based on processing speed multiplier (lower is better for responsiveness)
            score += (2.0 - agent_config.processing_speed_multiplier) * 20

            # Performance bonus/penalty
            performance = self.processing_stats['agent_performance'][agent_id]
            score += (performance['success_rate'] - 80) * 2  # Bonus for >80% success rate

            agent_scores.append((score, agent_id))

        if not agent_scores:
            return None

        # Select agent with highest score
        agent_scores.sort(reverse=True)
        return agent_scores[0][1]

    def _get_priority_value(self, priority: str) -> int:
        """Convert priority string to numeric value for queue ordering"""
        priority_values = {
            'low': 4,
            'medium': 3,
            'high': 2,
            'urgent': 1
        }
        return priority_values.get(priority, 3)

    def _agent_processing_loop(self, agent_id: str, agent_config: AgentConfig):
        """Main processing loop for a single agent"""
        logger.info(f"Agent {agent_id} processing loop started")

        while self.is_running and not self.stop_event.is_set():
            try:
                # Get next task from queue (with timeout)
                try:
                    priority, task = self.agent_queues[agent_id].get(timeout=1.0)
                except queue.Empty:
                    continue

                # Process the task
                self._process_email_task(agent_id, agent_config, task)

                # Update queue size
                self.processing_stats['agent_performance'][agent_id]['current_queue_size'] = \
                    self.agent_queues[agent_id].qsize()

            except Exception as e:
                logger.error(f"Error in agent {agent_id} processing loop: {e}")
                time.sleep(1)

        logger.info(f"Agent {agent_id} processing loop stopped")

    def _process_email_task(self, agent_id: str, agent_config: AgentConfig, task: EmailProcessingTask):
        """Process a single email task"""
        try:
            task.start_time = datetime.now()
            task.status = ProcessingStatus.PROCESSING
            self.active_tasks[task.email_id] = task

            logger.info(f"Agent {agent_id} processing email {task.email_id}")

            # Calculate processing time based on configuration and TimeWarp scaling
            processing_time = self._calculate_processing_time(agent_config, task)

            # Simulate failure if configured
            if self._should_simulate_failure(agent_config):
                self._handle_processing_failure(agent_id, task, "Simulated processing failure")
                return

            # Check for escalation conditions
            if self._should_escalate(agent_config, task):
                self._handle_escalation(agent_id, task, "Automatic escalation based on complexity")
                return

            # Wait for processing time (scaled by TimeWarp)
            self._wait_for_processing(processing_time)

            # Generate response if required
            response = None
            if task.email_data.get('requires_response', False) and agent_config.auto_responses:
                response = self._generate_response(agent_id, agent_config, task)

            # Mark as completed
            task.completion_time = datetime.now()
            task.status = ProcessingStatus.COMPLETED
            task.response_generated = response

            # Update statistics
            self._update_processing_statistics(agent_id, task, success=True)

            # Save processed email
            self._save_processed_email(task)

            logger.info(f"Agent {agent_id} completed email {task.email_id}")

        except Exception as e:
            logger.error(f"Error processing email task {task.email_id}: {e}")
            self._handle_processing_failure(agent_id, task, str(e))

        finally:
            # Clean up active task
            self.active_tasks.pop(task.email_id, None)

    def _calculate_processing_time(self, agent_config: AgentConfig, task: EmailProcessingTask) -> float:
        """Calculate processing time considering TimeWarp scaling"""
        # Get TimeWarp multiplier
        timewarp_multiplier = 1.0
        if agent_config.timewarp_scaling:
            timewarp_status = self.timewarp.get_time_status()
            timewarp_multiplier = timewarp_status.get('multiplier', 1)

        # Get agent processing time from configuration
        processing_time = self.config.get_agent_processing_time(
            task.assigned_agent,
            task.priority,
            timewarp_multiplier
        )

        # Convert minutes to seconds
        return processing_time * 60

    def _should_simulate_failure(self, agent_config: AgentConfig) -> bool:
        """Determine if processing should fail (for testing)"""
        failure_config = agent_config.failure_simulation

        if not failure_config.get('enabled', False):
            return False

        failure_rate = failure_config.get('failure_rate', 0.0)
        return random.random() < failure_rate

    def _should_escalate(self, agent_config: AgentConfig, task: EmailProcessingTask) -> bool:
        """Determine if email should be escalated"""
        # Simple escalation logic based on priority and random complexity
        if task.priority == 'urgent':
            return random.random() < 0.3  # 30% chance for urgent emails

        # Simulate complexity assessment
        complexity = random.random()
        return self.config.should_escalate(task.assigned_agent, complexity, 1)

    def _wait_for_processing(self, processing_time: float):
        """Wait for processing time, checking for stop event"""
        start_time = time.time()
        while time.time() - start_time < processing_time:
            if self.stop_event.is_set():
                break
            time.sleep(min(1.0, processing_time - (time.time() - start_time)))

    def _generate_response(self, agent_id: str, agent_config: AgentConfig,
                          task: EmailProcessingTask) -> Dict[str, Any]:
        """Generate automatic response to email"""
        try:
            email = task.email_data
            email_type = email.get('type', 'customer_inquiry')

            # Get response template
            template_config = self.response_templates.get(email_type)
            if not template_config:
                logger.warning(f"No response template for email type: {email_type}")
                return None

            # Extract variables from original email
            variables = self._extract_response_variables(email, agent_config, task)

            # Generate subject
            subject_template = template_config['subject_template']
            subject = subject_template.format(**variables)

            # Generate body
            body_template = template_config['body_template']

            # Select appropriate standard response
            standard_responses = template_config.get('standard_responses', {})
            if standard_responses:
                response_key = random.choice(list(standard_responses.keys()))
                specific_response = standard_responses[response_key]
            else:
                specific_response = "We are processing your request and will respond shortly."

            variables['specific_response'] = specific_response

            body = body_template.format(**variables)

            response = {
                'id': f"resp_{task.email_id}_{int(time.time())}",
                'original_email_id': task.email_id,
                'from': self._get_agent_email(agent_id),
                'to': email.get('from', ''),
                'subject': subject,
                'body': body,
                'generated_by_agent': agent_id,
                'generation_time': datetime.now(),
                'response_type': 'automatic',
                'template_used': email_type
            }

            # Save response
            self._save_response(response)

            return response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None

    def _extract_response_variables(self, email: Dict[str, Any], agent_config: AgentConfig,
                                   task: EmailProcessingTask) -> Dict[str, Any]:
        """Extract variables for response template"""
        # Extract sender name from email
        from_email = email.get('from', '')
        sender_name = from_email.split('@')[0] if '@' in from_email else 'Valued Customer'

        # Basic variables
        variables = {
            'customer_name': sender_name.replace('.', ' ').title(),
            'original_subject': email.get('subject', 'Your Inquiry'),
            'agent_name': agent_config.name,
            'department_name': agent_config.name,
            'email_id': task.email_id,
            'response_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'response_timeframe': self._get_response_timeframe(agent_config, task.priority)
        }

        # Email type specific variables
        email_type = email.get('type', 'customer_inquiry')

        if email_type == 'customer_inquiry':
            variables.update({
                'inquiry_summary': 'button product specifications',
            })
        elif email_type == 'oem_order':
            variables.update({
                'order_reference': f"ORD-{random.randint(100000, 999999)}",
                'quantity': f"{random.randint(1000, 10000)} units",
                'delivery_date': (datetime.now() + timedelta(days=random.randint(14, 45))).strftime('%Y-%m-%d')
            })
        elif email_type == 'quality_complaint':
            variables.update({
                'batch_reference': f"BATCH-{random.randint(10000, 99999)}",
                'issue_type': 'quality deviation',
                'investigation_id': random.randint(10000, 99999)
            })
        elif email_type == 'supplier_update':
            variables.update({
                'supplier_name': variables['customer_name'],
                'supplier_reference': f"SUP-{random.randint(10000, 99999)}",
                'material_type': 'production materials',
                'update_status': 'acknowledged'
            })

        return variables

    def _get_response_timeframe(self, agent_config: AgentConfig, priority: str) -> str:
        """Get human-readable response timeframe"""
        processing_time_minutes = self.config.get_agent_processing_time(
            agent_config.name, priority, 1.0  # No TimeWarp scaling for customer communication
        )

        if processing_time_minutes < 60:
            return f"{int(processing_time_minutes)} minutes"
        elif processing_time_minutes < 1440:  # Less than 24 hours
            hours = int(processing_time_minutes / 60)
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            days = int(processing_time_minutes / 1440)
            return f"{days} business day{'s' if days != 1 else ''}"

    def _get_agent_email(self, agent_id: str) -> str:
        """Get email address for agent responses"""
        agent_email_mapping = {
            'customer_service': 'service@h-bu.de',
            'oem_management': 'oem@h-bu.de',
            'quality_control': 'quality@h-bu.de',
            'production_planning': 'production@h-bu.de',
            'logistics': 'logistics@h-bu.de',
            'supplier_relations': 'suppliers@h-bu.de',
            'management': 'management@h-bu.de'
        }
        return agent_email_mapping.get(agent_id, 'info@h-bu.de')

    def _handle_processing_failure(self, agent_id: str, task: EmailProcessingTask, reason: str):
        """Handle processing failure"""
        task.status = ProcessingStatus.FAILED
        task.completion_time = datetime.now()
        task.processing_notes.append(f"Processing failed: {reason}")

        self._update_processing_statistics(agent_id, task, success=False)
        self._save_failed_email(task)

        logger.warning(f"Processing failed for email {task.email_id}: {reason}")

    def _handle_escalation(self, agent_id: str, task: EmailProcessingTask, reason: str):
        """Handle email escalation"""
        task.status = ProcessingStatus.ESCALATED
        task.escalation_reason = reason
        task.completion_time = datetime.now()

        self._update_processing_statistics(agent_id, task, success=False, escalated=True)
        self._save_escalated_email(task)

        logger.info(f"Email {task.email_id} escalated: {reason}")

    def _update_processing_statistics(self, agent_id: str, task: EmailProcessingTask,
                                     success: bool, escalated: bool = False):
        """Update processing statistics"""
        stats = self.processing_stats['agent_performance'][agent_id]

        if success:
            stats['emails_processed'] += 1
            self.processing_stats['total_processed'] += 1
        elif escalated:
            stats['emails_processed'] += 1
            self.processing_stats['total_escalated'] += 1
        else:
            self.processing_stats['total_failed'] += 1

        # Update success rate
        total_attempts = stats['emails_processed'] + self.processing_stats['total_failed']
        if total_attempts > 0:
            stats['success_rate'] = (stats['emails_processed'] / total_attempts) * 100

        # Update average processing time
        if task.start_time and task.completion_time:
            processing_time = (task.completion_time - task.start_time).total_seconds() / 60
            current_avg = stats['average_processing_time']
            count = stats['emails_processed']

            if count > 1:
                stats['average_processing_time'] = ((current_avg * (count - 1)) + processing_time) / count
            else:
                stats['average_processing_time'] = processing_time

    def _save_processed_email(self, task: EmailProcessingTask):
        """Save processed email to file"""
        try:
            filename = f"{task.email_id}_processed.json"
            filepath = os.path.join(self.output_dir, "processed", filename)

            data = {
                'task': {
                    'email_id': task.email_id,
                    'assigned_agent': task.assigned_agent,
                    'priority': task.priority,
                    'queue_time': task.queue_time.isoformat(),
                    'start_time': task.start_time.isoformat() if task.start_time else None,
                    'completion_time': task.completion_time.isoformat() if task.completion_time else None,
                    'status': task.status.value,
                    'processing_notes': task.processing_notes,
                    'response_generated': task.response_generated
                },
                'original_email': task.email_data
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            logger.error(f"Error saving processed email: {e}")

    def _save_response(self, response: Dict[str, Any]):
        """Save generated response to file"""
        try:
            filename = f"{response['id']}.json"
            filepath = os.path.join(self.output_dir, "responses", filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(response, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            logger.error(f"Error saving response: {e}")

    def _save_escalated_email(self, task: EmailProcessingTask):
        """Save escalated email to file"""
        try:
            filename = f"{task.email_id}_escalated.json"
            filepath = os.path.join(self.output_dir, "escalated", filename)

            data = {
                'email_id': task.email_id,
                'escalation_reason': task.escalation_reason,
                'assigned_agent': task.assigned_agent,
                'escalation_time': task.completion_time.isoformat() if task.completion_time else None,
                'original_email': task.email_data
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            logger.error(f"Error saving escalated email: {e}")

    def _save_failed_email(self, task: EmailProcessingTask):
        """Save failed email to file"""
        try:
            filename = f"{task.email_id}_failed.json"
            filepath = os.path.join(self.output_dir, "failed", filename)

            data = {
                'email_id': task.email_id,
                'assigned_agent': task.assigned_agent,
                'failure_time': task.completion_time.isoformat() if task.completion_time else None,
                'processing_notes': task.processing_notes,
                'original_email': task.email_data
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            logger.error(f"Error saving failed email: {e}")

    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        return {
            'system_stats': self.processing_stats.copy(),
            'active_tasks': len(self.active_tasks),
            'queue_sizes': {
                agent_id: queue.qsize()
                for agent_id, queue in self.agent_queues.items()
            },
            'is_running': self.is_running,
            'total_agents': len(self.agent_queues)
        }

    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status for specific agent"""
        if agent_id not in self.processing_stats['agent_performance']:
            return {'error': f'Agent {agent_id} not found'}

        return {
            'agent_id': agent_id,
            'performance': self.processing_stats['agent_performance'][agent_id],
            'queue_size': self.agent_queues[agent_id].qsize() if agent_id in self.agent_queues else 0,
            'is_active': agent_id in self.agent_threads and self.agent_threads[agent_id].is_alive(),
            'configuration': self.config.get_agent_config(agent_id).__dict__ if self.config.get_agent_config(agent_id) else None
        }

# Global agent processor instance
agent_processor = None

def get_agent_processor() -> TimeWarpAgentProcessor:
    """Get or create the global agent processor instance"""
    global agent_processor
    if agent_processor is None:
        agent_processor = TimeWarpAgentProcessor()
    return agent_processor

def init_agent_processor() -> TimeWarpAgentProcessor:
    """Initialize and start the agent processor"""
    processor = get_agent_processor()
    processor.start_processing()
    return processor