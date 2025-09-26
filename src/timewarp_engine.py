#!/usr/bin/env python3
"""
TimeWarp Engine - Core System for Time Acceleration
Happy Buttons Release 2.1 - Business Simulation TimeWarp Feature

Allows acceleration of business simulation from real-time to 1008x speed
(1 full week compressed into 10 minutes at maximum speed)
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, List
import json
import logging

logger = logging.getLogger(__name__)

class TimeWarpEngine:
    """Core TimeWarp system for accelerating business simulation"""

    # TimeWarp Speed Levels
    SPEED_LEVELS = {
        1: {
            "name": "Real Time",
            "multiplier": 1,
            "description": "Normal business speed",
            "icon": "fa-play",
            "color": "#28a745",
            "email_interval": 300  # 5 minutes between emails
        },
        2: {
            "name": "Fast Forward",
            "multiplier": 60,
            "description": "1 hour per minute",
            "icon": "fa-fast-forward",
            "color": "#ffc107",
            "email_interval": 5  # 5 seconds between emails
        },
        3: {
            "name": "Rapid Pace",
            "multiplier": 168,
            "description": "1 work day per minute",
            "icon": "fa-forward",
            "color": "#fd7e14",
            "email_interval": 2  # 2 seconds between emails
        },
        4: {
            "name": "Ultra Speed",
            "multiplier": 504,
            "description": "3 days per minute",
            "icon": "fa-rocket",
            "color": "#e83e8c",
            "email_interval": 0.6  # 600ms between emails
        },
        5: {
            "name": "Time Warp",
            "multiplier": 1008,
            "description": "1 week per 10 minutes",
            "icon": "fa-magic",
            "color": "#6f42c1",
            "email_interval": 0.3  # 300ms between emails
        }
    }

    def __init__(self):
        """Initialize TimeWarp Engine"""
        self.current_level = 1
        self.is_running = False
        self.is_paused = False

        # Time tracking
        self.real_start_time = time.time()
        self.simulation_start_time = datetime.now()
        self.pause_duration = 0
        self.pause_start = None

        # Weekly cycle tracking
        self.week_cycle_count = 0
        self.current_week_start = self.simulation_start_time
        self.emails_generated_this_week = 0
        self.weekly_restart_enabled = True

        # Event scheduling
        self.scheduled_events = []
        self.event_callbacks = {}

        # System integration
        self.email_generator = None
        self.agent_system = None
        self.ui_callbacks = []

        # Threading
        self.timer_thread = None
        self.running = True

        # Weekly email patterns for realistic business simulation
        self.weekly_patterns = {
            'monday': {
                'morning': {'customer_inquiry': 5, 'internal_coordination': 3},
                'afternoon': {'supplier_update': 2, 'logistics_coordination': 3}
            },
            'tuesday': {
                'morning': {'customer_inquiry': 4, 'oem_order': 3},
                'afternoon': {'quality_review': 2, 'production_planning': 2}
            },
            'wednesday': {
                'morning': {'supplier_coordination': 3, 'internal_status': 2},
                'afternoon': {'quality_complaint': 1, 'customer_follow_up': 2}
            },
            'thursday': {
                'morning': {'logistics_update': 2, 'oem_order': 2},
                'afternoon': {'management_report': 1, 'customer_inquiry': 3}
            },
            'friday': {
                'morning': {'week_summary': 2, 'quality_complaint': 2},
                'afternoon': {'logistics_planning': 2, 'internal_planning': 3}
            }
        }

        logger.info("TimeWarp Engine initialized")

    def start(self):
        """Start the TimeWarp engine"""
        if not self.is_running:
            self.is_running = True
            self.real_start_time = time.time()
            self.simulation_start_time = datetime.now()

            # Start the main timer thread
            self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
            self.timer_thread.start()

            logger.info(f"TimeWarp Engine started at level {self.current_level}")
            self._notify_ui_callbacks("started", {"level": self.current_level})

    def stop(self):
        """Stop the TimeWarp engine"""
        self.is_running = False
        self.running = False
        logger.info("TimeWarp Engine stopped")
        self._notify_ui_callbacks("stopped", {})

    def set_speed(self, level: int):
        """Set TimeWarp speed level (1-5)"""
        if level not in self.SPEED_LEVELS:
            raise ValueError(f"Invalid speed level: {level}. Must be 1-5.")

        old_level = self.current_level
        self.current_level = level

        logger.info(f"TimeWarp speed changed: Level {old_level} -> Level {level}")
        logger.info(f"New speed: {self.SPEED_LEVELS[level]['name']} ({self.SPEED_LEVELS[level]['multiplier']}x)")

        # Update all integrated systems
        self._update_system_speeds()

        # Notify UI
        self._notify_ui_callbacks("speed_changed", {
            "old_level": old_level,
            "new_level": level,
            "multiplier": self.SPEED_LEVELS[level]["multiplier"],
            "name": self.SPEED_LEVELS[level]["name"]
        })

    def pause(self):
        """Pause the TimeWarp simulation"""
        if not self.is_paused:
            self.is_paused = True
            self.pause_start = time.time()
            logger.info("TimeWarp simulation paused")
            self._notify_ui_callbacks("paused", {})

    def resume(self):
        """Resume the TimeWarp simulation"""
        if self.is_paused:
            self.is_paused = False
            if self.pause_start:
                self.pause_duration += time.time() - self.pause_start
                self.pause_start = None
            logger.info("TimeWarp simulation resumed")
            self._notify_ui_callbacks("resumed", {})

    def reset(self):
        """Reset the TimeWarp simulation to start"""
        self.real_start_time = time.time()
        self.simulation_start_time = datetime.now()
        self.pause_duration = 0
        self.pause_start = None
        self.scheduled_events.clear()

        logger.info("TimeWarp simulation reset")
        self._notify_ui_callbacks("reset", {})

    def get_current_simulation_time(self) -> datetime:
        """Get current simulated time based on acceleration"""
        if self.is_paused:
            # Return time at pause moment
            if self.pause_start:
                real_elapsed = self.pause_start - self.real_start_time - self.pause_duration
            else:
                real_elapsed = 0
        else:
            real_elapsed = time.time() - self.real_start_time - self.pause_duration

        # Apply time multiplier
        multiplier = self.SPEED_LEVELS[self.current_level]["multiplier"]
        simulated_elapsed = real_elapsed * multiplier

        return self.simulation_start_time + timedelta(seconds=simulated_elapsed)

    def get_time_status(self) -> Dict[str, Any]:
        """Get comprehensive time status for UI display"""
        sim_time = self.get_current_simulation_time()
        real_elapsed = time.time() - self.real_start_time - self.pause_duration

        # Calculate week progress
        week_start = self.simulation_start_time
        week_end = week_start + timedelta(days=7)
        if sim_time >= week_end:
            # Cycle to next week
            weeks_passed = int((sim_time - week_start).total_seconds() // (7 * 24 * 3600))
            week_start = week_start + timedelta(weeks=weeks_passed)
            week_end = week_start + timedelta(days=7)

        week_progress = ((sim_time - week_start).total_seconds() / (7 * 24 * 3600)) * 100
        week_progress = max(0, min(100, week_progress))

        return {
            "real_time": datetime.now().isoformat(),
            "simulation_time": sim_time.isoformat(),
            "speed_level": self.current_level,
            "speed_name": self.SPEED_LEVELS[self.current_level]["name"],
            "multiplier": self.SPEED_LEVELS[self.current_level]["multiplier"],
            "is_paused": self.is_paused,
            "is_running": self.is_running,
            "week_progress": week_progress,
            "day_of_week": sim_time.strftime("%A"),
            "day_number": sim_time.weekday() + 1,
            "real_elapsed": real_elapsed,
            "sim_elapsed": real_elapsed * self.SPEED_LEVELS[self.current_level]["multiplier"]
        }

    def schedule_event(self, delay_seconds: float, callback: Callable, data: Dict[str, Any] = None):
        """Schedule an event in simulated time"""
        # Convert simulated delay to real delay based on current speed
        real_delay = delay_seconds / self.SPEED_LEVELS[self.current_level]["multiplier"]
        trigger_time = time.time() + real_delay

        event = {
            "trigger_time": trigger_time,
            "callback": callback,
            "data": data or {},
            "simulated_delay": delay_seconds
        }

        self.scheduled_events.append(event)
        self.scheduled_events.sort(key=lambda x: x["trigger_time"])

    def register_email_generator(self, generator):
        """Register email generator for speed scaling"""
        self.email_generator = generator
        logger.info("Email generator registered with TimeWarp")

    def register_agent_system(self, agent_system):
        """Register agent system for speed scaling"""
        self.agent_system = agent_system
        logger.info("Agent system registered with TimeWarp")

    def add_ui_callback(self, callback: Callable):
        """Add UI callback for real-time updates"""
        self.ui_callbacks.append(callback)

    def _timer_loop(self):
        """Main timer loop for event processing and weekly cycle management"""
        last_email_generation = time.time()

        while self.running and self.is_running:
            try:
                if not self.is_paused:
                    current_sim_time = self.get_current_simulation_time()
                    current_real_time = time.time()

                    # Check for weekly cycle restart
                    self._check_weekly_cycle_restart(current_sim_time)

                    # Generate emails based on weekly patterns and TimeWarp speed
                    if self._should_generate_emails(current_real_time, last_email_generation):
                        self._generate_weekly_emails(current_sim_time)
                        last_email_generation = current_real_time

                    # Process scheduled events
                    events_to_remove = []
                    for event in self.scheduled_events:
                        if current_real_time >= event["trigger_time"]:
                            try:
                                event["callback"](event["data"])
                            except Exception as e:
                                logger.error(f"Error executing scheduled event: {e}")
                            events_to_remove.append(event)

                    # Remove processed events
                    for event in events_to_remove:
                        self.scheduled_events.remove(event)

                    # Send periodic updates to UI
                    status = self.get_time_status()
                    status['week_cycle'] = self.week_cycle_count
                    status['emails_this_week'] = self.emails_generated_this_week
                    self._notify_ui_callbacks("time_update", status)

                time.sleep(0.1)  # 100ms update interval

            except Exception as e:
                logger.error(f"Error in TimeWarp timer loop: {e}")
                time.sleep(1)

    def _update_system_speeds(self):
        """Update all integrated system speeds"""
        speed_config = self.SPEED_LEVELS[self.current_level]

        # Update email generator
        if self.email_generator:
            try:
                self.email_generator.set_generation_interval(speed_config["email_interval"])
            except Exception as e:
                logger.error(f"Error updating email generator speed: {e}")

        # Update agent system
        if self.agent_system:
            try:
                self.agent_system.set_processing_speed(speed_config["multiplier"])
            except Exception as e:
                logger.error(f"Error updating agent system speed: {e}")

    def _notify_ui_callbacks(self, event_type: str, data: Dict[str, Any]):
        """Notify all registered UI callbacks"""
        for callback in self.ui_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                logger.error(f"Error in UI callback: {e}")

    def get_speed_config(self, level: int = None) -> Dict[str, Any]:
        """Get speed configuration for a specific level"""
        if level is None:
            level = self.current_level
        return self.SPEED_LEVELS.get(level, self.SPEED_LEVELS[1])

    def get_all_speed_levels(self) -> Dict[int, Dict[str, Any]]:
        """Get all available speed levels"""
        return self.SPEED_LEVELS.copy()

    def _check_weekly_cycle_restart(self, current_sim_time: datetime):
        """Check if we should restart the weekly simulation cycle"""
        if not self.weekly_restart_enabled:
            return

        # Check if we've completed a full week (7 days)
        week_elapsed = current_sim_time - self.current_week_start
        if week_elapsed.days >= 7:
            # Start new week cycle
            self.week_cycle_count += 1
            self.current_week_start = self.current_week_start + timedelta(days=7)
            self.emails_generated_this_week = 0

            logger.info(f"🔄 Starting week cycle #{self.week_cycle_count} at simulation time {current_sim_time.strftime('%Y-%m-%d %H:%M:%S')}")

            # Notify UI of new week
            self._notify_ui_callbacks("new_week", {
                "cycle": self.week_cycle_count,
                "start_time": self.current_week_start.isoformat(),
                "sim_time": current_sim_time.isoformat()
            })

    def _should_generate_emails(self, current_real_time: float, last_generation: float) -> bool:
        """Determine if we should generate emails based on TimeWarp speed"""
        # Get email generation interval based on current speed level
        speed_config = self.SPEED_LEVELS[self.current_level]
        interval = speed_config["email_interval"]

        return (current_real_time - last_generation) >= interval

    def _generate_weekly_emails(self, current_sim_time: datetime):
        """Generate emails based on weekly patterns and current simulation time"""
        # Determine day and time context
        day_name = current_sim_time.strftime('%A').lower()
        hour = current_sim_time.hour

        # Skip weekends for business emails (optional - can be configured)
        if day_name in ['saturday', 'sunday']:
            return

        # Determine time period
        if 6 <= hour < 12:
            time_period = 'morning'
        elif 12 <= hour < 18:
            time_period = 'afternoon'
        else:
            time_period = 'evening'  # Reduced activity

        # Get email patterns for this day/time
        if day_name in self.weekly_patterns:
            day_patterns = self.weekly_patterns[day_name]
            if time_period in day_patterns:
                email_types = day_patterns[time_period]

                # Generate emails for each type
                total_generated = 0
                for email_type, base_count in email_types.items():
                    # Scale email count based on TimeWarp speed (but keep realistic)
                    speed_multiplier = min(self.SPEED_LEVELS[self.current_level]["multiplier"] / 60, 5)
                    email_count = max(1, int(base_count * speed_multiplier))

                    # Generate the emails
                    if self.email_generator:
                        try:
                            self.email_generator.generate_business_emails(
                                email_type=email_type,
                                count=email_count,
                                sim_time=current_sim_time,
                                day=day_name,
                                period=time_period
                            )
                            total_generated += email_count
                        except Exception as e:
                            logger.error(f"Error generating {email_type} emails: {e}")

                if total_generated > 0:
                    self.emails_generated_this_week += total_generated
                    logger.debug(f"Generated {total_generated} emails for {day_name} {time_period}")

    def get_weekly_schedule(self) -> Dict[str, Any]:
        """Get the complete weekly email generation schedule"""
        return {
            "patterns": self.weekly_patterns,
            "current_week": self.week_cycle_count,
            "emails_this_week": self.emails_generated_this_week,
            "week_start": self.current_week_start.isoformat(),
            "restart_enabled": self.weekly_restart_enabled
        }

    def set_weekly_restart(self, enabled: bool):
        """Enable or disable automatic weekly cycle restart"""
        self.weekly_restart_enabled = enabled
        logger.info(f"Weekly restart {'enabled' if enabled else 'disabled'}")

    def configure_email_patterns(self, patterns: Dict[str, Any]):
        """Configure custom email generation patterns"""
        self.weekly_patterns.update(patterns)
        logger.info("Email patterns updated")

    def get_current_week_info(self) -> Dict[str, Any]:
        """Get current week cycle information"""
        current_sim_time = self.get_current_simulation_time()

        # Calculate progress within current week
        week_elapsed = current_sim_time - self.current_week_start
        week_progress = (week_elapsed.total_seconds() / (7 * 24 * 3600)) * 100
        week_progress = max(0, min(100, week_progress))

        return {
            "cycle_number": self.week_cycle_count,
            "week_start": self.current_week_start.isoformat(),
            "current_time": current_sim_time.isoformat(),
            "week_progress": week_progress,
            "day_of_week": current_sim_time.strftime('%A'),
            "day_number": current_sim_time.weekday() + 1,
            "emails_generated": self.emails_generated_this_week,
            "time_until_restart": max(0, 7 - week_elapsed.days)
        }


# Global TimeWarp instance
timewarp = TimeWarpEngine()

def get_timewarp() -> TimeWarpEngine:
    """Get the global TimeWarp instance"""
    return timewarp


if __name__ == "__main__":
    # Test the TimeWarp engine
    print("🚀 Testing TimeWarp Engine")
    print("=" * 50)

    # Initialize logging
    logging.basicConfig(level=logging.INFO)

    # Create TimeWarp instance
    tw = TimeWarpEngine()

    # Test speed levels
    print("Speed Levels:")
    for level, config in tw.get_all_speed_levels().items():
        print(f"  Level {level}: {config['name']} ({config['multiplier']}x) - {config['description']}")

    # Test time calculation
    print("\nStarting TimeWarp engine...")
    tw.start()

    time.sleep(2)
    status = tw.get_time_status()
    print(f"Real time: {status['real_time']}")
    print(f"Sim time: {status['simulation_time']}")
    print(f"Speed: {status['speed_name']} ({status['multiplier']}x)")

    # Test speed change
    print("\nChanging to Time Warp speed (1008x)...")
    tw.set_speed(5)

    time.sleep(2)
    status = tw.get_time_status()
    print(f"New speed: {status['speed_name']} ({status['multiplier']}x)")
    print(f"Week progress: {status['week_progress']:.1f}%")
    print(f"Day: {status['day_of_week']}")

    tw.stop()
    print("\n✅ TimeWarp Engine test completed!")