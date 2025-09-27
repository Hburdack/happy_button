#!/usr/bin/env python3
"""
Detailed check of sales@h-bu.de mailbox for agent task emails
"""

import imaplib
import email
import yaml
from datetime import datetime
import urllib.parse


def check_sales_mailbox_detailed():
    """Check sales@h-bu.de mailbox thoroughly for agent task emails"""

    print("📧 DETAILED CHECK OF SALES@H-BU.DE MAILBOX")
    print("=" * 60)

    # Load email configuration
    with open('sim/config/company_release2.yaml', 'r') as f:
        config = yaml.safe_load(f)

    password = config['email']['servers']['imap']['password']

    try:
        # Connect to IMAP server
        print("🔌 Connecting to IMAP server...")
        mail = imaplib.IMAP4_SSL("mail.h-bu.de", 993)
        mail.login("sales@h-bu.de", password)
        mail.select('INBOX')
        print("✅ Successfully connected to sales@h-bu.de")

        # Get total email count
        status, messages = mail.search(None, 'ALL')
        if status == 'OK' and messages[0]:
            message_ids = messages[0].split()
            total_count = len(message_ids)
            print(f"📊 Total emails in sales mailbox: {total_count}")

            # Check ALL emails, not just recent ones
            print(f"🔍 Checking ALL {total_count} emails for agent tasks...")

            agent_emails_found = 0

            # Check all emails (reverse order to see newest first)
            for i, msg_id in enumerate(reversed(message_ids)):
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

                        # Check if this is an agent task email
                        is_agent_email = (
                            '[AGENT-TASK]' in subject or
                            'AGENT-TASK' in subject or
                            '5BAGENT-TASK5D' in subject or  # Base64 encoded
                            'AGENT=5FTASK' in subject or     # URL encoded
                            'ORDERS' in subject and 'AGENT' in subject or
                            'QUALITY' in subject and 'AGENT' in subject or
                            'OEM' in subject and 'AGENT' in subject or
                            'LOGISTICS' in subject and 'AGENT' in subject
                        )

                        if is_agent_email:
                            agent_emails_found += 1
                            print(f"\n   🎯 AGENT EMAIL #{agent_emails_found} FOUND!")
                            print(f"      📧 Email Position: {i+1} of {total_count}")
                            print(f"      From: {from_addr}")
                            print(f"      Subject: {subject}")
                            print(f"      Date: {date_str}")

                            # Try to decode the subject if it's encoded
                            if '=?utf-8?q?' in subject:
                                try:
                                    decoded_subject = urllib.parse.unquote(subject.replace('=?utf-8?q?', '').replace('?=', ''))
                                    print(f"      📝 Decoded: {decoded_subject}")
                                except Exception as e:
                                    print(f"      ❌ Decode error: {e}")

                            # Get email body preview
                            try:
                                if email_message.is_multipart():
                                    for part in email_message.walk():
                                        if part.get_content_type() == "text/plain":
                                            body = part.get_payload(decode=True)
                                            if body:
                                                body_text = body.decode('utf-8', errors='ignore')[:200]
                                                print(f"      📝 Body Preview: {body_text}...")
                                                break
                                else:
                                    body = email_message.get_payload(decode=True)
                                    if body:
                                        body_text = body.decode('utf-8', errors='ignore')[:200]
                                        print(f"      📝 Body Preview: {body_text}...")
                            except Exception as e:
                                print(f"      ❌ Body read error: {e}")

                        # Show progress for large mailboxes
                        if (i + 1) % 50 == 0:
                            print(f"   📊 Checked {i+1}/{total_count} emails... ({agent_emails_found} agent emails found so far)")

                except Exception as e:
                    print(f"   ❌ Error reading email {msg_id}: {str(e)}")
                    continue

            print(f"\n🎯 FINAL RESULT: Found {agent_emails_found} agent task emails in sales@h-bu.de")

            # Also search specifically for AGENT-TASK in subject
            print(f"\n🔍 Searching specifically for AGENT-TASK in subject...")
            status, task_messages = mail.search(None, 'SUBJECT', '"AGENT-TASK"')

            if status == 'OK' and task_messages[0]:
                task_ids = task_messages[0].split()
                print(f"✅ Found {len(task_ids)} emails with AGENT-TASK in subject")

                for task_id in task_ids:
                    try:
                        status, msg_data = mail.fetch(task_id, '(RFC822)')
                        if status == 'OK':
                            email_message = email.message_from_bytes(msg_data[0][1])
                            subject = email_message.get('Subject', 'No Subject')
                            from_addr = email_message.get('From', 'Unknown')
                            date_str = email_message.get('Date', '')
                            print(f"   📧 AGENT-TASK Email:")
                            print(f"      Subject: {subject}")
                            print(f"      From: {from_addr}")
                            print(f"      Date: {date_str}")
                    except Exception as e:
                        print(f"   ❌ Error: {str(e)}")
            else:
                print("❌ No emails found with AGENT-TASK in subject")

            # Check for any emails from info@h-bu.de (our agent sender)
            print(f"\n🔍 Searching for emails from info@h-bu.de...")
            status, info_messages = mail.search(None, 'FROM', '"info@h-bu.de"')

            if status == 'OK' and info_messages[0]:
                info_ids = info_messages[0].split()
                print(f"✅ Found {len(info_ids)} emails from info@h-bu.de")

                # Check the most recent 5 from info
                for info_id in info_ids[-5:]:
                    try:
                        status, msg_data = mail.fetch(info_id, '(RFC822)')
                        if status == 'OK':
                            email_message = email.message_from_bytes(msg_data[0][1])
                            subject = email_message.get('Subject', 'No Subject')
                            date_str = email_message.get('Date', '')
                            print(f"   📧 From info@h-bu.de:")
                            print(f"      Subject: {subject}")
                            print(f"      Date: {date_str}")
                    except Exception as e:
                        print(f"   ❌ Error: {str(e)}")
            else:
                print("❌ No emails found from info@h-bu.de")

        else:
            print("📭 No emails found in sales mailbox")

        mail.close()
        mail.logout()

        print("\n✅ Sales mailbox detailed check completed")

    except Exception as e:
        print(f"❌ Error connecting to sales@h-bu.de: {str(e)}")


if __name__ == "__main__":
    check_sales_mailbox_detailed()