#!/usr/bin/env python3
"""
Check all h-bu.de mailboxes for agent task emails
"""

import imaplib
import email
import yaml
from datetime import datetime
import time


def check_mailbox(mailbox_address, password):
    """Check a specific mailbox for agent task emails"""

    print(f"\n📧 CHECKING {mailbox_address.upper()}")
    print("=" * 60)

    try:
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL("mail.h-bu.de", 993)
        mail.login(mailbox_address, password)
        mail.select('INBOX')

        print(f"✅ Successfully connected to {mailbox_address}")

        # Get total email count
        status, messages = mail.search(None, 'ALL')
        if status == 'OK' and messages[0]:
            total_count = len(messages[0].split())
            print(f"📊 Total emails in mailbox: {total_count}")
        else:
            total_count = 0
            print("📊 Total emails in mailbox: 0")

        # Search for recent emails (last 5)
        if total_count > 0:
            message_ids = messages[0].split()
            recent_ids = message_ids[-5:] if len(message_ids) >= 5 else message_ids

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
                        # Look for both plain and encoded AGENT-TASK
                        is_agent_email = (
                            '[AGENT-TASK]' in subject or
                            'AGENT-TASK' in subject or
                            '5BAGENT-TASK5D' in subject or  # Base64 encoded
                            'AGENT=5FTASK' in subject or     # URL encoded
                            'ORDERS' in subject and 'AGENT' in subject or
                            'QUALITY' in subject and 'AGENT' in subject or
                            'OEM' in subject and 'AGENT' in subject
                        )

                        if is_agent_email:
                            agent_emails_found += 1
                            print(f"      🎯 AGENT TASK EMAIL FOUND!")

                            # Try to decode the subject if it's encoded
                            if '=?utf-8?q?' in subject:
                                try:
                                    import urllib.parse
                                    decoded_subject = urllib.parse.unquote(subject.replace('=?utf-8?q?', '').replace('?=', ''))
                                    print(f"      📝 Decoded: {decoded_subject}")
                                except:
                                    pass

                        print()

                except Exception as e:
                    print(f"   ❌ Error reading email {msg_id}: {str(e)}")
                    continue

            print(f"🎯 AGENT EMAILS FOUND: {agent_emails_found}")

        else:
            print("📭 No emails in this mailbox")

        mail.close()
        mail.logout()

        return agent_emails_found

    except Exception as e:
        print(f"❌ Error connecting to {mailbox_address}: {str(e)}")
        return 0


def check_all_mailboxes():
    """Check all h-bu.de mailboxes for agent emails"""

    print("📧 CHECKING ALL H-BU.DE MAILBOXES FOR AGENT EMAILS")
    print("=" * 70)

    # Load email configuration
    with open('sim/config/company_release2.yaml', 'r') as f:
        config = yaml.safe_load(f)

    password = config['email']['servers']['imap']['password']

    # Define all mailboxes to check
    mailboxes = [
        'info@h-bu.de',
        'sales@h-bu.de',
        'support@h-bu.de',
        'finance@h-bu.de'
    ]

    total_agent_emails = 0

    for mailbox in mailboxes:
        agent_count = check_mailbox(mailbox, password)
        total_agent_emails += agent_count

        # Small delay between mailbox checks to be gentle on server
        time.sleep(2)

    print("\n" + "=" * 70)
    print("📊 SUMMARY OF ALL MAILBOXES")
    print("=" * 70)
    print(f"🎯 Total Agent Emails Found: {total_agent_emails}")
    print(f"📧 Mailboxes Checked: {len(mailboxes)}")
    print(f"✅ Agent Email System Status: {'WORKING' if total_agent_emails > 0 else 'NO EMAILS FOUND'}")

    if total_agent_emails > 0:
        print("\n🚀 NEXT STEPS:")
        print("• Agent emails are successfully being delivered")
        print("• Inter-agent communication is operational")
        print("• Email routing system is working correctly")
        print("• Agents can coordinate via real h-bu.de infrastructure")

    print("=" * 70)


if __name__ == "__main__":
    check_all_mailboxes()