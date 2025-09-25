#!/usr/bin/env python3
"""
Test email server at IP 192.168.2.13
"""

import imaplib
import smtplib
import ssl
import socket

def test_ip_email_server():
    """Test the email server at 192.168.2.13"""

    print("="*60)
    print("📧 TESTING EMAIL SERVER AT 192.168.2.13")
    print("   Username: info@h-bu.de")
    print("   Password: Adrian1234&")
    print("="*60)

    server_ip = "192.168.2.13"
    username = "info@h-bu.de"
    password = "Adrian1234&"

    # Test IMAP
    print("🔍 Testing IMAP (port 993, SSL)...")
    imap_success = test_imap(server_ip, 993, username, password, ssl=True)

    if not imap_success:
        print("   Trying IMAP port 143 without SSL...")
        imap_success = test_imap(server_ip, 143, username, password, ssl=False)

    print()

    # Test SMTP
    print("📤 Testing SMTP (port 587, TLS)...")
    smtp_success = test_smtp(server_ip, 587, username, password, tls=True)

    if not smtp_success:
        print("   Trying SMTP port 25 without TLS...")
        smtp_success = test_smtp(server_ip, 25, username, password, tls=False)

    if not smtp_success:
        print("   Trying SMTP port 465 with SSL...")
        smtp_success = test_smtp(server_ip, 465, username, password, ssl=True)

    print()

    # Summary
    print("="*60)
    print("📋 TEST RESULTS")
    print("="*60)

    if imap_success and smtp_success:
        print("🎉 SUCCESS: Both IMAP and SMTP working!")
        print("   ✅ Can receive emails via IMAP")
        print("   ✅ Can send emails via SMTP")
        print("   🚀 Release 2 email system ready!")
    elif imap_success:
        print("⚠️  PARTIAL SUCCESS: IMAP working, SMTP failed")
        print("   ✅ Can receive emails")
        print("   ❌ Cannot send emails")
    elif smtp_success:
        print("⚠️  PARTIAL SUCCESS: SMTP working, IMAP failed")
        print("   ❌ Cannot receive emails")
        print("   ✅ Can send emails")
    else:
        print("❌ FAILED: Neither IMAP nor SMTP working")
        print("   Check server configuration and credentials")

def test_imap(server, port, username, password, ssl=False):
    """Test IMAP connection"""
    try:
        print(f"   Connecting to {server}:{port} (SSL: {ssl})...")

        if ssl:
            imap = imaplib.IMAP4_SSL(server, port)
        else:
            imap = imaplib.IMAP4(server, port)

        print(f"   ✅ Connected to IMAP server")

        # Login
        imap.login(username, password)
        print(f"   ✅ Login successful")

        # Select inbox
        imap.select('INBOX')
        print(f"   ✅ INBOX selected")

        # Get message count
        typ, messages = imap.search(None, 'ALL')
        if typ == 'OK':
            count = len(messages[0].split())
            print(f"   📧 Found {count} messages")

        imap.logout()
        return True

    except imaplib.IMAP4.error as e:
        print(f"   ❌ IMAP error: {e}")
        return False
    except socket.error as e:
        print(f"   ❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def test_smtp(server, port, username, password, tls=False, ssl=False):
    """Test SMTP connection"""
    try:
        print(f"   Connecting to {server}:{port} (TLS: {tls}, SSL: {ssl})...")

        if ssl:
            smtp = smtplib.SMTP_SSL(server, port)
        else:
            smtp = smtplib.SMTP(server, port)

        print(f"   ✅ Connected to SMTP server")

        if tls:
            smtp.starttls()
            print(f"   ✅ TLS enabled")

        # Login
        smtp.login(username, password)
        print(f"   ✅ Login successful")

        # Test sending email to self
        from email.mime.text import MIMEText
        msg = MIMEText("Test message from Happy Buttons Release 2 system.")
        msg['Subject'] = 'Email System Test'
        msg['From'] = username
        msg['To'] = username

        smtp.send_message(msg)
        print(f"   ✅ Test email sent successfully")

        smtp.quit()
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ Authentication failed: {e}")
        return False
    except socket.error as e:
        print(f"   ❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_ip_email_server()