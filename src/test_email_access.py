#!/usr/bin/env python3
"""
Test Email Access for info@h-bu.de
Tests both IMAP and SMTP connectivity
"""

import imaplib
import smtplib
import ssl
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_imap_connection():
    """Test IMAP connection to info@h-bu.de"""
    print("🔍 Testing IMAP connection for info@h-bu.de...")

    # Common IMAP servers to try
    imap_configs = [
        {"server": "imap.h-bu.de", "port": 993, "ssl": True},
        {"server": "mail.h-bu.de", "port": 993, "ssl": True},
        {"server": "imap.gmail.com", "port": 993, "ssl": True},  # If using Gmail
        {"server": "outlook.office365.com", "port": 993, "ssl": True},  # If using O365
    ]

    for config in imap_configs:
        try:
            print(f"   Trying {config['server']}:{config['port']} (SSL: {config['ssl']})...")

            if config['ssl']:
                imap = imaplib.IMAP4_SSL(config['server'], config['port'])
            else:
                imap = imaplib.IMAP4(config['server'], config['port'])

            print(f"   ✅ Connection established to {config['server']}")

            # Test login (will fail without credentials, but shows server is reachable)
            try:
                imap.login("info@h-bu.de", "test_password")
            except imaplib.IMAP4.error as e:
                if "authentication failed" in str(e).lower() or "login failed" in str(e).lower():
                    print(f"   🔐 Server reachable but needs valid credentials: {e}")
                    return config
                else:
                    print(f"   ❌ Login error: {e}")

            imap.logout()

        except socket.gaierror as e:
            print(f"   ❌ DNS resolution failed: {e}")
        except ConnectionRefusedError as e:
            print(f"   ❌ Connection refused: {e}")
        except ssl.SSLError as e:
            print(f"   ❌ SSL error: {e}")
        except Exception as e:
            print(f"   ❌ Connection error: {e}")

    print("   ❌ No IMAP servers were reachable")
    return None

def test_smtp_connection():
    """Test SMTP connection for info@h-bu.de"""
    print("📤 Testing SMTP connection for info@h-bu.de...")

    # Common SMTP servers to try
    smtp_configs = [
        {"server": "smtp.h-bu.de", "port": 587, "tls": True},
        {"server": "smtp.h-bu.de", "port": 465, "ssl": True},
        {"server": "mail.h-bu.de", "port": 587, "tls": True},
        {"server": "smtp.gmail.com", "port": 587, "tls": True},  # If using Gmail
        {"server": "smtp.office365.com", "port": 587, "tls": True},  # If using O365
    ]

    for config in smtp_configs:
        try:
            print(f"   Trying {config['server']}:{config['port']} (TLS: {config.get('tls', False)}, SSL: {config.get('ssl', False)})...")

            if config.get('ssl'):
                smtp = smtplib.SMTP_SSL(config['server'], config['port'])
            else:
                smtp = smtplib.SMTP(config['server'], config['port'])
                if config.get('tls'):
                    smtp.starttls()

            print(f"   ✅ Connection established to {config['server']}")

            # Test login (will fail without credentials, but shows server is reachable)
            try:
                smtp.login("info@h-bu.de", "test_password")
            except smtplib.SMTPAuthenticationError as e:
                print(f"   🔐 Server reachable but needs valid credentials: {e}")
                smtp.quit()
                return config
            except Exception as e:
                print(f"   ❌ Login error: {e}")

            smtp.quit()

        except socket.gaierror as e:
            print(f"   ❌ DNS resolution failed: {e}")
        except ConnectionRefusedError as e:
            print(f"   ❌ Connection refused: {e}")
        except ssl.SSLError as e:
            print(f"   ❌ SSL error: {e}")
        except Exception as e:
            print(f"   ❌ Connection error: {e}")

    print("   ❌ No SMTP servers were reachable")
    return None

def test_dns_resolution():
    """Test DNS resolution for h-bu.de domain"""
    print("🌐 Testing DNS resolution for h-bu.de domain...")

    domains_to_test = [
        "h-bu.de",
        "www.h-bu.de",
        "mail.h-bu.de",
        "imap.h-bu.de",
        "smtp.h-bu.de"
    ]

    for domain in domains_to_test:
        try:
            import socket
            ip = socket.gethostbyname(domain)
            print(f"   ✅ {domain} resolves to {ip}")
        except socket.gaierror:
            print(f"   ❌ {domain} - DNS resolution failed")

def test_mx_records():
    """Test MX records for h-bu.de domain"""
    print("📧 Testing MX records for h-bu.de...")

    try:
        import subprocess
        result = subprocess.run(['nslookup', '-type=mx', 'h-bu.de'],
                              capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            output = result.stdout
            print("   MX Record lookup result:")
            for line in output.split('\n'):
                if 'mail exchanger' in line.lower() or 'mx' in line.lower():
                    print(f"   ✅ {line.strip()}")
        else:
            print(f"   ❌ MX lookup failed: {result.stderr}")

    except subprocess.TimeoutExpired:
        print("   ⏱️ MX lookup timed out")
    except FileNotFoundError:
        print("   ❌ nslookup command not available")
    except Exception as e:
        print(f"   ❌ MX lookup error: {e}")

def generate_config_suggestions(imap_config, smtp_config):
    """Generate configuration suggestions based on test results"""
    print("\n🔧 CONFIGURATION SUGGESTIONS")
    print("="*50)

    if imap_config:
        print("✅ IMAP Configuration:")
        print(f"   Server: {imap_config['server']}")
        print(f"   Port: {imap_config['port']}")
        print(f"   SSL: {imap_config['ssl']}")
        print(f"   Username: info@h-bu.de")
        print(f"   Password: [Your email password]")
    else:
        print("❌ No working IMAP configuration found")

    print()

    if smtp_config:
        print("✅ SMTP Configuration:")
        print(f"   Server: {smtp_config['server']}")
        print(f"   Port: {smtp_config['port']}")
        print(f"   TLS: {smtp_config.get('tls', False)}")
        print(f"   SSL: {smtp_config.get('ssl', False)}")
        print(f"   Username: info@h-bu.de")
        print(f"   Password: [Your email password]")
    else:
        print("❌ No working SMTP configuration found")

    print("\n📝 Update your config file:")
    print("   File: sim/config/company_release2.yaml")
    print()

    if imap_config and smtp_config:
        print("   email:")
        print("     servers:")
        print("       imap:")
        print(f"         server: \"{imap_config['server']}\"")
        print(f"         port: {imap_config['port']}")
        print(f"         ssl: {imap_config['ssl']}")
        print("         username: \"info@h-bu.de\"")
        print("         password: \"YOUR_PASSWORD_HERE\"")
        print("       smtp:")
        print(f"         server: \"{smtp_config['server']}\"")
        print(f"         port: {smtp_config['port']}")
        print(f"         tls: {smtp_config.get('tls', False)}")
        if smtp_config.get('ssl'):
            print(f"         ssl: {smtp_config['ssl']}")
        print("         username: \"info@h-bu.de\"")
        print("         password: \"YOUR_PASSWORD_HERE\"")

def main():
    """Main test function"""
    print("="*60)
    print("📧 EMAIL ACCESS TEST FOR info@h-bu.de")
    print("="*60)
    print("Testing email server connectivity and configuration...")
    print()

    # Test DNS resolution first
    test_dns_resolution()
    print()

    # Test MX records
    test_mx_records()
    print()

    # Test IMAP connection
    imap_config = test_imap_connection()
    print()

    # Test SMTP connection
    smtp_config = test_smtp_connection()
    print()

    # Generate configuration suggestions
    generate_config_suggestions(imap_config, smtp_config)

    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)

    if imap_config and smtp_config:
        print("🎉 SUCCESS: Found working email server configurations!")
        print("   Next step: Update the config file with your actual password")
    elif imap_config or smtp_config:
        print("⚠️  PARTIAL: Found some working configurations")
        print("   Check the suggestions above and verify your email settings")
    else:
        print("❌ FAILED: No working email server configurations found")
        print("   Possible issues:")
        print("   • Domain h-bu.de may not exist or have email services")
        print("   • Firewall or network restrictions")
        print("   • Different server names are used")
        print("   • Email is hosted by a third-party provider")

if __name__ == "__main__":
    main()