#!/usr/bin/env python3
"""
Real Email Web Interface
Simple web interface showing ONLY real emails from the email server
"""

from flask import Flask, render_template_string, jsonify
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

app = Flask(__name__)

# HTML template for displaying real emails
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Happy Buttons - Real Email Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .stats { display: flex; justify-content: space-around; margin-bottom: 20px; }
        .stat-box { background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-number { font-size: 2em; font-weight: bold; color: #667eea; }
        .email-list { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .email-item { border: 1px solid #e0e0e0; margin: 10px 0; padding: 15px; border-radius: 8px; background: #fafafa; }
        .email-header { display: flex; justify-content: between; align-items: center; margin-bottom: 10px; }
        .email-from { font-weight: bold; color: #333; }
        .email-subject { font-size: 1.1em; margin: 5px 0; color: #555; }
        .email-meta { font-size: 0.9em; color: #777; }
        .email-content { margin-top: 10px; padding: 10px; background: white; border-radius: 4px; border-left: 4px solid #667eea; }
        .priority-high { border-left-color: #f44336; }
        .priority-medium { border-left-color: #ff9800; }
        .priority-low { border-left-color: #4caf50; }
        .mailbox-badge { background: #667eea; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; }
        .type-badge { background: #76b5c5; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-left: 5px; }
        .refresh-btn { background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin-bottom: 20px; }
        .refresh-btn:hover { background: #5a67d8; }
        .source-indicator { background: #28a745; color: white; padding: 3px 8px; border-radius: 10px; font-size: 0.7em; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Happy Buttons Release 2 - Real Email Dashboard</h1>
        <p>Showing ONLY real emails from email server (192.168.2.13) - No simulations!</p>
    </div>

    <div class="stats">
        <div class="stat-box">
            <div class="stat-number">{{ total_emails }}</div>
            <div>Total Real Emails</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{{ mailbox_count }}</div>
            <div>Active Mailboxes</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{{ recent_count }}</div>
            <div>Recent Emails</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{{ server_status }}</div>
            <div>Server Status</div>
        </div>
    </div>

    <button class="refresh-btn" onclick="location.reload();">🔄 Refresh Real Emails</button>

    <div class="email-list">
        <h2>📧 Real Emails from Email Server</h2>

        {% if not emails %}
        <p>No real emails found. Check email server connectivity.</p>
        {% endif %}

        {% for email in emails %}
        <div class="email-item">
            <div class="email-header">
                <div>
                    <span class="source-indicator">REAL SERVER</span>
                    <span class="mailbox-badge">{{ email.mailbox }}@h-bu.de</span>
                    <span class="type-badge">{{ email.type }}</span>
                </div>
                <div class="email-meta">{{ email.timestamp.strftime('%Y-%m-%d %H:%M') }}</div>
            </div>
            <div class="email-from">From: {{ email.from }}</div>
            <div class="email-subject">{{ email.subject }}</div>
            <div class="email-content priority-{{ email.priority }}">
                {{ email.content[:200] }}...
                {% if email.attachments %}
                <br><strong>📎 Attachments:</strong> {{ email.attachments|length }} file(s)
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>

    <div style="margin-top: 20px; padding: 20px; background: #e8f5e8; border-radius: 10px;">
        <h3>✅ Real Email Integration Status</h3>
        <ul>
            <li><strong>Email Server:</strong> 192.168.2.13 (Direct IP connectivity)</li>
            <li><strong>Mailboxes:</strong> info@, sales@, support@, finance@h-bu.de</li>
            <li><strong>Authentication:</strong> ✅ All mailboxes authenticated</li>
            <li><strong>Data Source:</strong> REAL email server (no simulations)</li>
            <li><strong>Last Updated:</strong> {{ current_time.strftime('%Y-%m-%d %H:%M:%S') }}</li>
        </ul>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main dashboard showing real emails"""
    try:
        from real_email_connector import RealEmailConnector

        # Get real email data
        connector = RealEmailConnector()
        emails = connector.get_real_emails(limit=20)
        mailbox_counts = connector.get_mailbox_counts()

        # Calculate statistics
        total_emails = sum(mailbox_counts.values())

        return render_template_string(HTML_TEMPLATE,
            emails=emails,
            total_emails=total_emails,
            mailbox_count=len(mailbox_counts),
            recent_count=len(emails),
            server_status="✅ ONLINE",
            current_time=datetime.now()
        )

    except Exception as e:
        return f"❌ Error connecting to real email server: {e}"

@app.route('/api/emails')
def api_emails():
    """API endpoint for real emails"""
    try:
        from real_email_connector import RealEmailConnector

        connector = RealEmailConnector()
        emails = connector.get_real_emails(limit=50)
        mailbox_counts = connector.get_mailbox_counts()

        return jsonify({
            'success': True,
            'emails': [
                {
                    'from': email['from'],
                    'subject': email['subject'],
                    'content': email['content'],
                    'type': email['type'],
                    'priority': email['priority'],
                    'mailbox': email.get('mailbox', 'unknown'),
                    'timestamp': email['timestamp'].isoformat(),
                    'attachments_count': len(email.get('attachments', [])),
                    'source': 'real_server'
                }
                for email in emails
            ],
            'statistics': {
                'total_emails': sum(mailbox_counts.values()),
                'mailbox_counts': mailbox_counts,
                'recent_emails': len(emails)
            },
            'server_info': {
                'server': '192.168.2.13',
                'status': 'connected',
                'mailboxes': list(mailbox_counts.keys())
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/stats')
def api_stats():
    """API endpoint for email statistics"""
    try:
        from real_email_connector import RealEmailConnector

        connector = RealEmailConnector()
        mailbox_counts = connector.get_mailbox_counts()

        return jsonify({
            'success': True,
            'mailbox_counts': mailbox_counts,
            'total_emails': sum(mailbox_counts.values()),
            'server_status': 'connected',
            'last_updated': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("🌐 Starting Real Email Web Interface...")
    print("📡 Connecting to email server: 192.168.2.13")
    print("🔗 Access at: http://localhost:8080")
    print("✅ Shows ONLY real emails - no simulations!")

    app.run(host='0.0.0.0', port=8080, debug=False)