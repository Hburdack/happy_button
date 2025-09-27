#!/usr/bin/env python3
"""
Local Email Simulator for Agent Communication
Simulates SMTP/IMAP functionality locally to avoid rate limiting during development
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

from .agent_email_dispatcher import AgentTask

logger = logging.getLogger(__name__)


class LocalEmailSimulator:
    """Simulates email functionality locally for agent communication testing"""

    def __init__(self, data_dir: str = "data/agent_emails"):
        """Initialize the local email simulator"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Create mailbox directories
        self.mailboxes = {
            'info': self.data_dir / 'info_mailbox',
            'sales': self.data_dir / 'sales_mailbox',
            'support': self.data_dir / 'support_mailbox',
            'finance': self.data_dir / 'finance_mailbox'
        }

        for mailbox_dir in self.mailboxes.values():
            mailbox_dir.mkdir(exist_ok=True)

        # Agent to mailbox mapping
        self.agent_mailbox_mapping = {
            'info_agent': 'info',
            'orders_agent': 'sales',
            'oem_agent': 'sales',
            'supplier_agent': 'info',
            'quality_agent': 'support',
            'management_agent': 'info',
            'finance_agent': 'finance',
            'logistics_agent': 'info'
        }

        logger.info("Local email simulator initialized")

    def send_task_email(self, task: AgentTask) -> bool:
        """Simulate sending a task email by storing it locally"""
        try:
            # Determine target mailbox
            target_mailbox = self.agent_mailbox_mapping.get(task.to_agent, 'info')
            mailbox_dir = self.mailboxes[target_mailbox]

            # Create email file
            email_filename = f"task_{task.task_id}_{int(time.time())}.json"
            email_path = mailbox_dir / email_filename

            # Create email data
            email_data = {
                'task_id': task.task_id,
                'from_agent': task.from_agent,
                'to_agent': task.to_agent,
                'from_email': 'info@h-bu.de',
                'to_email': f"{target_mailbox}@h-bu.de",
                'subject': f"[AGENT-TASK] [{task.from_agent.upper()}→{task.to_agent.upper()}] {task.subject}",
                'task_type': task.task_type,
                'priority': task.priority,
                'content': task.content,
                'data': task.data,
                'created_at': task.created_at.isoformat(),
                'due_at': task.due_at.isoformat() if task.due_at else None,
                'status': task.status,
                'simulated_send_time': datetime.now().isoformat(),
                'mailbox': target_mailbox
            }

            # Write email to file
            with open(email_path, 'w') as f:
                json.dump(email_data, f, indent=2)

            logger.info(f"Simulated email sent: {email_filename} to {target_mailbox} mailbox")
            return True

        except Exception as e:
            logger.error(f"Failed to simulate email sending: {str(e)}")
            return False

    def get_agent_tasks(self, agent_type: str, limit: int = 10) -> List[AgentTask]:
        """Get tasks for a specific agent from their mailbox"""
        try:
            # Determine agent's mailbox
            mailbox_name = self.agent_mailbox_mapping.get(agent_type, 'info')
            mailbox_dir = self.mailboxes[mailbox_name]

            tasks = []

            # Read all email files in the mailbox
            for email_file in sorted(mailbox_dir.glob("task_*.json"), reverse=True):
                try:
                    with open(email_file, 'r') as f:
                        email_data = json.load(f)

                    # Check if this email is for the requested agent
                    if email_data.get('to_agent') == agent_type:
                        # Convert back to AgentTask
                        task = AgentTask(
                            task_id=email_data['task_id'],
                            from_agent=email_data['from_agent'],
                            to_agent=email_data['to_agent'],
                            task_type=email_data['task_type'],
                            priority=email_data['priority'],
                            subject=email_data.get('subject', '').replace('[AGENT-TASK]', '').strip(),
                            content=email_data['content'],
                            data=email_data.get('data', {}),
                            created_at=datetime.fromisoformat(email_data['created_at']),
                            due_at=datetime.fromisoformat(email_data['due_at']) if email_data.get('due_at') else None,
                            status=email_data.get('status', 'pending')
                        )
                        tasks.append(task)

                        if len(tasks) >= limit:
                            break

                except Exception as e:
                    logger.error(f"Error reading email file {email_file}: {str(e)}")
                    continue

            logger.info(f"Found {len(tasks)} tasks for {agent_type} in {mailbox_name} mailbox")
            return tasks

        except Exception as e:
            logger.error(f"Error getting tasks for {agent_type}: {str(e)}")
            return []

    def get_agent_task_stats(self, agent_type: str) -> Dict[str, Any]:
        """Get task statistics for an agent"""
        try:
            tasks = self.get_agent_tasks(agent_type, limit=100)

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
                'last_checked': datetime.now().isoformat(),
                'simulation_mode': True
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
                'simulation_mode': True,
                'error': str(e)
            }

    def send_task_response(self, original_task: AgentTask, response_data: Dict[str, Any], status: str = "completed") -> bool:
        """Simulate sending a task response"""
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

    def get_mailbox_summary(self) -> Dict[str, Any]:
        """Get summary of all mailboxes"""
        summary = {}

        for mailbox_name, mailbox_dir in self.mailboxes.items():
            email_files = list(mailbox_dir.glob("task_*.json"))
            summary[mailbox_name] = {
                'email_count': len(email_files),
                'mailbox_path': str(mailbox_dir),
                'latest_emails': []
            }

            # Get latest 3 emails
            for email_file in sorted(email_files, reverse=True)[:3]:
                try:
                    with open(email_file, 'r') as f:
                        email_data = json.load(f)
                    summary[mailbox_name]['latest_emails'].append({
                        'task_id': email_data['task_id'],
                        'from_agent': email_data['from_agent'],
                        'to_agent': email_data['to_agent'],
                        'subject': email_data['subject'],
                        'priority': email_data['priority'],
                        'sent_time': email_data['simulated_send_time']
                    })
                except Exception as e:
                    logger.error(f"Error reading {email_file}: {e}")

        return summary

    def clear_mailbox(self, mailbox_name: str) -> int:
        """Clear all emails from a mailbox"""
        if mailbox_name not in self.mailboxes:
            return 0

        mailbox_dir = self.mailboxes[mailbox_name]
        email_files = list(mailbox_dir.glob("task_*.json"))

        for email_file in email_files:
            try:
                email_file.unlink()
            except Exception as e:
                logger.error(f"Error deleting {email_file}: {e}")

        logger.info(f"Cleared {len(email_files)} emails from {mailbox_name} mailbox")
        return len(email_files)

    def clear_all_mailboxes(self) -> int:
        """Clear all emails from all mailboxes"""
        total_cleared = 0
        for mailbox_name in self.mailboxes.keys():
            total_cleared += self.clear_mailbox(mailbox_name)
        return total_cleared


if __name__ == "__main__":
    # Test the local email simulator
    from agent_email_dispatcher import TaskTypes

    simulator = LocalEmailSimulator()

    print("🧪 TESTING LOCAL EMAIL SIMULATOR")
    print("=" * 50)

    # Create test task
    from agent_email_dispatcher import AgentEmailDispatcher
    dispatcher = AgentEmailDispatcher()

    test_task = dispatcher.create_coordination_task(
        from_agent="orders_agent",
        to_agent="quality_agent",
        task_type=TaskTypes.ESCALATION,
        content="Test escalation message for quality agent",
        priority="high",
        data={'test': True}
    )

    # Send test email
    print("📤 Sending test email...")
    success = simulator.send_task_email(test_task)
    print(f"✅ Email sent: {success}")

    # Check tasks
    print("\n📥 Checking for tasks...")
    tasks = simulator.get_agent_tasks('quality_agent')
    print(f"✅ Found {len(tasks)} tasks for quality_agent")

    # Get mailbox summary
    print("\n📊 Mailbox Summary:")
    summary = simulator.get_mailbox_summary()
    for mailbox, info in summary.items():
        print(f"   {mailbox}: {info['email_count']} emails")

    print("\n🏁 Local email simulator test completed")