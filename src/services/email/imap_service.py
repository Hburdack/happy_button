"""
IMAP Email Service for Happy Buttons Release 2
Multi-mailbox email ingestion with attachment handling
"""

import imaplib
import email
import os
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from email.message import EmailMessage
import yaml

@dataclass
class EmailAttachment:
    filename: str
    content: bytes
    content_type: str
    size: int

@dataclass
class EmailMessage:
    id: str
    from_addr: str
    to_addr: str
    subject: str
    body: str
    attachments: List[EmailAttachment]
    timestamp: float
    raw_message: str

class IMAPService:
    """Multi-mailbox IMAP email ingestion service"""

    def __init__(self, config_path: str = "sim/config/company_release2.yaml"):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.connections = {}
        self.last_poll_time = {}

        # Email storage directory
        self.storage_dir = "data/emails"
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(f"{self.storage_dir}/attachments", exist_ok=True)

    def _load_config(self, config_path: str) -> dict:
        """Load company configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.error(f"Config file not found: {config_path}")
            return {}

    def connect_mailbox(self, mailbox_name: str, server: str, username: str, password: str) -> bool:
        """Connect to a specific mailbox"""
        try:
            imap = imaplib.IMAP4_SSL(server)
            imap.login(username, password)
            imap.select('INBOX')

            self.connections[mailbox_name] = imap
            self.last_poll_time[mailbox_name] = 0

            self.logger.info(f"Connected to mailbox: {mailbox_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to {mailbox_name}: {e}")
            return False

    def connect_all_mailboxes(self) -> bool:
        """Connect to all configured mailboxes"""
        # Demo configuration - in real implementation, get from env vars
        mailbox_configs = {
            'info': {'server': 'imap.gmail.com', 'user': 'info@h-bu.de', 'pass': 'demo'},
            'finance': {'server': 'imap.gmail.com', 'user': 'finance@h-bu.de', 'pass': 'demo'},
            # Add other mailboxes as needed
        }

        success_count = 0
        for mailbox_name, config in mailbox_configs.items():
            if self.connect_mailbox(
                mailbox_name,
                config['server'],
                config['user'],
                config['pass']
            ):
                success_count += 1

        self.logger.info(f"Connected to {success_count}/{len(mailbox_configs)} mailboxes")
        return success_count > 0

    def poll_mailbox(self, mailbox_name: str) -> List[EmailMessage]:
        """Poll a specific mailbox for new emails"""
        if mailbox_name not in self.connections:
            self.logger.error(f"Mailbox not connected: {mailbox_name}")
            return []

        try:
            imap = self.connections[mailbox_name]

            # Search for emails since last poll
            search_criteria = "ALL"  # In production, use date-based search
            status, messages = imap.search(None, search_criteria)

            if status != 'OK':
                self.logger.error(f"Search failed for {mailbox_name}")
                return []

            email_messages = []
            message_ids = messages[0].split()

            # Process each message
            for msg_id in message_ids[-10:]:  # Last 10 messages for demo
                try:
                    email_msg = self._fetch_email(imap, msg_id, mailbox_name)
                    if email_msg:
                        email_messages.append(email_msg)
                except Exception as e:
                    self.logger.error(f"Error processing message {msg_id}: {e}")

            self.last_poll_time[mailbox_name] = time.time()
            return email_messages

        except Exception as e:
            self.logger.error(f"Error polling {mailbox_name}: {e}")
            return []

    def _fetch_email(self, imap: imaplib.IMAP4_SSL, msg_id: bytes, mailbox_name: str) -> Optional[EmailMessage]:
        """Fetch and parse individual email"""
        try:
            status, msg_data = imap.fetch(msg_id, '(RFC822)')
            if status != 'OK':
                return None

            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)

            # Extract basic fields
            from_addr = email_message.get('From', '')
            to_addr = email_message.get('To', '')
            subject = email_message.get('Subject', '')

            # Extract body
            body = self._extract_body(email_message)

            # Extract attachments
            attachments = self._extract_attachments(email_message, msg_id.decode())

            # Create EmailMessage object
            email_msg = EmailMessage(
                id=f"{mailbox_name}_{msg_id.decode()}_{int(time.time())}",
                from_addr=from_addr,
                to_addr=to_addr,
                subject=subject,
                body=body,
                attachments=attachments,
                timestamp=time.time(),
                raw_message=raw_email.decode('utf-8', errors='ignore')
            )

            # Save to storage
            self._save_email(email_msg)

            return email_msg

        except Exception as e:
            self.logger.error(f"Error fetching email {msg_id}: {e}")
            return None

    def _extract_body(self, email_message) -> str:
        """Extract plain text body from email"""
        body = ""

        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        continue
        else:
            try:
                body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = str(email_message.get_payload())

        return body.strip()

    def _extract_attachments(self, email_message, email_id: str) -> List[EmailAttachment]:
        """Extract attachments from email"""
        attachments = []

        if not email_message.is_multipart():
            return attachments

        for part in email_message.walk():
            if part.get_content_disposition() == 'attachment':
                filename = part.get_filename()
                if filename:
                    try:
                        content = part.get_payload(decode=True)
                        content_type = part.get_content_type()

                        # Save attachment to disk
                        attachment_path = f"{self.storage_dir}/attachments/{email_id}_{filename}"
                        with open(attachment_path, 'wb') as f:
                            f.write(content)

                        attachment = EmailAttachment(
                            filename=filename,
                            content=content,
                            content_type=content_type,
                            size=len(content)
                        )
                        attachments.append(attachment)

                        self.logger.info(f"Extracted attachment: {filename} ({len(content)} bytes)")

                    except Exception as e:
                        self.logger.error(f"Error extracting attachment {filename}: {e}")

        return attachments

    def _save_email(self, email_msg: EmailMessage):
        """Save email to storage"""
        try:
            email_file = f"{self.storage_dir}/{email_msg.id}.json"

            email_data = {
                'id': email_msg.id,
                'from': email_msg.from_addr,
                'to': email_msg.to_addr,
                'subject': email_msg.subject,
                'body': email_msg.body,
                'timestamp': email_msg.timestamp,
                'attachments': [
                    {
                        'filename': att.filename,
                        'content_type': att.content_type,
                        'size': att.size
                    } for att in email_msg.attachments
                ]
            }

            import json
            with open(email_file, 'w') as f:
                json.dump(email_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving email {email_msg.id}: {e}")

    def poll_all_mailboxes(self) -> Dict[str, List[EmailMessage]]:
        """Poll all connected mailboxes"""
        all_emails = {}

        for mailbox_name in self.connections:
            emails = self.poll_mailbox(mailbox_name)
            all_emails[mailbox_name] = emails

            if emails:
                self.logger.info(f"Retrieved {len(emails)} emails from {mailbox_name}")

        return all_emails

    def disconnect_all(self):
        """Disconnect from all mailboxes"""
        for mailbox_name, imap in self.connections.items():
            try:
                imap.logout()
                self.logger.info(f"Disconnected from {mailbox_name}")
            except Exception as e:
                self.logger.error(f"Error disconnecting from {mailbox_name}: {e}")

        self.connections.clear()

# Demo usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create service
    imap_service = IMAPService()

    # Demo: Connect and poll (would be real mailboxes in production)
    print("IMAP Service initialized")
    print("Note: This is a demo implementation. Real mailbox connections require actual credentials.")

    # Show configuration
    if imap_service.config:
        mailboxes = imap_service.config.get('mailboxes', {})
        print(f"Configured mailboxes: {list(mailboxes.keys())}")