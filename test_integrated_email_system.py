#!/usr/bin/env python3
"""
Test Integrated Email System
Tests both TimeWarp and Enhanced Business simulations with real email sending
"""

import sys
import time
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from enhanced_business_simulation import get_enhanced_simulation
from real_email_sender import get_real_email_sender

def test_enhanced_simulation():
    """Test enhanced business simulation with real email sending"""
    print("🧪 TESTING ENHANCED BUSINESS SIMULATION WITH REAL EMAILS")
    print("=" * 70)

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Get the simulation
    simulation = get_enhanced_simulation()

    # Check email sender integration
    print("📧 Email Sender Status:")
    email_sender = get_real_email_sender()
    print(f"  Real email sender available: {simulation.real_email_sender is not None}")
    print(f"  Real email sending enabled: {simulation.send_real_emails}")

    # Start the simulation with accelerated speed
    print("\n🚀 Starting Enhanced Business Simulation...")
    print("  Speed: 10x (6 seconds = 1 hour)")
    print("  Duration: 1 minute (simulates 10 hours of business)")

    simulation.start_simulation(speed_multiplier=10)

    # Let it run for 1 minute (simulates 10 hours)
    print("\n⏱️  Running simulation (1 minute = 10 business hours)...")

    start_time = time.time()
    while time.time() - start_time < 60:  # Run for 1 minute
        # Show status every 10 seconds
        if int(time.time() - start_time) % 10 == 0:
            status = simulation.get_simulation_status()
            email_status = email_sender.get_status()

            print(f"\n📊 Status at {int(time.time() - start_time)}s:")
            print(f"  Day: {status['day_number']} ({status['day_name']})")
            print(f"  Hour: {status['hour']:02d}:00")
            print(f"  Theme: {status['theme']}")
            print(f"  Emails generated: {status['total_emails_today']}")
            print(f"  Current issues: {status['current_issues']}")
            print(f"  Real emails sent: {email_status['emails_sent']}")
            print(f"  Email queue size: {email_status['queue_size']}")

        time.sleep(1)

    # Final status
    print("\n✅ SIMULATION COMPLETED")
    print("=" * 50)

    final_status = simulation.get_simulation_status()
    final_email_status = email_sender.get_status()

    print(f"📊 Final Results:")
    print(f"  Day reached: {final_status['day_number']} ({final_status['day_name']})")
    print(f"  Total display emails generated: {final_status['total_emails_today']}")
    print(f"  Total real emails sent: {final_email_status['emails_sent']}")
    print(f"  Email sending errors: {final_email_status['errors_count']}")
    print(f"  Active issues: {final_status['current_issues']}")
    print(f"  Optimization opportunities: {final_status['optimization_opportunities']}")

    # Show recent emails
    recent_emails = simulation.get_generated_emails(limit=5)
    print(f"\n📧 Recent Emails Generated:")
    for i, email in enumerate(recent_emails[-5:], 1):
        print(f"  {i}. From: {email['from']}")
        print(f"     Subject: {email['subject']}")
        print(f"     Priority: {email['priority']}")
        print(f"     Day/Hour: Day {email['day']} at {email['hour']:02d}:00")
        print(f"     Scenario: {email.get('scenario', 'Unknown')}")
        print()

    # Stop simulation
    simulation.stop_simulation()

    print("💡 CHECK YOUR EMAIL INBOX!")
    print("   New emails should now be visible in info@h-bu.de")
    print("   Real emails were sent during the simulation")

    return final_email_status['emails_sent'] > 0

def check_mailbox_after_test():
    """Check mailbox for new emails after test"""
    print("\n🔍 CHECKING MAILBOX FOR NEW EMAILS")
    print("=" * 50)

    try:
        from real_email_connector import RealEmailConnector

        # Create connector with correct config
        class SimpleEmailConnector:
            def get_real_emails(self, limit=10):
                """Simple email check using working config"""
                import imaplib
                import email
                from datetime import datetime

                emails = []
                try:
                    # Use the working config from send_test_email.py
                    mail = imaplib.IMAP4_SSL("mail.h-bu.de", 993)
                    mail.login("info@h-bu.de", "Adrian1234&")
                    mail.select('INBOX')

                    # Search for recent emails
                    status, messages = mail.search(None, 'ALL')
                    if status == 'OK':
                        # Get the last few emails
                        message_ids = messages[0].split()
                        recent_ids = message_ids[-limit:] if len(message_ids) > limit else message_ids

                        for msg_id in reversed(recent_ids):  # Newest first
                            try:
                                status, msg_data = mail.fetch(msg_id, '(RFC822)')
                                if status == 'OK':
                                    email_body = msg_data[0][1]
                                    email_message = email.message_from_bytes(email_body)

                                    # Parse basic info
                                    from_addr = email_message.get('From', 'Unknown')
                                    subject = email_message.get('Subject', 'No Subject')
                                    date_str = email_message.get('Date', '')

                                    # Parse date
                                    try:
                                        from email.utils import parsedate_to_datetime
                                        timestamp = parsedate_to_datetime(date_str)
                                    except:
                                        timestamp = datetime.now()

                                    emails.append({
                                        'from': from_addr,
                                        'subject': subject,
                                        'timestamp': timestamp,
                                        'date_str': date_str
                                    })

                            except Exception as e:
                                print(f"Error parsing email: {e}")

                    mail.close()
                    mail.logout()

                except Exception as e:
                    print(f"Error connecting to mailbox: {e}")

                return emails

        # Check emails
        connector = SimpleEmailConnector()
        emails = connector.get_real_emails(limit=10)

        print(f"📧 Found {len(emails)} emails in mailbox:")
        print()

        # Show recent emails with timestamps
        for i, email in enumerate(emails, 1):
            timestamp = email['timestamp']
            time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(timestamp, 'strftime') else str(timestamp)

            print(f"  {i}. [{time_str}]")
            print(f"     From: {email['from']}")
            print(f"     Subject: {email['subject']}")
            print()

        # Check if we have very recent emails (last 5 minutes)
        now = datetime.now()
        recent_emails = []
        for email in emails:
            try:
                if hasattr(email['timestamp'], 'replace'):
                    # Make it timezone naive for comparison
                    email_time = email['timestamp'].replace(tzinfo=None)
                    if (now - email_time).total_seconds() < 300:  # 5 minutes
                        recent_emails.append(email)
            except:
                pass

        print(f"🔥 RECENT EMAILS (last 5 minutes): {len(recent_emails)}")
        for email in recent_emails:
            print(f"  ✅ {email['from']}: {email['subject']}")

        return len(recent_emails) > 0

    except Exception as e:
        print(f"❌ Error checking mailbox: {e}")
        return False

if __name__ == "__main__":
    print("🎯 INTEGRATED EMAIL SYSTEM TEST")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Test enhanced simulation with real email sending
    success = test_enhanced_simulation()

    # Wait a moment for emails to be processed
    print("\n⏱️  Waiting 10 seconds for emails to be delivered...")
    time.sleep(10)

    # Check mailbox
    has_new_emails = check_mailbox_after_test()

    print("\n" + "=" * 70)
    print("🎯 FINAL RESULTS")
    print("=" * 70)

    if success and has_new_emails:
        print("✅ SUCCESS! Integrated email system is working!")
        print("   ✓ Enhanced Business Simulation generated emails")
        print("   ✓ Real emails were sent to info@h-bu.de")
        print("   ✓ New emails are visible in the mailbox")
        print("\n🎉 The user will now see NEW emails in the dashboard!")
    elif success:
        print("⚠️  PARTIAL SUCCESS")
        print("   ✓ Enhanced Business Simulation generated emails")
        print("   ✓ Real emails were sent")
        print("   ❓ May take a few minutes for emails to appear")
    else:
        print("❌ FAILED")
        print("   ❌ Email sending or simulation failed")

    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")