#!/usr/bin/env python3
"""
Agent Email Dispatcher for Inter-Agent Communication
Enables agents to send and receive task emails via real mailboxes
"""

import smtplib
import imaplib
import email
import yaml
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class AgentTask:
    """Represents a task sent between agents"""
    task_id: str
    from_agent: str
    to_agent: str
    task_type: str
    priority: str
    subject: str
    content: str
    data: Dict[str, Any]
    created_at: datetime
    due_at: Optional[datetime] = None
    status: str = "pending"
    response_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'task_id': self.task_id,
            'from_agent': self.from_agent,
            'to_agent': self.to_agent,
            'task_type': self.task_type,
            'priority': self.priority,
            'subject': self.subject,
            'content': self.content,
            'data': self.data,
            'created_at': self.created_at.isoformat(),
            'due_at': self.due_at.isoformat() if self.due_at else None,
            'status': self.status,
            'response_data': self.response_data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentTask':
        """Create from dictionary"""
        return cls(
            task_id=data['task_id'],
            from_agent=data['from_agent'],
            to_agent=data['to_agent'],
            task_type=data['task_type'],
            priority=data['priority'],
            subject=data['subject'],
            content=data['content'],
            data=data['data'],
            created_at=datetime.fromisoformat(data['created_at']),
            due_at=datetime.fromisoformat(data['due_at']) if data['due_at'] else None,
            status=data.get('status', 'pending'),
            response_data=data.get('response_data')
        )


class AgentEmailDispatcher:
    """Handles email communication between agents using real mailboxes"""

    def __init__(self, config_path="sim/config/company_release2.yaml"):
        """Initialize with email server configuration"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.email_domains = self.config['email']['domains']
        self.imap_config = self.config['email']['servers']['imap']
        self.smtp_config = self.config['email']['servers']['smtp']

        # Map agent types to email addresses
        self.agent_email_mapping = {
            'info_agent': 'info@h-bu.de',
            'orders_agent': 'sales@h-bu.de',  # Orders use sales for outbound
            'oem_agent': 'sales@h-bu.de',
            'supplier_agent': 'info@h-bu.de',  # Suppliers communicate via info
            'quality_agent': 'support@h-bu.de',  # Quality uses support
            'management_agent': 'info@h-bu.de',  # Management uses info
            'finance_agent': 'finance@h-bu.de',
            'logistics_agent': 'info@h-bu.de'
        }

        # Reverse mapping for routing incoming emails
        self.email_agent_mapping = {
            'info@h-bu.de': ['info_agent', 'supplier_agent', 'management_agent', 'logistics_agent'],
            'sales@h-bu.de': ['orders_agent', 'oem_agent'],
            'support@h-bu.de': ['quality_agent'],
            'finance@h-bu.de': ['finance_agent']
        }

    def send_task_email(self, task: AgentTask) -> bool:
        """Send a task email from one agent to another"""
        try:
            # Use info@h-bu.de as sender for all emails to avoid authentication issues
            from_email = "info@h-bu.de"
            to_email = self.agent_email_mapping.get(task.to_agent, "info@h-bu.de")

            # Create email message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = f"[AGENT-TASK] [{task.from_agent.upper()}→{task.to_agent.upper()}] {task.subject}"

            # Create email body with task metadata
            email_body = self._create_task_email_body(task)
            msg.attach(MIMEText(email_body, 'plain'))

            # Add task data as JSON attachment
            task_json = json.dumps(task.to_dict(), indent=2)
            attachment = MIMEBase('application', 'json')
            attachment.set_payload(task_json)
            encoders.encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="task_{task.task_id}.json"'
            )
            msg.attach(attachment)

            # Send email via SMTP
            server = smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port'])
            server.starttls()
            server.login(self.smtp_config['username'], self.smtp_config['password'])

            text = msg.as_string()
            server.sendmail(from_email, [to_email], text)
            server.quit()

            logger.info(f"Task email sent: {task.task_id} from {task.from_agent} to {task.to_agent}")
            return True

        except Exception as e:
            logger.error(f"Failed to send task email: {str(e)}")
            return False

    def _create_task_email_body(self, task: AgentTask) -> str:
        """Create formatted email body for agent task"""
        body = f"""AGENT TASK COMMUNICATION
========================

Task ID: {task.task_id}
From Agent: {task.from_agent}
To Agent: {task.to_agent}
Task Type: {task.task_type}
Priority: {task.priority}
Created: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Due: {task.due_at.strftime('%Y-%m-%d %H:%M:%S') if task.due_at else 'No deadline'}

TASK DESCRIPTION:
{task.content}

STATUS: {task.status}

---
This is an automated inter-agent communication.
Do not reply to this email directly.
"""
        return body

    def check_for_agent_tasks(self, agent_type: str, limit: int = 10) -> List[AgentTask]:
        """Check for incoming task emails for a specific agent"""
        tasks = []

        # Get agent's email addresses
        agent_emails = []
        for email_addr, agent_types in self.email_agent_mapping.items():
            if agent_type in agent_types:
                agent_emails.append(email_addr)

        # Check each mailbox for agent tasks
        for email_addr in agent_emails:
            try:
                mailbox_tasks = self._fetch_agent_tasks_from_mailbox(email_addr, limit)
                tasks.extend(mailbox_tasks)
            except Exception as e:
                logger.error(f"Error checking agent tasks in {email_addr}: {e}")

        # Sort by priority and creation time
        tasks.sort(key=lambda t: (
            0 if t.priority == 'critical' else 1 if t.priority == 'high' else 2,
            t.created_at
        ))

        return tasks[:limit]

    def _fetch_agent_tasks_from_mailbox(self, email_address: str, limit: int) -> List[AgentTask]:
        """Fetch agent task emails from a specific mailbox"""
        tasks = []

        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(self.imap_config['server'], self.imap_config['port'])

            # Use the specific email address for login if it's not info@h-bu.de
            if email_address == "info@h-bu.de":
                mail.login(self.imap_config['username'], self.imap_config['password'])
            else:
                # For other mailboxes, try to use the same password (common in business setups)
                mail.login(email_address, self.imap_config['password'])

            mail.select('INBOX')

            # Search for all emails and filter for agent tasks
            status, messages = mail.search(None, 'ALL')

            if status == 'OK' and messages[0]:
                message_ids = messages[0].split()
                # Get recent messages only for efficiency
                recent_ids = message_ids[-50:] if len(message_ids) > 50 else message_ids

                for msg_id in reversed(recent_ids):  # Newest first
                    try:
                        # Fetch email
                        status, msg_data = mail.fetch(msg_id, '(RFC822)')

                        if status == 'OK':
                            # Parse email
                            email_body = msg_data[0][1]
                            email_message = email.message_from_bytes(email_body)

                            # Check if this is an agent task email by subject
                            subject = email_message.get('Subject', '')

                            # Decode subject if needed
                            try:
                                from email.header import decode_header
                                decoded_subject = decode_header(subject)
                                decoded_subject_str = ''
                                for part, encoding in decoded_subject:
                                    if isinstance(part, bytes):
                                        decoded_subject_str += part.decode(encoding or 'utf-8', errors='ignore')
                                    else:
                                        decoded_subject_str += part
                                subject = decoded_subject_str
                            except:
                                pass

                            if '[AGENT-TASK]' in subject:
                                # Extract agent task
                                task = self._parse_agent_task_email(email_message)
                                if task:
                                    tasks.append(task)

                    except Exception as e:
                        logger.error(f"Error parsing agent task email {msg_id}: {e}")
                        continue

            mail.close()
            mail.logout()

        except Exception as e:
            logger.error(f"Error connecting to {email_address}: {e}")

        return tasks

    def _parse_agent_task_email(self, email_message) -> Optional[AgentTask]:
        """Parse agent task from email message"""
        try:
            # Check if this is an agent task email
            subject_raw = email_message.get('Subject', '')

            # Decode the subject line properly
            try:
                from email.header import decode_header
                decoded_subject = decode_header(subject_raw)
                subject = ''
                for part, encoding in decoded_subject:
                    if isinstance(part, bytes):
                        subject += part.decode(encoding or 'utf-8', errors='ignore')
                    else:
                        subject += part
            except:
                subject = subject_raw

            if '[AGENT-TASK]' not in subject:
                return None

            # Look for JSON attachment with task data
            task_data = None

            if email_message.is_multipart():
                for part in email_message.walk():
                    content_disposition = str(part.get('Content-Disposition', ''))
                    content_type = part.get_content_type()

                    # Check for JSON attachment
                    if ('attachment' in content_disposition and
                        'task_' in content_disposition and
                        '.json' in content_disposition):

                        try:
                            payload = part.get_payload(decode=True)
                            task_data = json.loads(payload.decode('utf-8'))
                            break
                        except Exception as e:
                            logger.error(f"Error parsing task JSON: {e}")

            # If no JSON attachment, try to extract from email body
            if not task_data:
                # This is a fallback - try to parse from email body format
                body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                else:
                    body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')

                task_data = self._extract_task_from_body(body, email_message)

            if task_data:
                return AgentTask.from_dict(task_data)

        except Exception as e:
            logger.error(f"Error parsing agent task email: {e}")

        return None

    def _extract_task_from_body(self, body: str, email_message) -> Optional[Dict[str, Any]]:
        """Extract task data from email body (fallback method)"""
        try:
            lines = body.split('\n')
            task_data = {}

            for line in lines:
                line = line.strip()
                if line.startswith('Task ID:'):
                    task_data['task_id'] = line.split(':', 1)[1].strip()
                elif line.startswith('From Agent:'):
                    task_data['from_agent'] = line.split(':', 1)[1].strip()
                elif line.startswith('To Agent:'):
                    task_data['to_agent'] = line.split(':', 1)[1].strip()
                elif line.startswith('Task Type:'):
                    task_data['task_type'] = line.split(':', 1)[1].strip()
                elif line.startswith('Priority:'):
                    task_data['priority'] = line.split(':', 1)[1].strip()
                elif line.startswith('Created:'):
                    created_str = line.split(':', 1)[1].strip()
                    task_data['created_at'] = datetime.strptime(created_str, '%Y-%m-%d %H:%M:%S').isoformat()

            # Extract content between "TASK DESCRIPTION:" and "STATUS:"
            desc_start = body.find('TASK DESCRIPTION:')
            status_start = body.find('STATUS:')

            if desc_start != -1 and status_start != -1:
                content = body[desc_start + len('TASK DESCRIPTION:'):status_start].strip()
                task_data['content'] = content

            # Fill in missing fields
            task_data.setdefault('subject', email_message.get('Subject', '').replace('[AGENT-TASK]', '').strip())
            task_data.setdefault('data', {})
            task_data.setdefault('status', 'pending')
            task_data.setdefault('due_at', None)
            task_data.setdefault('response_data', None)

            return task_data

        except Exception as e:
            logger.error(f"Error extracting task from body: {e}")
            return None

    def send_task_response(self, original_task: AgentTask, response_data: Dict[str, Any],
                          status: str = "completed") -> bool:
        """Send a response to a task"""
        try:
            # Create response task
            response_task = AgentTask(
                task_id=f"resp_{original_task.task_id}",
                from_agent=original_task.to_agent,
                to_agent=original_task.from_agent,
                task_type="task_response",
                priority=original_task.priority,
                subject=f"Re: {original_task.subject}",
                content=f"Response to task {original_task.task_id}:\n\n{response_data.get('message', 'Task completed successfully')}",
                data={
                    'original_task_id': original_task.task_id,
                    'response_data': response_data,
                    'completion_status': status
                },
                created_at=datetime.now()
            )

            return self.send_task_email(response_task)

        except Exception as e:
            logger.error(f"Failed to send task response: {str(e)}")
            return False

    def create_coordination_task(self, from_agent: str, to_agent: str,
                               task_type: str, content: str,
                               priority: str = "medium",
                               data: Optional[Dict[str, Any]] = None,
                               due_hours: Optional[int] = None) -> AgentTask:
        """Create a new coordination task between agents"""

        task_id = f"coord_{uuid.uuid4().hex[:8]}"
        due_at = datetime.now() + timedelta(hours=due_hours) if due_hours else None

        return AgentTask(
            task_id=task_id,
            from_agent=from_agent,
            to_agent=to_agent,
            task_type=task_type,
            priority=priority,
            subject=f"Coordination: {task_type.replace('_', ' ').title()}",
            content=content,
            data=data or {},
            created_at=datetime.now(),
            due_at=due_at
        )

    def get_agent_task_stats(self, agent_type: str) -> Dict[str, Any]:
        """Get task statistics for an agent"""
        try:
            tasks = self.check_for_agent_tasks(agent_type, limit=100)

            total_tasks = len(tasks)
            pending_tasks = len([t for t in tasks if t.status == 'pending'])
            high_priority = len([t for t in tasks if t.priority in ['high', 'critical']])
            overdue_tasks = len([t for t in tasks if t.due_at and t.due_at < datetime.now()])

            return {
                'total_tasks': total_tasks,
                'pending_tasks': pending_tasks,
                'high_priority_tasks': high_priority,
                'overdue_tasks': overdue_tasks,
                'task_types': list(set(t.task_type for t in tasks)),
                'last_checked': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting task stats for {agent_type}: {e}")
            return {
                'total_tasks': 0,
                'pending_tasks': 0,
                'high_priority_tasks': 0,
                'overdue_tasks': 0,
                'task_types': [],
                'last_checked': datetime.now().isoformat(),
                'error': str(e)
            }


# Common task types for agent coordination
class TaskTypes:
    INVENTORY_CHECK = "inventory_check"
    APPROVAL_REQUEST = "approval_request"
    ESCALATION = "escalation"
    QUALITY_INVESTIGATION = "quality_investigation"
    CUSTOMER_CALLBACK = "customer_callback"
    COORDINATION_UPDATE = "coordination_update"
    URGENT_NOTIFICATION = "urgent_notification"
    DOCUMENT_REVIEW = "document_review"
    PRICING_REQUEST = "pricing_request"
    CAPACITY_PLANNING = "capacity_planning"


if __name__ == "__main__":
    # Test the agent email dispatcher
    dispatcher = AgentEmailDispatcher()

    print("🤖 TESTING AGENT EMAIL DISPATCHER")
    print("=" * 50)

    # Test task creation
    test_task = dispatcher.create_coordination_task(
        from_agent="info_agent",
        to_agent="orders_agent",
        task_type=TaskTypes.INVENTORY_CHECK,
        content="Please check inventory for order #12345. Customer requested 5000 units of BTN-001.",
        priority="high",
        data={"order_id": "12345", "product": "BTN-001", "quantity": 5000},
        due_hours=4
    )

    print(f"📧 Created test task: {test_task.task_id}")
    print(f"   From: {test_task.from_agent}")
    print(f"   To: {test_task.to_agent}")
    print(f"   Type: {test_task.task_type}")
    print(f"   Priority: {test_task.priority}")

    # Test sending task (commented out to avoid actual email sending in test)
    # success = dispatcher.send_task_email(test_task)
    # print(f"✅ Task sent successfully: {success}")

    # Test checking for tasks
    print(f"\n📥 Checking for pending tasks...")
    for agent_type in ['info_agent', 'orders_agent', 'quality_agent']:
        stats = dispatcher.get_agent_task_stats(agent_type)
        print(f"   {agent_type}: {stats['pending_tasks']} pending tasks")

    print(f"\n✅ Agent email dispatcher ready for inter-agent communication!")