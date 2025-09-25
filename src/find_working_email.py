#!/usr/bin/env python3
"""
Find working email configuration for info@h-bu.de
Tests various common email providers and configurations
"""

import imaplib
import smtplib
import socket

def test_email_providers():
    """Test various email providers that might host info@h-bu.de"""

    print("🔍 SEARCHING FOR WORKING EMAIL CONFIGURATION")
    print("="*60)

    # Common email hosting providers
    providers = [
        {
            "name": "Gmail (Google Workspace)",
            "imap": {"server": "imap.gmail.com", "port": 993, "ssl": True},
            "smtp": {"server": "smtp.gmail.com", "port": 587, "tls": True}
        },
        {
            "name": "Microsoft 365 / Outlook",
            "imap": {"server": "outlook.office365.com", "port": 993, "ssl": True},
            "smtp": {"server": "smtp.office365.com", "port": 587, "tls": True}
        },
        {
            "name": "Yahoo Mail",
            "imap": {"server": "imap.mail.yahoo.com", "port": 993, "ssl": True},
            "smtp": {"server": "smtp.mail.yahoo.com", "port": 587, "tls": True}
        },
        {
            "name": "1&1 IONOS",
            "imap": {"server": "imap.ionos.com", "port": 993, "ssl": True},
            "smtp": {"server": "smtp.ionos.com", "port": 587, "tls": True}
        },
        {
            "name": "Strato",
            "imap": {"server": "imap.strato.de", "port": 993, "ssl": True},
            "smtp": {"server": "smtp.strato.de", "port": 587, "tls": True}
        },
        {
            "name": "ALL-INKL.COM",
            "imap": {"server": "imap.all-inkl.com", "port": 993, "ssl": True},
            "smtp": {"server": "smtp.all-inkl.com", "port": 587, "tls": True}
        },
        {
            "name": "Hostinger",
            "imap": {"server": "imap.hostinger.com", "port": 993, "ssl": True},
            "smtp": {"server": "smtp.hostinger.com", "port": 587, "tls": True}
        },
        {
            "name": "Original (mail.burdack.org)",
            "imap": {"server": "mail.burdack.org", "port": 993, "ssl": True},
            "smtp": {"server": "mail.burdack.org", "port": 587, "tls": True}
        },
        {
            "name": "Alternative burdack.org",
            "imap": {"server": "burdack.org", "port": 993, "ssl": True},
            "smtp": {"server": "burdack.org", "port": 587, "tls": True}
        }
    ]

    working_configs = []

    for provider in providers:
        print(f"\n🔍 Testing {provider['name']}...")

        # Test IMAP
        imap_works = test_imap_server(provider['imap'])
        smtp_works = test_smtp_server(provider['smtp'])

        if imap_works and smtp_works:
            working_configs.append(provider)
            print(f"   ✅ {provider['name']}: Both IMAP and SMTP working!")
        elif imap_works:
            print(f"   ⚠️  {provider['name']}: IMAP works, SMTP failed")
        elif smtp_works:
            print(f"   ⚠️  {provider['name']}: SMTP works, IMAP failed")

    return working_configs

def test_imap_server(config):
    """Test IMAP server connectivity"""
    try:
        if config.get('ssl'):
            imap = imaplib.IMAP4_SSL(config['server'], config['port'])
        else:
            imap = imaplib.IMAP4(config['server'], config['port'])

        # Try authentication (will fail but shows server is reachable)
        try:
            imap.login("info@h-bu.de", "test_password")
        except imaplib.IMAP4.error as e:
            if "authentication failed" in str(e).lower() or "login failed" in str(e).lower():
                imap.logout()
                return True  # Server is reachable, just needs correct credentials

        imap.logout()
        return False

    except socket.gaierror:
        return False
    except ConnectionRefusedError:
        return False
    except Exception:
        return False

def test_smtp_server(config):
    """Test SMTP server connectivity"""
    try:
        smtp = smtplib.SMTP(config['server'], config['port'])

        if config.get('tls'):
            smtp.starttls()

        # Try authentication (will fail but shows server is reachable)
        try:
            smtp.login("info@h-bu.de", "test_password")
        except smtplib.SMTPAuthenticationError:
            smtp.quit()
            return True  # Server is reachable, just needs correct credentials
        except Exception:
            pass

        smtp.quit()
        return False

    except socket.gaierror:
        return False
    except ConnectionRefusedError:
        return False
    except Exception:
        return False

def main():
    """Main test function"""
    working_configs = test_email_providers()

    print("\n" + "="*60)
    print("📋 RESULTS SUMMARY")
    print("="*60)

    if working_configs:
        print(f"🎉 Found {len(working_configs)} working email provider(s)!")

        for i, config in enumerate(working_configs, 1):
            print(f"\n📧 Option {i}: {config['name']}")
            print("   IMAP Configuration:")
            print(f"     server: \"{config['imap']['server']}\"")
            print(f"     port: {config['imap']['port']}")
            print(f"     ssl: {config['imap'].get('ssl', False)}")
            print("   SMTP Configuration:")
            print(f"     server: \"{config['smtp']['server']}\"")
            print(f"     port: {config['smtp']['port']}")
            print(f"     tls: {config['smtp'].get('tls', False)}")

        print(f"\n🔧 RECOMMENDED: Use Option 1 ({working_configs[0]['name']})")
        print("   Update your sim/config/company_release2.yaml:")

        best = working_configs[0]
        print("\n   email:")
        print("     servers:")
        print("       imap:")
        print(f"         server: \"{best['imap']['server']}\"")
        print(f"         port: {best['imap']['port']}")
        print(f"         ssl: {best['imap'].get('ssl', False)}")
        print("         username: \"info@h-bu.de\"")
        print("         password: \"Adrian1234&\"")
        print("       smtp:")
        print(f"         server: \"{best['smtp']['server']}\"")
        print(f"         port: {best['smtp']['port']}")
        print(f"         tls: {best['smtp'].get('tls', False)}")
        print("         username: \"info@h-bu.de\"")
        print("         password: \"Adrian1234&\"")

    else:
        print("❌ No working email configurations found.")
        print("   Possible solutions:")
        print("   • Check if info@h-bu.de is a valid email address")
        print("   • Contact your email provider for correct server settings")
        print("   • Use a test email account (Gmail/Outlook) for development")
        print("   • Check firewall/network restrictions")

if __name__ == "__main__":
    main()