#!/usr/bin/env python3
"""
Direct check of support@h-bu.de mailbox for agent emails
"""

import imaplib
import email
import yaml
from datetime import datetime


def check_support_mailbox():
    """Check support@h-bu.de mailbox directly for agent task emails"""

    print("📧 CHECKING SUPPORT@H-BU.DE MAILBOX FOR AGENT EMAILS")
    print("=" * 60)

    # Load email configuration
    with open('sim/config/company_release2.yaml', 'r') as f:
        config = yaml.safe_load(f)

    imap_config = config['email']['servers']['imap']

    try:
        # Connect to IMAP server
        print("🔌 Connecting to IMAP server...")
        mail = imaplib.IMAP4_SSL(imap_config['server'], imap_config['port'])

        # Try to login with support@h-bu.de credentials (same password as info)
        try:
            mail.login("support@h-bu.de", imap_config['password'])
            print("✅ Successfully logged into support@h-bu.de")
        except:
            # Fallback: Use info@h-bu.de credentials but select different folder
            print("ℹ️  Using info@h-bu.de credentials...")
            mail.login(imap_config['username'], imap_config['password'])

        # Select INBOX
        mail.select('INBOX')
        print("📂 Selected INBOX")

        # Search for ALL recent emails first
        print("\n📋 Searching for recent emails...")
        status, messages = mail.search(None, 'ALL')

        if status == 'OK' and messages[0]:
            message_ids = messages[0].split()
            total_emails = len(message_ids)
            print(f"📊 Found {total_emails} total emails in mailbox")

            # Check the most recent 10 emails
            recent_ids = message_ids[-10:] if len(message_ids) >= 10 else message_ids
            print(f"🔍 Checking last {len(recent_ids)} emails for agent tasks...")

            agent_emails_found = 0

            for i, msg_id in enumerate(reversed(recent_ids)):
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')

                    if status == 'OK':
                        # Parse email
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)

                        # Get email details
                        from_addr = email_message.get('From', 'Unknown')
                        subject = email_message.get('Subject', 'No Subject')
                        date_str = email_message.get('Date', '')

                        print(f"   📧 Email {i+1}:")
                        print(f"      From: {from_addr}")
                        print(f"      Subject: {subject}")
                        print(f"      Date: {date_str}")

                        # Check if this is an agent task email
                        if '[AGENT-TASK]' in subject:
                            agent_emails_found += 1
                            print(f"      🎯 AGENT TASK EMAIL FOUND!")

                            # Extract agent info from subject
                            if '→' in subject:
                                agent_part = subject.split('[AGENT-TASK]')[1].strip()
                                print(f"      🤖 Agent Communication: {agent_part}")

                        print()

                except Exception as e:
                    print(f"   ❌ Error reading email {msg_id}: {str(e)}")
                    continue

            print(f"🎯 RESULT: Found {agent_emails_found} agent task emails!")

        else:
            print("❌ No emails found in mailbox")

        # Also search specifically for agent task emails
        print("\n🔍 Searching specifically for [AGENT-TASK] emails...")
        status, messages = mail.search(None, 'SUBJECT', '"[AGENT-TASK]"')

        if status == 'OK' and messages[0]:
            task_message_ids = messages[0].split()
            print(f"✅ Found {len(task_message_ids)} emails with [AGENT-TASK] in subject")

            for msg_id in task_message_ids[-5:]:  # Show last 5
                try:
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    if status == 'OK':
                        email_message = email.message_from_bytes(msg_data[0][1])
                        subject = email_message.get('Subject', 'No Subject')
                        from_addr = email_message.get('From', 'Unknown')
                        date_str = email_message.get('Date', '')
                        print(f"   📧 {subject}")
                        print(f"      From: {from_addr}")
                        print(f"      Date: {date_str}")
                except Exception as e:
                    print(f"   ❌ Error: {str(e)}")
        else:
            print("❌ No [AGENT-TASK] emails found")

        mail.close()
        mail.logout()
        print("\n✅ Mailbox check completed")

    except Exception as e:
        print(f"❌ Error connecting to mailbox: {str(e)}")


if __name__ == "__main__":
    check_support_mailbox()