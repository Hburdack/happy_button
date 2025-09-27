"""
Real-time KPI Degradation Tracking for Release 3.0
Monitors and tracks Key Performance Indicators during scenario execution
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class KPIType(Enum):
    """KPI measurement types"""
    RESPONSE_TIME = "response_time"
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    REVENUE_IMPACT = "revenue_impact"
    SLA_COMPLIANCE = "sla_compliance"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    COST_INCREASE = "cost_increase"
    REPUTATION_SCORE = "reputation_score"

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class KPIThreshold:
    """KPI threshold configuration"""
    warning_threshold: float
    critical_threshold: float
    emergency_threshold: float
    baseline_value: float
    unit: str = ""
    direction: str = "decrease"  # "increase" or "decrease" for degradation

@dataclass
class KPIReading:
    """Individual KPI measurement"""
    timestamp: datetime
    value: float
    scenario_id: Optional[str] = None
    alert_level: Optional[AlertLevel] = None
    degradation_percentage: Optional[float] = None

@dataclass
class KPIAlert:
    """KPI alert notification"""
    kpi_type: KPIType
    alert_level: AlertLevel
    current_value: float
    threshold_value: float
    degradation_percentage: float
    timestamp: datetime
    scenario_id: Optional[str] = None
    message: str = ""

class RealTimeKPITracker:
    """Real-time KPI degradation tracking system"""

    def __init__(self, config_path: str = "config/kpi_thresholds.yaml"):
        self.config_path = Path(config_path)
        self.kpi_thresholds: Dict[KPIType, KPIThreshold] = {}
        self.kpi_history: Dict[KPIType, List[KPIReading]] = {}
        self.alert_callbacks: List[Callable[[KPIAlert], None]] = []
        self.active_scenarios: Dict[str, datetime] = {}
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None

        # Load default thresholds
        self._setup_default_thresholds()

        # Ensure data directory exists
        Path("data/metrics").mkdir(parents=True, exist_ok=True)

    def _setup_default_thresholds(self):
        """Setup default KPI thresholds"""
        self.kpi_thresholds = {
            KPIType.RESPONSE_TIME: KPIThreshold(
                baseline_value=2.0,
                warning_threshold=4.0,
                critical_threshold=8.0,
                emergency_threshold=15.0,
                unit="seconds",
                direction="increase"
            ),
            KPIType.CUSTOMER_SATISFACTION: KPIThreshold(
                baseline_value=4.5,
                warning_threshold=4.0,
                critical_threshold=3.5,
                emergency_threshold=3.0,
                unit="stars",
                direction="decrease"
            ),
            KPIType.REVENUE_IMPACT: KPIThreshold(
                baseline_value=0.0,
                warning_threshold=-1000.0,
                critical_threshold=-5000.0,
                emergency_threshold=-10000.0,
                unit="$",
                direction="decrease"
            ),
            KPIType.SLA_COMPLIANCE: KPIThreshold(
                baseline_value=99.5,
                warning_threshold=95.0,
                critical_threshold=90.0,
                emergency_threshold=85.0,
                unit="%",
                direction="decrease"
            ),
            KPIType.ERROR_RATE: KPIThreshold(
                baseline_value=0.1,
                warning_threshold=2.0,
                critical_threshold=5.0,
                emergency_threshold=10.0,
                unit="%",
                direction="increase"
            ),
            KPIType.THROUGHPUT: KPIThreshold(
                baseline_value=100.0,
                warning_threshold=80.0,
                critical_threshold=60.0,
                emergency_threshold=40.0,
                unit="req/min",
                direction="decrease"
            ),
            KPIType.COST_INCREASE: KPIThreshold(
                baseline_value=0.0,
                warning_threshold=10.0,
                critical_threshold=25.0,
                emergency_threshold=50.0,
                unit="%",
                direction="increase"
            ),
            KPIType.REPUTATION_SCORE: KPIThreshold(
                baseline_value=85.0,
                warning_threshold=75.0,
                critical_threshold=65.0,
                emergency_threshold=50.0,
                unit="score",
                direction="decrease"
            )
        }

    def add_alert_callback(self, callback: Callable[[KPIAlert], None]):
        """Add callback for KPI alerts"""
        self.alert_callbacks.append(callback)

    def record_kpi_reading(self, kpi_type: KPIType, value: float, scenario_id: Optional[str] = None):
        """Record a new KPI reading and check for alerts"""
        if kpi_type not in self.kpi_thresholds:
            logger.warning(f"No threshold configured for KPI type: {kpi_type}")
            return

        threshold = self.kpi_thresholds[kpi_type]

        # Calculate degradation percentage
        degradation_percentage = self._calculate_degradation(value, threshold)

        # Determine alert level
        alert_level = self._determine_alert_level(value, threshold)

        # Create KPI reading
        reading = KPIReading(
            timestamp=datetime.now(),
            value=value,
            scenario_id=scenario_id,
            alert_level=alert_level,
            degradation_percentage=degradation_percentage
        )

        # Store reading
        if kpi_type not in self.kpi_history:
            self.kpi_history[kpi_type] = []

        self.kpi_history[kpi_type].append(reading)

        # Limit history to last 1000 readings
        if len(self.kpi_history[kpi_type]) > 1000:
            self.kpi_history[kpi_type] = self.kpi_history[kpi_type][-1000:]

        # Generate alert if needed
        if alert_level and alert_level != AlertLevel.INFO:
            self._generate_alert(kpi_type, reading, threshold)

        # Save to disk periodically
        asyncio.create_task(self._save_metrics_async())

    def _calculate_degradation(self, current_value: float, threshold: KPIThreshold) -> float:
        """Calculate degradation percentage from baseline"""
        baseline = threshold.baseline_value

        if baseline == 0:
            return 0.0

        if threshold.direction == "decrease":
            # Lower values are worse (e.g., customer satisfaction)
            degradation = ((baseline - current_value) / baseline) * 100
        else:
            # Higher values are worse (e.g., response time)
            degradation = ((current_value - baseline) / baseline) * 100

        return max(0.0, degradation)

    def _determine_alert_level(self, value: float, threshold: KPIThreshold) -> Optional[AlertLevel]:
        """Determine alert level based on value and thresholds"""
        if threshold.direction == "decrease":
            # Lower values trigger alerts
            if value <= threshold.emergency_threshold:
                return AlertLevel.EMERGENCY
            elif value <= threshold.critical_threshold:
                return AlertLevel.CRITICAL
            elif value <= threshold.warning_threshold:
                return AlertLevel.WARNING
        else:
            # Higher values trigger alerts
            if value >= threshold.emergency_threshold:
                return AlertLevel.EMERGENCY
            elif value >= threshold.critical_threshold:
                return AlertLevel.CRITICAL
            elif value >= threshold.warning_threshold:
                return AlertLevel.WARNING

        return AlertLevel.INFO

    def _generate_alert(self, kpi_type: KPIType, reading: KPIReading, threshold: KPIThreshold):
        """Generate and dispatch KPI alert"""
        # Determine threshold value for this alert level
        threshold_value = threshold.baseline_value
        if reading.alert_level == AlertLevel.WARNING:
            threshold_value = threshold.warning_threshold
        elif reading.alert_level == AlertLevel.CRITICAL:
            threshold_value = threshold.critical_threshold
        elif reading.alert_level == AlertLevel.EMERGENCY:
            threshold_value = threshold.emergency_threshold

        # Create alert message
        direction_word = "degraded" if threshold.direction == "decrease" else "increased"
        scenario_text = f" during scenario '{reading.scenario_id}'" if reading.scenario_id else ""

        message = (
            f"KPI {kpi_type.value} has {direction_word} to {reading.value}{threshold.unit} "
            f"({reading.degradation_percentage:.1f}% degradation){scenario_text}"
        )

        alert = KPIAlert(
            kpi_type=kpi_type,
            alert_level=reading.alert_level,
            current_value=reading.value,
            threshold_value=threshold_value,
            degradation_percentage=reading.degradation_percentage or 0.0,
            timestamp=reading.timestamp,
            scenario_id=reading.scenario_id,
            message=message
        )

        # Log alert
        logger.warning(f"KPI Alert [{alert.alert_level.value.upper()}]: {alert.message}")

        # Dispatch to callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    async def start_monitoring(self, interval_seconds: float = 5.0):
        """Start real-time KPI monitoring"""
        if self.is_monitoring:
            logger.warning("KPI monitoring already active")
            return

        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop(interval_seconds))
        logger.info(f"Started KPI monitoring with {interval_seconds}s interval")

    async def stop_monitoring(self):
        """Stop KPI monitoring"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped KPI monitoring")

    async def _monitoring_loop(self, interval_seconds: float):
        """Main monitoring loop"""
        try:
            while self.is_monitoring:
                # Simulate real KPI collection (in real implementation, this would
                # collect from actual system metrics, database queries, etc.)
                await self._collect_simulated_metrics()

                await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            logger.info("KPI monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Error in KPI monitoring loop: {e}")
            self.is_monitoring = False

    async def _collect_simulated_metrics(self):
        """Collect simulated KPI metrics (placeholder for real implementation)"""
        # This is a simulation - in real implementation, you would:
        # - Query database for response times
        # - Check customer satisfaction surveys
        # - Calculate revenue impact
        # - Monitor SLA compliance
        # - Track error rates from logs
        # - Measure throughput from metrics

        import random

        # Simulate degradation based on active scenarios
        degradation_factor = 1.0
        active_scenario_count = len(self.active_scenarios)

        if active_scenario_count > 0:
            # More scenarios = more degradation
            degradation_factor = 1.0 + (active_scenario_count * 0.3)

        # Simulate realistic KPI values with scenario impact
        base_metrics = {
            KPIType.RESPONSE_TIME: 2.0 * degradation_factor + random.uniform(-0.5, 1.0),
            KPIType.CUSTOMER_SATISFACTION: max(1.0, 4.5 - (degradation_factor - 1.0) * 2.0 + random.uniform(-0.2, 0.1)),
            KPIType.SLA_COMPLIANCE: max(50.0, 99.5 - (degradation_factor - 1.0) * 15.0 + random.uniform(-2.0, 1.0)),
            KPIType.ERROR_RATE: 0.1 * degradation_factor + random.uniform(0, 0.5),
            KPIType.THROUGHPUT: max(20.0, 100.0 / degradation_factor + random.uniform(-10.0, 5.0)),
        }

        # Record metrics for active scenarios
        scenario_id = list(self.active_scenarios.keys())[0] if self.active_scenarios else None

        for kpi_type, value in base_metrics.items():
            self.record_kpi_reading(kpi_type, value, scenario_id)

    def register_scenario_start(self, scenario_id: str):
        """Register that a scenario has started"""
        self.active_scenarios[scenario_id] = datetime.now()
        logger.info(f"Registered scenario start: {scenario_id}")

    def register_scenario_end(self, scenario_id: str):
        """Register that a scenario has ended"""
        if scenario_id in self.active_scenarios:
            del self.active_scenarios[scenario_id]
            logger.info(f"Registered scenario end: {scenario_id}")

    def get_current_kpi_values(self) -> Dict[str, Any]:
        """Get current KPI values and status"""
        current_values = {}

        for kpi_type in self.kpi_thresholds.keys():
            if kpi_type in self.kpi_history and self.kpi_history[kpi_type]:
                latest_reading = self.kpi_history[kpi_type][-1]
                current_values[kpi_type.value] = {
                    "value": latest_reading.value,
                    "degradation_percentage": latest_reading.degradation_percentage,
                    "alert_level": latest_reading.alert_level.value if latest_reading.alert_level else "info",
                    "timestamp": latest_reading.timestamp.isoformat(),
                    "unit": self.kpi_thresholds[kpi_type].unit
                }
            else:
                threshold = self.kpi_thresholds[kpi_type]
                current_values[kpi_type.value] = {
                    "value": threshold.baseline_value,
                    "degradation_percentage": 0.0,
                    "alert_level": "info",
                    "timestamp": datetime.now().isoformat(),
                    "unit": threshold.unit
                }

        return current_values

    def get_kpi_history(self, kpi_type: KPIType, hours: int = 1) -> List[Dict[str, Any]]:
        """Get KPI history for specified time period"""
        if kpi_type not in self.kpi_history:
            return []

        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_readings = [
            reading for reading in self.kpi_history[kpi_type]
            if reading.timestamp >= cutoff_time
        ]

        return [
            {
                "timestamp": reading.timestamp.isoformat(),
                "value": reading.value,
                "degradation_percentage": reading.degradation_percentage,
                "alert_level": reading.alert_level.value if reading.alert_level else "info",
                "scenario_id": reading.scenario_id
            }
            for reading in recent_readings
        ]

    def get_alert_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get summary of alerts in specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        alert_counts = {level.value: 0 for level in AlertLevel}
        recent_alerts = []

        for kpi_type, readings in self.kpi_history.items():
            for reading in readings:
                if (reading.timestamp >= cutoff_time and
                    reading.alert_level and
                    reading.alert_level != AlertLevel.INFO):

                    alert_counts[reading.alert_level.value] += 1
                    recent_alerts.append({
                        "kpi_type": kpi_type.value,
                        "alert_level": reading.alert_level.value,
                        "value": reading.value,
                        "degradation_percentage": reading.degradation_percentage,
                        "timestamp": reading.timestamp.isoformat(),
                        "scenario_id": reading.scenario_id
                    })

        # Sort by timestamp, most recent first
        recent_alerts.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "alert_counts": alert_counts,
            "total_alerts": sum(alert_counts.values()),
            "recent_alerts": recent_alerts[:10]  # Last 10 alerts
        }

    async def _save_metrics_async(self):
        """Save metrics to disk asynchronously"""
        try:
            metrics_data = {
                "kpi_thresholds": {
                    kpi_type.value: asdict(threshold)
                    for kpi_type, threshold in self.kpi_thresholds.items()
                },
                "current_values": self.get_current_kpi_values(),
                "active_scenarios": {
                    scenario_id: start_time.isoformat()
                    for scenario_id, start_time in self.active_scenarios.items()
                },
                "last_updated": datetime.now().isoformat()
            }

            with open("data/metrics/kpi_tracker_state.json", "w") as f:
                json.dump(metrics_data, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error saving KPI metrics: {e}")

# Global KPI tracker instance
kpi_tracker = RealTimeKPITracker()