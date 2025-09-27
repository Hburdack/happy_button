#!/usr/bin/env python3
"""
Check Agent Emails in Mailboxes
Look specifically for agent task emails
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.real_email_connector import RealEmailConnector

def main():
    print("🔍 CHECKING FOR AGENT TASK EMAILS")
    print("=" * 50)

    connector = RealEmailConnector()

    # Check all emails (including read ones) to find agent tasks
    print("📧 Retrieving all recent emails (including read)...")
    emails = connector.get_real_emails(limit=20, include_read=True)

    print(f"📊 Found {len(emails)} recent emails")

    # Filter for agent task emails
    agent_task_emails = []
    for email in emails:
        subject = email.get('subject', '')
        if '[AGENT-TASK]' in subject:
            agent_task_emails.append(email)

    print(f"🤖 Found {len(agent_task_emails)} AGENT-TASK emails")

    if agent_task_emails:
        print("\n📋 AGENT TASK EMAILS:")
        for i, email in enumerate(agent_task_emails):
            print(f"\n   Email {i+1}:")
            print(f"      From: {email['from']}")
            print(f"      To: {email['to']}")
            print(f"      Subject: {email['subject']}")
            print(f"      Time: {email['timestamp']}")
            print(f"      Mailbox: {email.get('mailbox', 'unknown')}")
            print(f"      Content: {email['content'][:100]}...")
    else:
        print("\n❌ No agent task emails found")
        print("   This might mean:")
        print("   - Emails haven't arrived yet")
        print("   - Email subjects don't contain [AGENT-TASK]")
        print("   - Emails are in a different folder")

    # Show some recent emails for debugging
    print(f"\n📋 RECENT EMAILS (for debugging):")
    for i, email in enumerate(emails[:5]):
        print(f"\n   Email {i+1}:")
        print(f"      From: {email['from']}")
        print(f"      Subject: {email['subject'][:80]}...")
        print(f"      Time: {email['timestamp']}")
        print(f"      Mailbox: {email.get('mailbox', 'unknown')}")

    # Check individual mailboxes
    print(f"\n📊 MAILBOX OVERVIEW:")
    counts = connector.get_mailbox_counts()
    for dept, count in counts.items():
        print(f"   {dept}@h-bu.de: {count} total messages")

if __name__ == "__main__":
    main()