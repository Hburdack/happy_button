#!/usr/bin/env python3
"""
Send Test Email to info@h-bu.de
Test if email reception is working
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_test_email():
    """Send test email to info@h-bu.de"""

    # Email server configuration
    smtp_server = "192.168.2.13"
    smtp_port = 587
    sender_email = "info@h-bu.de"
    password = "Adrian1234&"
    recipient_email = "info@h-bu.de"

    try:
        # Create email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # Email body
        body = f"""
Test email sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is a test to verify that the info@h-bu.de mailbox is receiving new emails.

System: Happy Buttons Release 2
Purpose: Mailbox reception test
Status: Testing email flow

If you receive this email, the mailbox is working correctly.
        """

        msg.attach(MIMEText(body, 'plain'))

        # Connect and send
        print(f"📧 Sending test email to {recipient_email}...")
        print(f"🔗 Server: {smtp_server}:{smtp_port}")

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, password)

        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()

        print("✅ Test email sent successfully!")
        print(f"📨 From: {sender_email}")
        print(f"📨 To: {recipient_email}")
        print(f"📝 Subject: Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return True

    except Exception as e:
        print(f"❌ Error sending test email: {e}")
        return False

if __name__ == "__main__":
    print("📬 HAPPY BUTTONS EMAIL TEST")
    print("=" * 50)

    success = send_test_email()

    if success:
        print("\n✅ Test completed successfully!")
        print("💡 Check the info@h-bu.de mailbox for the test email")
        print("⏱️  Wait a few seconds, then run the email checker again")
    else:
        print("\n❌ Test failed!")
        print("💡 Check email server connectivity and credentials")