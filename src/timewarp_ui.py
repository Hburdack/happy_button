#!/usr/bin/env python3
"""
TimeWarp UI Integration
Flask routes and WebSocket handlers for TimeWarp controls

Provides real-time UI updates and control interfaces for the TimeWarp system
"""

from flask import jsonify, request, render_template
from flask_socketio import emit, SocketIO
import json
import logging
from datetime import datetime
from .timewarp_engine import get_timewarp

logger = logging.getLogger(__name__)

def get_timewarp_ui():
    """Get TimeWarp UI instance"""
    return _timewarp_ui_instance

def init_timewarp_ui(app, socketio):
    """Initialize TimeWarp UI with Flask app and SocketIO"""
    global _timewarp_ui_instance
    _timewarp_ui_instance = TimeWarpUI(app, socketio)
    return _timewarp_ui_instance

# Global instance
_timewarp_ui_instance = None

class TimeWarpUI:
    """TimeWarp UI Integration Manager"""

    def __init__(self, app=None, socketio=None):
        self.app = app
        self.socketio = socketio
        self.timewarp = get_timewarp()
        self.connected_clients = set()

        if app and socketio:
            self.init_app(app, socketio)

    def init_app(self, app, socketio):
        """Initialize TimeWarp UI with Flask app and SocketIO"""
        self.app = app
        self.socketio = socketio

        # Register TimeWarp UI callback
        self.timewarp.add_ui_callback(self._handle_timewarp_event)

        # Register Flask routes
        self._register_routes()

        # Register SocketIO events
        self._register_socketio_events()

        logger.info("TimeWarp UI initialized")

    def _register_routes(self):
        """Register Flask routes for TimeWarp API"""

        @self.app.route('/api/timewarp/status')
        def timewarp_status():
            """Get current TimeWarp status"""
            try:
                status = self.timewarp.get_time_status()
                speed_levels = self.timewarp.get_all_speed_levels()

                return jsonify({
                    "success": True,
                    "status": status,
                    "speed_levels": speed_levels
                })
            except Exception as e:
                logger.error(f"Error getting TimeWarp status: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/timewarp/set-speed', methods=['POST'])
        def set_timewarp_speed():
            """Set TimeWarp speed level"""
            try:
                data = request.get_json()
                level = data.get('level')

                if not level or level not in range(1, 6):
                    return jsonify({
                        "success": False,
                        "error": "Invalid speed level. Must be 1-5."
                    }), 400

                old_level = self.timewarp.current_level
                self.timewarp.set_speed(level)

                return jsonify({
                    "success": True,
                    "message": f"Speed changed from level {old_level} to {level}",
                    "status": self.timewarp.get_time_status()
                })

            except Exception as e:
                logger.error(f"Error setting TimeWarp speed: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/timewarp/pause', methods=['POST'])
        def pause_timewarp():
            """Pause TimeWarp simulation"""
            try:
                self.timewarp.pause()
                return jsonify({
                    "success": True,
                    "message": "TimeWarp paused",
                    "status": self.timewarp.get_time_status()
                })
            except Exception as e:
                logger.error(f"Error pausing TimeWarp: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/timewarp/resume', methods=['POST'])
        def resume_timewarp():
            """Resume TimeWarp simulation"""
            try:
                self.timewarp.resume()
                return jsonify({
                    "success": True,
                    "message": "TimeWarp resumed",
                    "status": self.timewarp.get_time_status()
                })
            except Exception as e:
                logger.error(f"Error resuming TimeWarp: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/timewarp/reset', methods=['POST'])
        def reset_timewarp():
            """Reset TimeWarp simulation"""
            try:
                self.timewarp.reset()
                return jsonify({
                    "success": True,
                    "message": "TimeWarp reset",
                    "status": self.timewarp.get_time_status()
                })
            except Exception as e:
                logger.error(f"Error resetting TimeWarp: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

        @self.app.route('/api/timewarp/start', methods=['POST'])
        def start_timewarp():
            """Start TimeWarp engine"""
            try:
                self.timewarp.start()
                return jsonify({
                    "success": True,
                    "message": "TimeWarp started",
                    "status": self.timewarp.get_time_status()
                })
            except Exception as e:
                logger.error(f"Error starting TimeWarp: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

    def _register_socketio_events(self):
        """Register SocketIO events for real-time TimeWarp updates"""

        @self.socketio.on('timewarp_connect')
        def handle_timewarp_connect():
            """Client connected to TimeWarp updates"""
            self.connected_clients.add(request.sid)

            # Send current status
            status = self.timewarp.get_time_status()
            speed_levels = self.timewarp.get_all_speed_levels()

            emit('timewarp_status', {
                "status": status,
                "speed_levels": speed_levels
            })

            logger.info(f"Client {request.sid} connected to TimeWarp updates")

        @self.socketio.on('timewarp_disconnect')
        def handle_timewarp_disconnect():
            """Client disconnected from TimeWarp updates"""
            self.connected_clients.discard(request.sid)
            logger.info(f"Client {request.sid} disconnected from TimeWarp updates")

        @self.socketio.on('timewarp_set_speed')
        def handle_set_speed(data):
            """Handle speed change request via SocketIO"""
            try:
                level = data.get('level')
                if level and level in range(1, 6):
                    self.timewarp.set_speed(level)
                    emit('timewarp_speed_changed', {
                        "level": level,
                        "status": self.timewarp.get_time_status()
                    })
                else:
                    emit('timewarp_error', {
                        "error": "Invalid speed level"
                    })
            except Exception as e:
                logger.error(f"Error handling speed change: {e}")
                emit('timewarp_error', {"error": str(e)})

    def _handle_timewarp_event(self, event_type: str, data: dict):
        """Handle TimeWarp events and broadcast to connected clients"""
        if not self.socketio:
            return

        try:
            # Broadcast to all connected clients
            self.socketio.emit('timewarp_event', {
                "type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            })

            # Special handling for specific events
            if event_type == "time_update":
                self.socketio.emit('timewarp_time_update', data)
            elif event_type == "speed_changed":
                self.socketio.emit('timewarp_speed_changed', data)
            elif event_type in ["paused", "resumed", "reset", "started", "stopped"]:
                self.socketio.emit('timewarp_state_changed', {
                    "state": event_type,
                    "data": data
                })

        except Exception as e:
            logger.error(f"Error broadcasting TimeWarp event: {e}")

    def get_timewarp_widget_html(self) -> str:
        """Generate HTML for TimeWarp control widget"""
        speed_levels = self.timewarp.get_all_speed_levels()
        current_status = self.timewarp.get_time_status()

        html = f'''
        <div id="timewarp-widget" class="timewarp-control-widget">
            <div class="timewarp-header">
                <i class="fas fa-clock text-primary"></i>
                <span class="fw-bold">TimeWarp Control</span>
                <button class="btn btn-sm btn-outline-secondary" id="timewarp-fullscreen">
                    <i class="fas fa-expand"></i>
                </button>
            </div>

            <div class="time-displays">
                <div class="time-display real-time">
                    <label>Real Time</label>
                    <span id="real-time-display">{datetime.now().strftime("%H:%M:%S")}</span>
                </div>
                <div class="time-display sim-time">
                    <label>Simulation Time</label>
                    <span id="sim-time-display">{current_status.get("day_of_week", "Monday")} {current_status.get("simulation_time", "")[:16].replace("T", " ")}</span>
                </div>
            </div>

            <div class="speed-controls">
        '''

        for level, config in speed_levels.items():
            active_class = "active" if level == current_status.get("speed_level", 1) else ""
            html += f'''
                <button class="speed-btn {active_class}" data-level="{level}"
                        style="border-color: {config['color']}; color: {config['color']};"
                        title="{config['description']}">
                    <i class="fas {config['icon']}"></i>
                    <span class="speed-label">{config['multiplier']}x</span>
                </button>
            '''

        html += f'''
            </div>

            <div class="control-buttons">
                <button class="btn btn-sm btn-success" id="timewarp-play"
                        {'disabled' if current_status.get("is_running") else ''}>
                    <i class="fas fa-play"></i> Start
                </button>
                <button class="btn btn-sm btn-warning" id="timewarp-pause"
                        {'disabled' if not current_status.get("is_running") else ''}>
                    <i class="fas fa-pause"></i> Pause
                </button>
                <button class="btn btn-sm btn-info" id="timewarp-reset">
                    <i class="fas fa-redo"></i> Reset
                </button>
            </div>

            <div class="progress-section">
                <div class="progress-labels">
                    <span>Week Progress</span>
                    <span id="week-day">{current_status.get("day_of_week", "Monday")}</span>
                </div>
                <div class="progress" style="height: 8px;">
                    <div class="progress-bar bg-primary" id="week-progress-bar"
                         style="width: {current_status.get('week_progress', 0):.1f}%"></div>
                </div>
                <div class="progress-text">
                    <small class="text-muted" id="progress-text">
                        Day {current_status.get("day_number", 1)} of 7
                    </small>
                </div>
            </div>

            <div class="status-section">
                <div class="status-indicator">
                    <span class="status-dot {'running' if current_status.get('is_running') else 'stopped'}"></span>
                    <span id="status-text">{'Running' if current_status.get('is_running') else 'Stopped'}</span>
                </div>
            </div>
        </div>
        '''

        return html

    def get_timewarp_css(self) -> str:
        """Generate CSS for TimeWarp UI components"""
        return '''
        <style>
        .timewarp-control-widget {
            background: white;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            margin-bottom: 20px;
            min-width: 300px;
        }

        .timewarp-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e9ecef;
        }

        .time-displays {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 16px;
        }

        .time-display {
            text-align: center;
            padding: 8px;
            background: #f8f9fa;
            border-radius: 6px;
        }

        .time-display label {
            display: block;
            font-size: 0.75rem;
            color: #6c757d;
            margin-bottom: 4px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .time-display span {
            display: block;
            font-family: 'Courier New', monospace;
            font-weight: bold;
            font-size: 0.9rem;
            color: #2c3e50;
        }

        .speed-controls {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 4px;
            margin-bottom: 16px;
        }

        .speed-btn {
            padding: 8px 4px;
            border: 2px solid #ddd;
            background: white;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 2px;
        }

        .speed-btn:hover {
            background: #f8f9fa;
            transform: translateY(-1px);
        }

        .speed-btn.active {
            background: linear-gradient(135deg, var(--bs-primary) 0%, var(--bs-secondary) 100%);
            color: white !important;
            border-color: var(--bs-primary) !important;
            box-shadow: 0 2px 8px rgba(0,123,255,0.3);
        }

        .speed-btn i {
            font-size: 1.2rem;
        }

        .speed-label {
            font-size: 0.7rem;
            font-weight: bold;
        }

        .control-buttons {
            display: flex;
            gap: 6px;
            margin-bottom: 16px;
        }

        .control-buttons .btn {
            flex: 1;
        }

        .progress-section {
            margin-bottom: 16px;
        }

        .progress-labels {
            display: flex;
            justify-content: space-between;
            font-size: 0.85rem;
            margin-bottom: 6px;
        }

        .progress-text {
            margin-top: 4px;
            text-align: center;
        }

        .status-section {
            text-align: center;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            font-size: 0.9rem;
        }

        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #dc3545;
            animation: pulse 2s infinite;
        }

        .status-dot.running {
            background: #28a745;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        /* Mobile responsive */
        @media (max-width: 768px) {
            .timewarp-control-widget {
                margin: 10px;
            }

            .time-displays {
                grid-template-columns: 1fr;
            }

            .speed-controls {
                grid-template-columns: repeat(5, 1fr);
                gap: 2px;
            }

            .speed-btn {
                padding: 6px 2px;
            }

            .speed-btn i {
                font-size: 1rem;
            }

            .speed-label {
                font-size: 0.6rem;
            }
        }
        </style>
        '''

    def get_timewarp_js(self) -> str:
        """Generate JavaScript for TimeWarp UI functionality"""
        return '''
        <script>
        class TimeWarpUI {
            constructor() {
                this.socket = io();
                this.isConnected = false;
                this.init();
            }

            init() {
                this.connectSocket();
                this.setupEventListeners();
                this.startUIUpdates();
            }

            connectSocket() {
                this.socket.emit('timewarp_connect');

                this.socket.on('timewarp_status', (data) => {
                    this.updateUI(data.status);
                    this.isConnected = true;
                });

                this.socket.on('timewarp_time_update', (data) => {
                    this.updateTimeDisplays(data);
                });

                this.socket.on('timewarp_speed_changed', (data) => {
                    this.updateSpeedDisplay(data);
                });

                this.socket.on('timewarp_state_changed', (data) => {
                    this.updateStateDisplay(data);
                });

                this.socket.on('timewarp_error', (data) => {
                    this.showError(data.error);
                });
            }

            setupEventListeners() {
                // Speed control buttons
                document.querySelectorAll('.speed-btn').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        const level = parseInt(e.currentTarget.dataset.level);
                        this.setSpeed(level);
                    });
                });

                // Control buttons
                document.getElementById('timewarp-play')?.addEventListener('click', () => {
                    this.startTimeWarp();
                });

                document.getElementById('timewarp-pause')?.addEventListener('click', () => {
                    this.pauseTimeWarp();
                });

                document.getElementById('timewarp-reset')?.addEventListener('click', () => {
                    this.resetTimeWarp();
                });

                // Fullscreen toggle
                document.getElementById('timewarp-fullscreen')?.addEventListener('click', () => {
                    this.toggleFullscreen();
                });
            }

            setSpeed(level) {
                fetch('/api/timewarp/set-speed', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ level: level })
                })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        this.showError(data.error);
                    }
                })
                .catch(error => {
                    this.showError('Network error: ' + error.message);
                });
            }

            startTimeWarp() {
                fetch('/api/timewarp/start', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        this.showError(data.error);
                    }
                });
            }

            pauseTimeWarp() {
                fetch('/api/timewarp/pause', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        this.showError(data.error);
                    }
                });
            }

            resetTimeWarp() {
                if (confirm('Reset TimeWarp simulation? This will restart the week cycle.')) {
                    fetch('/api/timewarp/reset', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (!data.success) {
                            this.showError(data.error);
                        }
                    });
                }
            }

            updateTimeDisplays(data) {
                // Update real time
                const realTime = new Date().toLocaleTimeString();
                const realTimeElement = document.getElementById('real-time-display');
                if (realTimeElement) {
                    realTimeElement.textContent = realTime;
                }

                // Update simulation time
                const simTime = new Date(data.simulation_time);
                const simTimeElement = document.getElementById('sim-time-display');
                if (simTimeElement) {
                    simTimeElement.textContent = data.day_of_week + ' ' + simTime.toLocaleString().substring(0, 16);
                }

                // Update progress
                const progressBar = document.getElementById('week-progress-bar');
                if (progressBar) {
                    progressBar.style.width = data.week_progress + '%';
                }

                const weekDay = document.getElementById('week-day');
                if (weekDay) {
                    weekDay.textContent = data.day_of_week;
                }

                const progressText = document.getElementById('progress-text');
                if (progressText) {
                    progressText.textContent = `Day ${data.day_number} of 7`;
                }
            }

            updateSpeedDisplay(data) {
                // Update active speed button
                document.querySelectorAll('.speed-btn').forEach(btn => {
                    btn.classList.remove('active');
                });

                const activeBtn = document.querySelector(`[data-level="${data.new_level}"]`);
                if (activeBtn) {
                    activeBtn.classList.add('active');
                }

                this.showMessage(`Speed changed to ${data.name || 'Level ' + data.new_level}`);
            }

            updateStateDisplay(data) {
                const statusDot = document.querySelector('.status-dot');
                const statusText = document.getElementById('status-text');
                const playBtn = document.getElementById('timewarp-play');
                const pauseBtn = document.getElementById('timewarp-pause');

                switch(data.state) {
                    case 'started':
                        if (statusDot) statusDot.className = 'status-dot running';
                        if (statusText) statusText.textContent = 'Running';
                        if (playBtn) playBtn.disabled = true;
                        if (pauseBtn) pauseBtn.disabled = false;
                        break;
                    case 'paused':
                        if (statusDot) statusDot.className = 'status-dot paused';
                        if (statusText) statusText.textContent = 'Paused';
                        break;
                    case 'stopped':
                        if (statusDot) statusDot.className = 'status-dot stopped';
                        if (statusText) statusText.textContent = 'Stopped';
                        if (playBtn) playBtn.disabled = false;
                        if (pauseBtn) pauseBtn.disabled = true;
                        break;
                    case 'reset':
                        this.showMessage('TimeWarp simulation reset');
                        break;
                }
            }

            updateUI(status) {
                this.updateTimeDisplays(status);
                this.updateSpeedDisplay({ new_level: status.speed_level });
                this.updateStateDisplay({ state: status.is_running ? 'started' : 'stopped' });
            }

            startUIUpdates() {
                // Update real time display every second
                setInterval(() => {
                    const realTimeElement = document.getElementById('real-time-display');
                    if (realTimeElement) {
                        realTimeElement.textContent = new Date().toLocaleTimeString();
                    }
                }, 1000);
            }

            showMessage(message) {
                // Simple toast notification
                const toast = document.createElement('div');
                toast.className = 'alert alert-info alert-dismissible fade show position-fixed';
                toast.style.top = '20px';
                toast.style.right = '20px';
                toast.style.zIndex = '9999';
                toast.innerHTML = `
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                document.body.appendChild(toast);

                setTimeout(() => {
                    toast.remove();
                }, 3000);
            }

            showError(error) {
                console.error('TimeWarp Error:', error);
                this.showMessage('Error: ' + error);
            }

            toggleFullscreen() {
                // Implement fullscreen TimeWarp dashboard
                console.log('Fullscreen TimeWarp not implemented yet');
            }
        }

        // Initialize TimeWarp UI when DOM is ready
        document.addEventListener('DOMContentLoaded', function() {
            if (document.getElementById('timewarp-widget')) {
                window.timeWarpUI = new TimeWarpUI();
            }
        });
        </script>
        '''


# Global TimeWarp UI instance
timewarp_ui = TimeWarpUI()

def get_timewarp_ui() -> TimeWarpUI:
    """Get the global TimeWarp UI instance"""
    return timewarp_ui