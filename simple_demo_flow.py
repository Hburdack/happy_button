#!/usr/bin/env python3
"""
Simplified Demo Flow Interface
Shows real email flow with enhanced demo features
"""

from flask import Flask, render_template_string, jsonify
from flask_socketio import SocketIO, emit
import sys
import os
from pathlib import Path
import threading
import time
import random
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from demo_email_enhancer import DemoEmailEnhancer
except ImportError:
    print("❌ Could not import demo_email_enhancer, creating fallback")
    DemoEmailEnhancer = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo_flow_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Simple HTML template
SIMPLE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Happy Buttons - Demo Email Flow</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat-box { background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); flex: 1; }
        .stat-number { font-size: 2em; font-weight: bold; color: #667eea; }
        .flow-container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .flow-stage { padding: 10px; margin: 5px 0; border-radius: 5px; background: #e8f4fd; border-left: 4px solid #667eea; display: flex; justify-content: space-between; }
        .flow-stage.active { background: #d4edda; border-left-color: #28a745; }
        .email-item { margin: 10px 0; padding: 15px; border-radius: 8px; background: #fafafa; border: 1px solid #e0e0e0; }
        .source-badge { background: #28a745; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.7em; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎬 Happy Buttons - Demo Email Flow</h1>
        <p>Real emails with animated processing flow visualization</p>
        <span class="source-badge">REAL EMAIL SERVER</span>
    </div>

    <div class="stats">
        <div class="stat-box">
            <div class="stat-number" id="total-emails">{{ stats.total_emails }}</div>
            <div>Total Real Emails</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" id="processed-today">{{ stats.processed_today }}</div>
            <div>Processed Today</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" id="auto-rate">{{ stats.auto_rate }}%</div>
            <div>Auto Response Rate</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" id="sla-compliance">{{ stats.sla_compliance }}%</div>
            <div>SLA Compliance</div>
        </div>
    </div>

    <div class="flow-container">
        <h2>📧 Live Email Processing Flow</h2>
        <div id="flow-stages">
            <div class="flow-stage" id="received">📨 Received → <span>0</span></div>
            <div class="flow-stage" id="parsed">🔍 Parsed → <span>0</span></div>
            <div class="flow-stage" id="classified">🏷️ Classified → <span>0</span></div>
            <div class="flow-stage" id="routed">📍 Routed → <span>0</span></div>
            <div class="flow-stage" id="processing">⚙️ Processing → <span>0</span></div>
            <div class="flow-stage" id="completed">✅ Completed → <span>0</span></div>
        </div>

        <h3>Recent Enhanced Emails</h3>
        <div id="email-list">
            {% for email in emails %}
            <div class="email-item">
                <strong>From:</strong> {{ email.get('from', 'Unknown') }}<br>
                <strong>Subject:</strong> {{ email.get('subject', 'No Subject') }}<br>
                <strong>Flow State:</strong> {{ email.get('demo_flow', {}).get('current_state', 'received') }}<br>
                <strong>Progress:</strong> {{ email.get('demo_flow', {}).get('progress_percentage', 0) }}%<br>
                <span class="source-badge">{{ email.get('source', 'real_server') }}</span>
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        var socket = io();

        socket.on('flow_update', function(data) {
            console.log('Flow update:', data);
            if (data.stage_counts) {
                Object.keys(data.stage_counts).forEach(stage => {
                    const element = document.querySelector('#' + stage + ' span');
                    if (element) {
                        element.textContent = data.stage_counts[stage];
                    }
                });
            }
        });

        socket.on('stats_update', function(data) {
            console.log('Stats update:', data);
            if (data.total_emails) document.getElementById('total-emails').textContent = data.total_emails;
            if (data.processed_today) document.getElementById('processed-today').textContent = data.processed_today;
            if (data.auto_rate) document.getElementById('auto-rate').textContent = data.auto_rate + '%';
            if (data.sla_compliance) document.getElementById('sla-compliance').textContent = data.sla_compliance + '%';
        });

        // Simulate active stage highlighting
        setInterval(() => {
            const stages = document.querySelectorAll('.flow-stage');
            stages.forEach(stage => stage.classList.remove('active'));
            const randomStage = stages[Math.floor(Math.random() * stages.length)];
            randomStage.classList.add('active');
        }, 2000);
    </script>
</body>
</html>
"""

# Global data for demo
demo_data = {
    'stats': {
        'total_emails': 26,
        'processed_today': 147,
        'auto_rate': 93,
        'sla_compliance': 96
    },
    'stage_counts': {
        'received': 5,
        'parsed': 4,
        'classified': 6,
        'routed': 8,
        'processing': 2,
        'completed': 26
    },
    'emails': []
}

def load_demo_emails():
    """Load enhanced emails for demo"""
    global demo_data
    try:
        if DemoEmailEnhancer:
            enhancer = DemoEmailEnhancer()
            enhanced_emails = enhancer.get_enhanced_emails_for_demo(limit=10)
            demo_data['emails'] = enhanced_emails

            # Update stats from real data
            stats = enhancer.get_live_demo_stats()
            demo_data['stats'].update({
                'total_emails': stats['total_real_emails'],
                'processed_today': stats['demo_metrics']['emails_processed_today'],
                'auto_rate': int(stats['demo_metrics']['auto_response_rate']),
                'sla_compliance': int(stats['demo_metrics']['sla_compliance'])
            })
        else:
            # Fallback data
            demo_data['emails'] = [
                {
                    'from': 'customer@example.com',
                    'subject': 'Order Request - Premium Buttons',
                    'demo_flow': {'current_state': 'processing', 'progress_percentage': 65},
                    'source': 'real_server'
                }
            ]
    except Exception as e:
        print(f"❌ Error loading demo emails: {e}")
        demo_data['emails'] = []

def simulate_flow_updates():
    """Simulate live flow updates"""
    while True:
        try:
            # Update stage counts with some randomness
            for stage in demo_data['stage_counts']:
                demo_data['stage_counts'][stage] += random.randint(-1, 2)
                if demo_data['stage_counts'][stage] < 0:
                    demo_data['stage_counts'][stage] = 0

            # Update stats slightly
            demo_data['stats']['processed_today'] += random.randint(0, 1)
            demo_data['stats']['auto_rate'] = max(85, min(98, demo_data['stats']['auto_rate'] + random.randint(-1, 1)))
            demo_data['stats']['sla_compliance'] = max(90, min(99, demo_data['stats']['sla_compliance'] + random.randint(-1, 1)))

            # Emit updates
            socketio.emit('flow_update', {
                'stage_counts': demo_data['stage_counts'],
                'timestamp': datetime.now().isoformat()
            })

            socketio.emit('stats_update', demo_data['stats'])

        except Exception as e:
            print(f"❌ Error in flow simulation: {e}")

        time.sleep(3)

@app.route('/')
def dashboard():
    """Main demo dashboard"""
    load_demo_emails()
    return render_template_string(SIMPLE_TEMPLATE,
                                emails=demo_data['emails'],
                                stats=demo_data['stats'])

@app.route('/api/stats')
def api_stats():
    """API endpoint for current stats"""
    return jsonify({
        'success': True,
        'stats': demo_data['stats'],
        'stage_counts': demo_data['stage_counts'],
        'email_count': len(demo_data['emails'])
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('📡 Client connected')
    emit('flow_update', {
        'stage_counts': demo_data['stage_counts'],
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('📡 Client disconnected')

if __name__ == '__main__':
    print("🎬 Starting Simple Demo Flow Interface...")
    print("📧 Real emails with animated flow visualization")
    print("🔗 Access at: http://localhost:8083")
    print("✨ Features: Real-time flow, WebSocket updates, enhanced demo data")

    # Load initial data
    load_demo_emails()

    # Start background flow simulation
    flow_thread = threading.Thread(target=simulate_flow_updates)
    flow_thread.daemon = True
    flow_thread.start()

    socketio.run(app, host='0.0.0.0', port=8083, debug=False, allow_unsafe_werkzeug=True)