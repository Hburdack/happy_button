#!/usr/bin/env python3
"""
Demo Email Flow Web Interface
Shows real emails with animated flow processing for demo purposes
"""

from flask import Flask, render_template_string, jsonify
from flask_socketio import SocketIO, emit
import sys
from pathlib import Path
from datetime import datetime
import threading
import time
import random

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo_flow_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# HTML template with animated email flow
DEMO_FLOW_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Happy Buttons - Live Email Flow Demo</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0e1a; color: white; overflow-x: hidden; }

        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; text-align: center; }
        .header h1 { color: white; margin-bottom: 10px; }
        .live-indicator { background: #28a745; color: white; padding: 5px 15px; border-radius: 20px; display: inline-block; margin-top: 10px; }
        .live-indicator::before { content: "🔴 "; animation: blink 1s infinite; }

        .dashboard { display: flex; height: calc(100vh - 120px); }
        .flow-panel { flex: 1; background: #1a1f2e; padding: 20px; border-right: 1px solid #2d3748; }
        .email-panel { flex: 1; background: #2d3748; padding: 20px; }

        .flow-title { color: #4fc3f7; font-size: 1.5em; margin-bottom: 20px; text-align: center; }

        .flow-stages { display: flex; flex-direction: column; gap: 20px; }
        .flow-stage { background: #374151; border-radius: 10px; padding: 15px; position: relative; }
        .stage-title { color: #60a5fa; font-weight: bold; margin-bottom: 10px; }
        .stage-content { min-height: 60px; }

        .email-item {
            background: #4b5563;
            border-radius: 8px;
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid #10b981;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .email-item:hover { transform: translateX(5px); box-shadow: 0 4px 8px rgba(0,0,0,0.3); }
        .email-item.processing { border-left-color: #f59e0b; animation: pulse 2s infinite; }
        .email-item.completed { border-left-color: #10b981; }

        .email-from { font-weight: bold; color: #93c5fd; font-size: 0.9em; }
        .email-subject { color: #e5e7eb; margin: 5px 0; }
        .email-meta { color: #9ca3af; font-size: 0.8em; display: flex; justify-content: space-between; }

        .progress-bar {
            width: 100%;
            height: 4px;
            background: #374151;
            border-radius: 2px;
            margin-top: 5px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #10b981, #34d399);
            border-radius: 2px;
            transition: width 0.5s ease;
        }

        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card {
            background: #374151;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #4b5563;
        }
        .stat-number { font-size: 2em; color: #10b981; font-weight: bold; }
        .stat-label { color: #9ca3af; font-size: 0.9em; }

        .email-detail {
            background: #374151;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            border: 1px solid #4b5563;
        }
        .email-detail h3 { color: #60a5fa; margin-bottom: 15px; }
        .detail-row { margin: 8px 0; }
        .detail-label { color: #9ca3af; display: inline-block; width: 120px; }
        .detail-value { color: #e5e7eb; }

        .flow-arrow {
            position: absolute;
            right: -15px;
            top: 50%;
            transform: translateY(-50%);
            color: #10b981;
            font-size: 1.5em;
            animation: bounce 2s infinite;
        }

        @keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0.3; } }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); } 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); } }
        @keyframes bounce { 0%, 20%, 50%, 80%, 100% { transform: translateY(-50%) translateX(0); } 40% { transform: translateY(-50%) translateX(5px); } 60% { transform: translateY(-50%) translateX(3px); } }

        .demo-badge { background: #7c3aed; color: white; padding: 3px 8px; border-radius: 10px; font-size: 0.7em; }
        .real-badge { background: #059669; color: white; padding: 3px 8px; border-radius: 10px; font-size: 0.7em; }

        @media (max-width: 768px) {
            .dashboard { flex-direction: column; }
            .flow-panel, .email-panel { flex: none; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Happy Buttons - Live Email Flow Demo</h1>
        <p>Real-time email processing with animated workflow visualization</p>
        <div class="live-indicator">LIVE DEMO - Real Emails with Flow Animation</div>
    </div>

    <div class="dashboard">
        <div class="flow-panel">
            <div class="flow-title">📧 Real-Time Email Processing Flow</div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number" id="total-emails">{{ stats.total_real_emails }}</div>
                    <div class="stat-label">Real Emails</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="processed-today">{{ stats.demo_metrics.emails_processed_today }}</div>
                    <div class="stat-label">Processed Today</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="auto-rate">{{ "%.1f"|format(stats.demo_metrics.auto_response_rate) }}%</div>
                    <div class="stat-label">Auto Response</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="sla-compliance">{{ "%.1f"|format(stats.demo_metrics.sla_compliance) }}%</div>
                    <div class="stat-label">SLA Compliance</div>
                </div>
            </div>

            <div class="flow-stages">
                <div class="flow-stage">
                    <div class="stage-title">📥 Incoming Emails</div>
                    <div class="stage-content" id="incoming-stage"></div>
                    <div class="flow-arrow">→</div>
                </div>

                <div class="flow-stage">
                    <div class="stage-title">🔍 AI Processing</div>
                    <div class="stage-content" id="processing-stage"></div>
                    <div class="flow-arrow">→</div>
                </div>

                <div class="flow-stage">
                    <div class="stage-title">🤖 Agent Assignment</div>
                    <div class="stage-content" id="assignment-stage"></div>
                    <div class="flow-arrow">→</div>
                </div>

                <div class="flow-stage">
                    <div class="stage-title">📤 Response & Completion</div>
                    <div class="stage-content" id="completion-stage"></div>
                </div>
            </div>
        </div>

        <div class="email-panel">
            <div class="flow-title">📨 Enhanced Real Email Details</div>
            <div id="email-details">
                <p style="color: #9ca3af; text-align: center; padding: 20px;">
                    Click on an email in the flow to see enhanced details
                </p>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let selectedEmailId = null;

        // Handle real-time email updates
        socket.on('email_update', function(data) {
            updateFlowStages(data.emails);
            updateStats(data.stats);
        });

        // Handle email detail requests
        socket.on('email_detail', function(data) {
            showEmailDetail(data);
        });

        function updateFlowStages(emails) {
            const stages = {
                'incoming': document.getElementById('incoming-stage'),
                'processing': document.getElementById('processing-stage'),
                'assignment': document.getElementById('assignment-stage'),
                'completion': document.getElementById('completion-stage')
            };

            // Clear all stages
            Object.values(stages).forEach(stage => stage.innerHTML = '');

            // Distribute emails across stages based on their flow state
            emails.forEach(email => {
                const emailElement = createEmailElement(email);

                const flowState = email.demo_flow.current_state;
                if (['received', 'parsed'].includes(flowState)) {
                    stages.incoming.appendChild(emailElement);
                } else if (['classified', 'routed'].includes(flowState)) {
                    stages.processing.appendChild(emailElement);
                } else if (['assigned', 'processing'].includes(flowState)) {
                    stages.assignment.appendChild(emailElement);
                } else {
                    stages.completion.appendChild(emailElement);
                }
            });
        }

        function createEmailElement(email) {
            const div = document.createElement('div');
            div.className = `email-item ${email.demo_flow.current_state === 'processing' ? 'processing' : 'completed'}`;
            div.onclick = () => requestEmailDetail(email.demo_id);

            div.innerHTML = `
                <div class="email-from">${email.from}</div>
                <div class="email-subject">${email.subject.substring(0, 40)}...</div>
                <div class="email-meta">
                    <span><span class="real-badge">REAL</span> <span class="demo-badge">ENHANCED</span></span>
                    <span>${email.demo_flow.progress_percentage}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${email.demo_flow.progress_percentage}%"></div>
                </div>
            `;

            return div;
        }

        function updateStats(stats) {
            document.getElementById('total-emails').textContent = stats.total_real_emails;
            document.getElementById('processed-today').textContent = stats.demo_metrics.emails_processed_today;
            document.getElementById('auto-rate').textContent = stats.demo_metrics.auto_response_rate.toFixed(1) + '%';
            document.getElementById('sla-compliance').textContent = stats.demo_metrics.sla_compliance.toFixed(1) + '%';
        }

        function requestEmailDetail(emailId) {
            socket.emit('request_email_detail', {email_id: emailId});
        }

        function showEmailDetail(email) {
            const detailsDiv = document.getElementById('email-details');
            detailsDiv.innerHTML = `
                <div class="email-detail">
                    <h3>📧 Enhanced Email Details</h3>
                    <div class="detail-row">
                        <span class="detail-label">Demo ID:</span>
                        <span class="detail-value">${email.demo_id}</span>
                        <span class="real-badge" style="margin-left: 10px;">REAL EMAIL</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">From:</span>
                        <span class="detail-value">${email.from}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Subject:</span>
                        <span class="detail-value">${email.subject}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Type:</span>
                        <span class="detail-value">${email.type.toUpperCase()}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Flow State:</span>
                        <span class="detail-value">${email.demo_flow.current_state.toUpperCase()}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Progress:</span>
                        <span class="detail-value">${email.demo_flow.progress_percentage}%</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Agent:</span>
                        <span class="detail-value">${email.demo_agent.assigned_to}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Processing Time:</span>
                        <span class="detail-value">${email.demo_metrics.processing_time_ms}ms</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Confidence:</span>
                        <span class="detail-value">${(email.demo_metrics.confidence_score * 100).toFixed(1)}%</span>
                    </div>
                    <div style="margin-top: 15px;">
                        <span class="detail-label">Content:</span>
                        <div style="background: #2d3748; padding: 10px; border-radius: 5px; margin-top: 5px; color: #e5e7eb;">
                            ${email.content}
                        </div>
                    </div>
                </div>
            `;
        }

        // Request initial data
        socket.emit('request_update');

        // Auto-refresh every 10 seconds
        setInterval(() => {
            socket.emit('request_update');
        }, 10000);
    </script>
</body>
</html>
"""

# Store enhanced emails for demo
enhanced_emails = []
current_stats = {}

@app.route('/')
def demo_flow():
    """Demo flow dashboard"""
    try:
        from demo_email_enhancer import DemoEmailEnhancer

        enhancer = DemoEmailEnhancer()
        global enhanced_emails, current_stats
        enhanced_emails = enhancer.get_enhanced_emails_for_demo(limit=15, show_flow=True, add_demo_data=True)
        current_stats = enhancer.get_live_demo_stats()

        return render_template_string(DEMO_FLOW_TEMPLATE,
            emails=enhanced_emails,
            stats=current_stats
        )

    except Exception as e:
        return f"❌ Error: {e}"

@socketio.on('request_update')
def handle_update_request():
    """Handle real-time update requests"""
    try:
        from demo_email_enhancer import DemoEmailEnhancer

        enhancer = DemoEmailEnhancer()
        global enhanced_emails, current_stats

        # Get fresh data
        enhanced_emails = enhancer.get_enhanced_emails_for_demo(limit=15, show_flow=True, add_demo_data=True)
        current_stats = enhancer.get_live_demo_stats()

        # Emit update to client
        emit('email_update', {
            'emails': [
                {
                    'demo_id': email['demo_id'],
                    'from': email['from'],
                    'subject': email['subject'],
                    'type': email['type'],
                    'demo_flow': email['demo_flow'],
                    'demo_agent': email['demo_agent'],
                    'demo_metrics': email['demo_metrics']
                }
                for email in enhanced_emails
            ],
            'stats': current_stats
        })

    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('request_email_detail')
def handle_detail_request(data):
    """Handle email detail requests"""
    email_id = data.get('email_id')

    # Find the email
    selected_email = None
    for email in enhanced_emails:
        if email.get('demo_id') == email_id:
            selected_email = email
            break

    if selected_email:
        emit('email_detail', selected_email)
    else:
        emit('error', {'message': 'Email not found'})

def simulate_flow_updates():
    """Background thread to simulate email flow updates"""
    while True:
        time.sleep(random.randint(15, 45))  # Random interval between updates

        try:
            from demo_email_enhancer import DemoEmailEnhancer

            enhancer = DemoEmailEnhancer()
            global enhanced_emails, current_stats

            # Update some emails' flow state randomly for demo effect
            for email in enhanced_emails:
                if random.random() < 0.3:  # 30% chance to advance
                    current_state_index = email['demo_flow']['completed_steps'].index(email['demo_flow']['current_state'])
                    if current_state_index < len(email['demo_flow']['completed_steps']) - 1:
                        email['demo_flow']['current_state'] = email['demo_flow']['completed_steps'][current_state_index + 1]
                        email['demo_flow']['progress_percentage'] = min(100, email['demo_flow']['progress_percentage'] + 10)

            # Update stats
            current_stats = enhancer.get_live_demo_stats()

            # Emit updates to all connected clients
            socketio.emit('email_update', {
                'emails': [
                    {
                        'demo_id': email['demo_id'],
                        'from': email['from'],
                        'subject': email['subject'],
                        'type': email['type'],
                        'demo_flow': email['demo_flow'],
                        'demo_agent': email['demo_agent'],
                        'demo_metrics': email['demo_metrics']
                    }
                    for email in enhanced_emails
                ],
                'stats': current_stats
            })

        except Exception as e:
            print(f"Background update error: {e}")

if __name__ == '__main__':
    print("🎬 Starting Demo Email Flow Interface...")
    print("📧 Real emails with animated flow visualization")
    print("🔗 Access at: http://localhost:8082")
    print("✨ Features: Real-time flow, WebSocket updates, enhanced demo data")

    # Start background flow simulation
    flow_thread = threading.Thread(target=simulate_flow_updates)
    flow_thread.daemon = True
    flow_thread.start()

    socketio.run(app, host='0.0.0.0', port=8082, debug=False, allow_unsafe_werkzeug=True)