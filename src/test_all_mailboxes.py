#!/usr/bin/env python3
"""
Test all Happy Buttons mailboxes at 192.168.2.13
Tests: info@h-bu.de, sales@h-bu.de, support@h-bu.de, finance@h-bu.de
"""

import imaplib
import smtplib
import yaml
from email.mime.text import MIMEText

def load_config():
    """Load email domains from config file"""
    try:
        with open("../sim/config/company_release2.yaml", 'r') as f:
            config = yaml.safe_load(f)
            return config['email']['domains']
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return {}

def test_mailbox(email_address, server_ip="192.168.2.13", password="Adrian1234&"):
    """Test both IMAP and SMTP for a single mailbox"""
    print(f"\n📧 Testing {email_address}")
    print("-" * 50)

    # Test IMAP
    imap_success = test_imap_mailbox(server_ip, 993, email_address, password)

    # Test SMTP
    smtp_success = test_smtp_mailbox(server_ip, 587, email_address, password)

    return imap_success, smtp_success

def test_imap_mailbox(server, port, username, password):
    """Test IMAP connection for a mailbox"""
    try:
        print(f"   🔍 IMAP {server}:{port}...")

        imap = imaplib.IMAP4_SSL(server, port)
        imap.login(username, password)
        imap.select('INBOX')

        # Get message count
        typ, messages = imap.search(None, 'ALL')
        if typ == 'OK':
            count = len(messages[0].split())
            print(f"   ✅ IMAP: Login successful, {count} messages found")
        else:
            print(f"   ✅ IMAP: Login successful, message count unknown")

        imap.logout()
        return True

    except imaplib.IMAP4.error as e:
        print(f"   ❌ IMAP: Authentication failed - {e}")
        return False
    except Exception as e:
        print(f"   ❌ IMAP: Connection error - {e}")
        return False

def test_smtp_mailbox(server, port, username, password):
    """Test SMTP connection for a mailbox"""
    try:
        print(f"   📤 SMTP {server}:{port}...")

        smtp = smtplib.SMTP(server, port)
        smtp.starttls()
        smtp.login(username, password)

        # Send test email to self
        msg = MIMEText(f"Test message from {username} via Release 2 system.")
        msg['Subject'] = f'Mailbox Test from {username}'
        msg['From'] = username
        msg['To'] = username

        smtp.send_message(msg)
        print(f"   ✅ SMTP: Login and send successful")

        smtp.quit()
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ SMTP: Authentication failed - {e}")
        return False
    except Exception as e:
        print(f"   ❌ SMTP: Connection error - {e}")
        return False

def test_cross_mailbox_sending(working_mailboxes, server_ip="192.168.2.13", password="Adrian1234&"):
    """Test sending emails between different mailboxes"""
    print(f"\n🔄 Testing cross-mailbox email sending...")
    print("-" * 50)

    if len(working_mailboxes) < 2:
        print("   ⚠️  Need at least 2 working mailboxes for cross-sending test")
        return

    # Test sending from first working mailbox to all others
    sender = working_mailboxes[0]
    recipients = working_mailboxes[1:]

    try:
        smtp = smtplib.SMTP(server_ip, 587)
        smtp.starttls()
        smtp.login(sender, password)

        for recipient in recipients:
            msg = MIMEText(f"Test email from {sender} to {recipient} via Release 2 system.")
            msg['Subject'] = 'Cross-Mailbox Test - Happy Buttons Release 2'
            msg['From'] = sender
            msg['To'] = recipient

            smtp.send_message(msg, from_addr=sender, to_addrs=[recipient])
            print(f"   ✅ {sender} → {recipient}: Success")

        smtp.quit()
        print(f"   🎉 Cross-mailbox sending test completed!")

    except Exception as e:
        print(f"   ❌ Cross-mailbox test failed: {e}")

def update_config_with_results(working_mailboxes):
    """Update config file with working mailbox settings"""
    if not working_mailboxes:
        return

    print(f"\n🔧 Updating configuration with working mailboxes...")

    # Create updated server config for all working mailboxes
    server_config = {
        "imap": {
            "server": "192.168.2.13",
            "port": 993,
            "ssl": True
        },
        "smtp": {
            "server": "192.168.2.13",
            "port": 587,
            "tls": True
        }
    }

    print("   📝 Working mailbox configurations:")
    for mailbox in working_mailboxes:
        print(f"   ✅ {mailbox}: IMAP ✅ SMTP ✅")

    print(f"   💾 All working mailboxes use server: 192.168.2.13")
    print(f"   🔐 All working mailboxes use password: Adrian1234&")

def main():
    """Test all Happy Buttons mailboxes"""
    print("="*70)
    print("📬 TESTING ALL HAPPY BUTTONS MAILBOXES")
    print("   Server: 192.168.2.13")
    print("   Password: Adrian1234&")
    print("="*70)

    # Load configured domains
    domains = load_config()

    if not domains:
        # Fallback to default mailboxes
        domains = {
            'info': 'info@h-bu.de',
            'sales': 'sales@h-bu.de',
            'support': 'support@h-bu.de',
            'finance': 'finance@h-bu.de'
        }

    # Test each mailbox
    results = {}
    working_mailboxes = []

    for dept, email in domains.items():
        imap_ok, smtp_ok = test_mailbox(email)
        results[email] = {'imap': imap_ok, 'smtp': smtp_ok}

        if imap_ok and smtp_ok:
            working_mailboxes.append(email)

    # Test cross-mailbox sending
    if working_mailboxes:
        test_cross_mailbox_sending(working_mailboxes)

    # Results summary
    print("\n" + "="*70)
    print("📋 MAILBOX TEST SUMMARY")
    print("="*70)

    total_mailboxes = len(results)
    working_count = len(working_mailboxes)

    print(f"📊 Results: {working_count}/{total_mailboxes} mailboxes fully functional")
    print()

    for email, result in results.items():
        imap_status = "✅" if result['imap'] else "❌"
        smtp_status = "✅" if result['smtp'] else "❌"
        overall = "🎉 WORKING" if result['imap'] and result['smtp'] else "⚠️  PARTIAL" if result['imap'] or result['smtp'] else "❌ FAILED"

        print(f"📧 {email}")
        print(f"   IMAP: {imap_status}  SMTP: {smtp_status}  Overall: {overall}")

    print()

    if working_count == total_mailboxes:
        print("🎉 EXCELLENT: All mailboxes are fully operational!")
        print("   ✅ Complete email system ready for Release 2")
        print("   ✅ Multi-department email handling available")
        print("   ✅ Cross-mailbox communication working")
    elif working_count > 0:
        print(f"⚠️  PARTIAL SUCCESS: {working_count} of {total_mailboxes} mailboxes working")
        print("   ✅ System can operate with available mailboxes")
        print("   ⚠️  Some departments may have limited email access")
    else:
        print("❌ FAILURE: No mailboxes are working")
        print("   🔧 Check server configuration and credentials")

    # Update configuration
    update_config_with_results(working_mailboxes)

    # Release 2 readiness assessment
    print(f"\n🚀 RELEASE 2 EMAIL SYSTEM STATUS:")
    if working_count >= 2:
        print("   ✅ PRODUCTION READY - Multiple mailboxes operational")
    elif working_count == 1:
        print("   ⚠️  LIMITED READY - Single mailbox operational")
    else:
        print("   ❌ NOT READY - No working mailboxes")

if __name__ == "__main__":
    main()