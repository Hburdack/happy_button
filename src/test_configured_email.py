#!/usr/bin/env python3
"""
Test the actually configured email server (mail.burdack.org)
"""

import imaplib
import smtplib
import ssl
import socket
import yaml

def load_config():
    """Load email configuration from config file"""
    try:
        with open("../sim/config/company_release2.yaml", 'r') as f:
            config = yaml.safe_load(f)
            return config['email']['servers']
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None

def test_configured_imap(imap_config):
    """Test the configured IMAP server"""
    print("🔍 Testing configured IMAP server...")

    server = imap_config['server']
    port = imap_config['port']
    username = imap_config['username']
    password = imap_config['password']

    print(f"   Server: {server}:{port}")
    print(f"   Username: {username}")
    print(f"   SSL: {imap_config.get('ssl', False)}")

    try:
        if imap_config.get('ssl', False):
            imap = imaplib.IMAP4_SSL(server, port)
        else:
            imap = imaplib.IMAP4(server, port)

        print(f"   ✅ Connected to {server}")

        # Test login with actual credentials
        imap.login(username, password)
        print(f"   ✅ Login successful for {username}")

        # Test selecting inbox
        imap.select('INBOX')
        print(f"   ✅ INBOX selected successfully")

        # Get message count
        typ, messages = imap.search(None, 'ALL')
        message_count = len(messages[0].split())
        print(f"   📧 Found {message_count} messages in inbox")

        imap.logout()
        return True

    except socket.gaierror as e:
        print(f"   ❌ DNS resolution failed: {e}")
        return False
    except imaplib.IMAP4.error as e:
        print(f"   ❌ IMAP error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

def test_configured_smtp(smtp_config):
    """Test the configured SMTP server"""
    print("📤 Testing configured SMTP server...")

    server = smtp_config['server']
    port = smtp_config['port']
    username = smtp_config['username']
    password = smtp_config['password']

    print(f"   Server: {server}:{port}")
    print(f"   Username: {username}")
    print(f"   TLS: {smtp_config.get('tls', False)}")

    try:
        smtp = smtplib.SMTP(server, port)

        print(f"   ✅ Connected to {server}")

        if smtp_config.get('tls', False):
            smtp.starttls()
            print(f"   ✅ TLS started")

        # Test login with actual credentials
        smtp.login(username, password)
        print(f"   ✅ Login successful for {username}")

        # Test sending a test message (to self)
        from email.mime.text import MIMEText
        msg = MIMEText("This is a test message from Happy Buttons Release 2 system.")
        msg['Subject'] = 'Release 2 Email System Test'
        msg['From'] = username
        msg['To'] = username

        smtp.send_message(msg, from_addr=username, to_addrs=[username])
        print(f"   ✅ Test message sent successfully")

        smtp.quit()
        return True

    except socket.gaierror as e:
        print(f"   ❌ DNS resolution failed: {e}")
        return False
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ Authentication failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

def main():
    """Test the configured email setup"""
    print("="*60)
    print("📧 TESTING CONFIGURED EMAIL SETUP")
    print("   mail.burdack.org with info@h-bu.de")
    print("="*60)

    # Load configuration
    servers = load_config()
    if not servers:
        print("❌ Failed to load email configuration")
        return

    imap_config = servers.get('imap')
    smtp_config = servers.get('smtp')

    # Test IMAP
    if imap_config:
        imap_success = test_configured_imap(imap_config)
        print()
    else:
        print("❌ No IMAP configuration found")
        imap_success = False

    # Test SMTP
    if smtp_config:
        smtp_success = test_configured_smtp(smtp_config)
        print()
    else:
        print("❌ No SMTP configuration found")
        smtp_success = False

    # Summary
    print("="*60)
    print("📋 TEST SUMMARY")
    print("="*60)

    if imap_success and smtp_success:
        print("🎉 SUCCESS: Both IMAP and SMTP are working!")
        print("   ✅ IMAP: Can read emails from info@h-bu.de")
        print("   ✅ SMTP: Can send emails from info@h-bu.de")
        print("   🚀 Release 2 email system is ready to use!")
    elif imap_success:
        print("⚠️  PARTIAL: IMAP working, SMTP failed")
        print("   ✅ Can read emails")
        print("   ❌ Cannot send emails - check SMTP settings")
    elif smtp_success:
        print("⚠️  PARTIAL: SMTP working, IMAP failed")
        print("   ❌ Cannot read emails - check IMAP settings")
        print("   ✅ Can send emails")
    else:
        print("❌ FAILED: Neither IMAP nor SMTP working")
        print("   Check credentials and server settings")

if __name__ == "__main__":
    main()