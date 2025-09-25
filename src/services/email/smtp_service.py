"""
SMTP Email Service for Happy Buttons Release 2
Handles outbound email sending with royal courtesy templates
"""

import smtplib
import time
import logging
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import yaml
import asyncio
from queue import Queue
import threading

@dataclass
class EmailToSend:
    to: str
    subject: str
    body: str
    from_addr: Optional[str] = None
    reply_to: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[str]] = None
    priority: str = "normal"  # low, normal, high, critical
    template_used: Optional[str] = None
    courtesy_score: Optional[int] = None

@dataclass
class SendResult:
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    sent_at: Optional[float] = None

class SMTPService:
    """SMTP email sending service with queue management and royal courtesy validation"""

    def __init__(self, config_path: str = "sim/config/company_release2.yaml"):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)

        # Email server configuration (would come from env vars in production)
        self.smtp_config = {
            'server': 'smtp.gmail.com',
            'port': 587,
            'username': 'noreply@h-bu.de',
            'password': 'demo_password',  # Use env var in production
            'use_tls': True
        }

        # Email queue for batch processing
        self.email_queue = Queue()
        self.sending_thread = None
        self.is_running = False

        # Storage setup
        self.storage_dir = "data/sent_emails"
        os.makedirs(self.storage_dir, exist_ok=True)

        # Royal courtesy validation settings
        self.min_courtesy_score = 60

        # Rate limiting to prevent spam
        self.max_emails_per_minute = 30
        self.last_send_times = []

    def _load_config(self, config_path: str) -> dict:
        """Load configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.error(f"Config file not found: {config_path}")
            return {}

    def start_service(self):
        """Start the email sending service"""
        if self.is_running:
            return

        self.is_running = True
        self.sending_thread = threading.Thread(target=self._process_email_queue, daemon=True)
        self.sending_thread.start()

        self.logger.info("SMTP service started")

    def stop_service(self):
        """Stop the email sending service"""
        self.is_running = False
        if self.sending_thread:
            self.sending_thread.join(timeout=5)

        self.logger.info("SMTP service stopped")

    async def send_email(self, email: EmailToSend) -> SendResult:
        """Queue email for sending"""
        try:
            # Validate email
            validation_result = self._validate_email(email)
            if not validation_result['valid']:
                return SendResult(
                    success=False,
                    error=f"Validation failed: {validation_result['errors']}"
                )

            # Check courtesy score if provided
            if email.courtesy_score and email.courtesy_score < self.min_courtesy_score:
                self.logger.warning(f"Email courtesy score too low ({email.courtesy_score}), reviewing...")
                # In production, might queue for manual review

            # Add to queue based on priority
            priority_order = {'critical': 0, 'high': 1, 'normal': 2, 'low': 3}
            priority_value = priority_order.get(email.priority, 2)

            self.email_queue.put((priority_value, time.time(), email))

            self.logger.info(f"Email queued for sending to {email.to} (priority: {email.priority})")

            return SendResult(success=True, message_id=f"queued_{int(time.time())}")

        except Exception as e:
            self.logger.error(f"Error queueing email: {e}")
            return SendResult(success=False, error=str(e))

    def _validate_email(self, email: EmailToSend) -> Dict[str, Any]:
        """Validate email before sending"""
        errors = []
        warnings = []

        # Basic validation
        if not email.to:
            errors.append("Recipient email is required")
        elif '@' not in email.to:
            errors.append("Invalid recipient email format")

        if not email.subject:
            warnings.append("Email subject is empty")

        if not email.body:
            errors.append("Email body is required")
        elif len(email.body) < 10:
            warnings.append("Email body seems very short")

        # Royal courtesy validation
        if email.template_used:
            courtesy_validation = self._validate_royal_courtesy(email.body)
            if courtesy_validation['score'] < self.min_courtesy_score:
                warnings.append(f"Courtesy score below threshold ({courtesy_validation['score']}/{self.min_courtesy_score})")

        # Content screening (basic)
        inappropriate_words = ['spam', 'urgent money', 'click here now']
        for word in inappropriate_words:
            if word.lower() in email.body.lower():
                errors.append(f"Inappropriate content detected: {word}")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _validate_royal_courtesy(self, email_body: str) -> Dict[str, Any]:
        """Validate royal courtesy standards"""
        score = 0

        # Greeting analysis
        greetings = ['dear', 'esteemed', 'honored', 'respected']
        if any(greeting in email_body.lower() for greeting in greetings):
            score += 20

        # Politeness markers
        polite_phrases = ['please', 'thank you', 'grateful', 'appreciate', 'kindly']
        polite_count = sum(1 for phrase in polite_phrases if phrase in email_body.lower())
        score += min(polite_count * 5, 25)

        # Professional closing
        closings = ['sincerely', 'faithfully', 'regards', 'respectfully']
        if any(closing in email_body.lower() for closing in closings):
            score += 15

        # Company representation
        if 'happy buttons' in email_body.lower():
            score += 10

        # Formal language
        formal_indicators = ['shall', 'would', 'may', 'might', 'should']
        formal_count = sum(1 for indicator in formal_indicators if indicator in email_body.lower())
        score += min(formal_count * 3, 15)

        # Length and structure (professional emails should be substantial)
        if len(email_body) > 200:
            score += 10

        # Avoid casual language
        casual_words = ["hey", "hi there", "what's up", "no problem", "sure thing"]
        casual_penalty = sum(1 for word in casual_words if word in email_body.lower()) * 5
        score -= casual_penalty

        return {
            'score': max(0, min(100, score)),
            'breakdown': {
                'greeting': 20 if any(greeting in email_body.lower() for greeting in greetings) else 0,
                'politeness': min(polite_count * 5, 25),
                'closing': 15 if any(closing in email_body.lower() for closing in closings) else 0,
                'company_ref': 10 if 'happy buttons' in email_body.lower() else 0,
                'formal_language': min(formal_count * 3, 15),
                'length_structure': 10 if len(email_body) > 200 else 0,
                'casual_penalty': -casual_penalty
            }
        }

    def _process_email_queue(self):
        """Background thread to process email queue"""
        while self.is_running:
            try:
                if self.email_queue.empty():
                    time.sleep(1)
                    continue

                # Check rate limiting
                if not self._can_send_email():
                    time.sleep(2)
                    continue

                # Get next email (priority queue simulation)
                emails_to_process = []
                while not self.email_queue.empty() and len(emails_to_process) < 5:
                    emails_to_process.append(self.email_queue.get())

                # Sort by priority
                emails_to_process.sort(key=lambda x: x[0])  # Sort by priority value

                # Send emails
                for priority_value, queued_at, email in emails_to_process:
                    if self.is_running:
                        self._send_single_email(email)
                        time.sleep(0.1)  # Small delay between emails

            except Exception as e:
                self.logger.error(f"Error in email processing thread: {e}")
                time.sleep(5)

    def _can_send_email(self) -> bool:
        """Check if we can send email based on rate limiting"""
        current_time = time.time()

        # Remove timestamps older than 1 minute
        self.last_send_times = [t for t in self.last_send_times if current_time - t < 60]

        # Check if under limit
        return len(self.last_send_times) < self.max_emails_per_minute

    def _send_single_email(self, email: EmailToSend) -> SendResult:
        """Send a single email via SMTP"""
        try:
            self.logger.info(f"Sending email to {email.to}: {email.subject}")

            # Create message
            msg = MIMEMultipart()
            msg['From'] = email.from_addr or self.smtp_config['username']
            msg['To'] = email.to
            msg['Subject'] = email.subject

            if email.reply_to:
                msg['Reply-To'] = email.reply_to

            if email.cc:
                msg['Cc'] = ', '.join(email.cc)

            # Add body
            msg.attach(MIMEText(email.body, 'plain', 'utf-8'))

            # Add attachments if any
            if email.attachments:
                for attachment_path in email.attachments:
                    self._add_attachment(msg, attachment_path)

            # In production, would actually send via SMTP
            # For demo, we simulate sending
            result = self._simulate_smtp_send(msg, email)

            # Record send time for rate limiting
            self.last_send_times.append(time.time())

            # Save sent email record
            self._save_sent_email_record(email, result)

            return result

        except Exception as e:
            self.logger.error(f"Error sending email to {email.to}: {e}")
            return SendResult(success=False, error=str(e))

    def _simulate_smtp_send(self, msg: MIMEMultipart, email: EmailToSend) -> SendResult:
        """Simulate SMTP sending (replace with real SMTP in production)"""
        # In a real implementation, this would be:
        #
        # server = smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port'])
        # if self.smtp_config['use_tls']:
        #     server.starttls()
        # server.login(self.smtp_config['username'], self.smtp_config['password'])
        #
        # recipients = [email.to]
        # if email.cc:
        #     recipients.extend(email.cc)
        # if email.bcc:
        #     recipients.extend(email.bcc)
        #
        # server.send_message(msg, to_addrs=recipients)
        # server.quit()

        # For demo, simulate successful send
        message_id = f"sent_{int(time.time())}_{hash(email.to) % 10000}"
        sent_at = time.time()

        self.logger.info(f"✓ Email sent to {email.to} (simulated)")

        return SendResult(
            success=True,
            message_id=message_id,
            sent_at=sent_at
        )

    def _add_attachment(self, msg: MIMEMultipart, attachment_path: str):
        """Add attachment to email"""
        try:
            if os.path.exists(attachment_path):
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())

                encoders.encode_base64(part)

                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(attachment_path)}'
                )

                msg.attach(part)

        except Exception as e:
            self.logger.error(f"Error adding attachment {attachment_path}: {e}")

    def _save_sent_email_record(self, email: EmailToSend, result: SendResult):
        """Save record of sent email"""
        try:
            record = {
                'to': email.to,
                'subject': email.subject,
                'from': email.from_addr,
                'sent_at': result.sent_at,
                'message_id': result.message_id,
                'success': result.success,
                'error': result.error,
                'template_used': email.template_used,
                'courtesy_score': email.courtesy_score,
                'priority': email.priority
            }

            # Save to file
            record_file = f"{self.storage_dir}/sent_{int(result.sent_at or time.time())}.json"
            with open(record_file, 'w') as f:
                json.dump(record, f, indent=2)

            # Also emit event for dashboard
            event_data = {
                'type': 'email_sent',
                'email_id': result.message_id,
                'recipient': email.to,
                'subject': email.subject,
                'sent_at': result.sent_at,
                'success': result.success,
                'template': email.template_used
            }

            # Save to events directory
            events_dir = "data/events"
            os.makedirs(events_dir, exist_ok=True)
            event_file = f"{events_dir}/email_sent_{int(time.time())}.json"

            with open(event_file, 'w') as f:
                json.dump(event_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving sent email record: {e}")

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            'queue_size': self.email_queue.qsize(),
            'is_running': self.is_running,
            'recent_send_rate': len(self.last_send_times),
            'rate_limit': self.max_emails_per_minute
        }

    def get_sending_statistics(self) -> Dict[str, Any]:
        """Get email sending statistics"""
        stats = {
            'total_sent': 0,
            'sent_today': 0,
            'success_rate': 0,
            'avg_courtesy_score': 0,
            'templates_used': {}
        }

        try:
            # Count sent emails from storage
            today_start = time.time() - (24 * 3600)

            for filename in os.listdir(self.storage_dir):
                if filename.startswith('sent_') and filename.endswith('.json'):
                    try:
                        with open(f"{self.storage_dir}/{filename}", 'r') as f:
                            record = json.load(f)

                            stats['total_sent'] += 1

                            if record.get('sent_at', 0) > today_start:
                                stats['sent_today'] += 1

                            if record.get('template_used'):
                                template = record['template_used']
                                stats['templates_used'][template] = stats['templates_used'].get(template, 0) + 1

                    except Exception as e:
                        self.logger.warning(f"Error reading sent email record {filename}: {e}")

        except Exception as e:
            self.logger.error(f"Error calculating statistics: {e}")

        return stats

# Convenience function for agents
async def send_royal_email(to: str, subject: str, body: str, template: str = None,
                          priority: str = "normal", courtesy_score: int = None) -> SendResult:
    """Convenience function for sending royal courtesy emails"""

    # Get or create SMTP service instance
    # In production, this would be a singleton service
    smtp_service = SMTPService()

    if not smtp_service.is_running:
        smtp_service.start_service()

    email = EmailToSend(
        to=to,
        subject=subject,
        body=body,
        template_used=template,
        priority=priority,
        courtesy_score=courtesy_score
    )

    return await smtp_service.send_email(email)

# Demo usage
if __name__ == "__main__":
    import asyncio
    import logging

    logging.basicConfig(level=logging.INFO)

    async def demo_smtp_service():
        service = SMTPService()
        service.start_service()

        # Demo email
        demo_email = EmailToSend(
            to="customer@example.com",
            subject="Order Confirmation - Happy Buttons GmbH",
            body="""Dear Esteemed Customer,

We are delighted to confirm receipt of your order and thank you for choosing Happy Buttons GmbH.

Your order will be processed with our utmost care and attention to quality.

We remain at your distinguished service.

Yours faithfully,
Happy Buttons GmbH""",
            template_used="order_confirmation",
            priority="high",
            courtesy_score=88
        )

        result = await service.send_email(demo_email)
        print(f"Send result: {result}")

        # Check status
        await asyncio.sleep(2)
        status = service.get_queue_status()
        stats = service.get_sending_statistics()

        print(f"Queue Status: {status}")
        print(f"Statistics: {stats}")

        service.stop_service()

    asyncio.run(demo_smtp_service())