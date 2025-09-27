"""
Scenario Manager for Release 3.0 - Weakness Injection System
Manages organizational failure scenarios for Happy Buttons simulation
"""

import yaml
import json
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

# Import scenario implementations
from .late_triage import LateTriage
from .missed_expedite import MissedExpedite
from .vip_handling import VIPHandling
from .global_disruption import GlobalDisruption
from .kpi_tracker import kpi_tracker, KPIType

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScenarioStatus(Enum):
    """Scenario execution status"""
    INACTIVE = "inactive"
    ACTIVATING = "activating"
    ACTIVE = "active"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class ScenarioPriority(Enum):
    """Scenario priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ScenarioMetrics:
    """Metrics for scenario execution tracking"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: int = 0
    impact_score: float = 0.0
    kpi_degradation: Dict[str, float] = None
    events_triggered: int = 0
    alerts_generated: int = 0
    affected_orders: int = 0
    revenue_impact: float = 0.0
    reputation_impact: float = 0.0

    def __post_init__(self):
        if self.kpi_degradation is None:
            self.kpi_degradation = {}

@dataclass
class ScenarioState:
    """Current state of a scenario"""
    scenario_id: str
    name: str
    status: ScenarioStatus
    priority: ScenarioPriority
    enabled: bool
    configuration: Dict[str, Any]
    metrics: ScenarioMetrics
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'scenario_id': self.scenario_id,
            'name': self.name,
            'status': self.status.value,
            'priority': self.priority.value,
            'enabled': self.enabled,
            'configuration': self.configuration,
            'metrics': asdict(self.metrics),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'error_message': self.error_message
        }

class ScenarioManager:
    """
    Central manager for organizational failure scenarios
    Handles scenario configuration, execution, monitoring, and cleanup
    """

    def __init__(self, config_path: str = "config/scenarios/classic_org_scenarios.yaml"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.active_scenarios: Dict[str, ScenarioState] = {}
        self.scenario_history: List[Dict[str, Any]] = []
        self.metrics_cache: Dict[str, Any] = {}

        # Load configuration
        self.load_configuration()

        # Initialize state tracking
        self.is_running = False
        self.last_update = datetime.now()

        logger.info(f"ScenarioManager initialized with config: {config_path}")

        # Start KPI monitoring
        self._setup_kpi_monitoring()

    def _setup_kpi_monitoring(self):
        """Setup KPI monitoring system"""
        try:
            # Set up monitoring to start when event loop is available
            self._kpi_monitoring_requested = True
            logger.info("KPI monitoring setup scheduled")
        except Exception as e:
            logger.error(f"Error setting up KPI monitoring: {e}")

    async def _start_kpi_monitoring_if_needed(self):
        """Start KPI monitoring if requested and not already running"""
        if hasattr(self, '_kpi_monitoring_requested') and self._kpi_monitoring_requested:
            if not kpi_tracker.is_monitoring:
                await kpi_tracker.start_monitoring(interval_seconds=3.0)
                logger.info("KPI monitoring started successfully")
            self._kpi_monitoring_requested = False

    async def start_scenario(self, scenario_id: str, duration_seconds: int = 300) -> Dict[str, Any]:
        """Start a scenario execution"""
        try:
            logger.info(f"Starting scenario: {scenario_id}")

            # Start KPI monitoring if needed
            await self._start_kpi_monitoring_if_needed()

            # Register scenario start with KPI tracker
            kpi_tracker.register_scenario_start(scenario_id)

            # Continue with existing start logic...
            if scenario_id not in self.config.get('scenarios', {}):
                raise ValueError(f"Scenario '{scenario_id}' not found in configuration")

            # Check if scenario is already active
            if scenario_id in self.active_scenarios and self.active_scenarios[scenario_id].status == ScenarioStatus.ACTIVE:
                return {'success': False, 'error': f'Scenario {scenario_id} is already active'}

            # Get scenario configuration
            scenario_config = self.config['scenarios'][scenario_id].copy()

            # Create scenario state
            scenario_state = ScenarioState(
                id=scenario_id,
                status=ScenarioStatus.ACTIVATING,
                configuration=scenario_config,
                started_at=datetime.now(),
                updated_at=datetime.now(),
                metrics=ScenarioMetrics()
            )

            self.active_scenarios[scenario_id] = scenario_state

            # Start async execution
            asyncio.create_task(self._execute_scenario(scenario_id, duration_seconds))

            logger.info(f"Scenario {scenario_id} started successfully")
            return {'success': True, 'scenario_id': scenario_id, 'duration_seconds': duration_seconds}

        except Exception as e:
            logger.error(f"Error starting scenario {scenario_id}: {e}")
            # Clean up KPI tracker registration on error
            kpi_tracker.register_scenario_end(scenario_id)
            return {'success': False, 'error': str(e)}

    async def stop_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """Stop a running scenario"""
        try:
            if scenario_id not in self.active_scenarios:
                return {'success': False, 'error': f'Scenario {scenario_id} is not active'}

            scenario_state = self.active_scenarios[scenario_id]
            scenario_state.status = ScenarioStatus.STOPPING
            scenario_state.updated_at = datetime.now()

            # Complete scenario
            await self._complete_scenario(scenario_id)

            # Unregister from KPI tracker
            kpi_tracker.register_scenario_end(scenario_id)

            logger.info(f"Scenario {scenario_id} stopped successfully")
            return {'success': True, 'scenario_id': scenario_id}

        except Exception as e:
            logger.error(f"Error stopping scenario {scenario_id}: {e}")
            return {'success': False, 'error': str(e)}

    def load_configuration(self) -> None:
        """Load scenario configuration from YAML file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
                logger.info("Scenario configuration loaded successfully")
            else:
                logger.error(f"Configuration file not found: {self.config_path}")
                raise FileNotFoundError(f"Scenario configuration file not found: {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading scenario configuration: {e}")
            raise

    def reload_configuration(self) -> bool:
        """Reload configuration from file"""
        try:
            self.load_configuration()
            logger.info("Configuration reloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error reloading configuration: {e}")
            return False

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate scenario configuration"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        # Check required sections
        required_sections = ['scenarios', 'global_settings', 'execution_rules']
        for section in required_sections:
            if section not in self.config:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing required section: {section}")

        # Validate individual scenarios
        if 'scenarios' in self.config:
            for scenario_id, scenario_config in self.config['scenarios'].items():
                if not isinstance(scenario_config, dict):
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"Invalid scenario configuration: {scenario_id}")
                    continue

                # Check required scenario fields
                required_fields = ['name', 'description', 'enabled', 'category', 'priority']
                for field in required_fields:
                    if field not in scenario_config:
                        validation_result['warnings'].append(f"Missing field '{field}' in scenario: {scenario_id}")

        return validation_result

    def get_available_scenarios(self) -> Dict[str, Any]:
        """Get list of all available scenarios"""
        scenarios = {}

        if 'scenarios' in self.config:
            for scenario_id, scenario_config in self.config['scenarios'].items():
                scenarios[scenario_id] = {
                    'id': scenario_id,
                    'name': scenario_config.get('name', scenario_id),
                    'description': scenario_config.get('description', ''),
                    'category': scenario_config.get('category', 'unknown'),
                    'priority': scenario_config.get('priority', 'medium'),
                    'enabled': scenario_config.get('enabled', False),
                    'status': self.get_scenario_status(scenario_id)
                }

        return scenarios

    def get_scenario_status(self, scenario_id: str) -> str:
        """Get current status of a specific scenario"""
        if scenario_id in self.active_scenarios:
            return self.active_scenarios[scenario_id].status.value
        return ScenarioStatus.INACTIVE.value

    def get_scenario_details(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific scenario"""
        if scenario_id not in self.config.get('scenarios', {}):
            return None

        scenario_config = self.config['scenarios'][scenario_id]

        # Get current state if active
        current_state = None
        if scenario_id in self.active_scenarios:
            current_state = self.active_scenarios[scenario_id].to_dict()

        return {
            'id': scenario_id,
            'configuration': scenario_config,
            'current_state': current_state,
            'available_actions': self._get_available_actions(scenario_id)
        }

    def _get_available_actions(self, scenario_id: str) -> List[str]:
        """Get available actions for a scenario based on current state"""
        if scenario_id not in self.config.get('scenarios', {}):
            return []

        current_status = self.get_scenario_status(scenario_id)
        scenario_enabled = self.config['scenarios'][scenario_id].get('enabled', False)

        actions = []

        if not scenario_enabled:
            actions.append('enable')
        else:
            actions.append('disable')

        if current_status == ScenarioStatus.INACTIVE.value and scenario_enabled:
            actions.append('start')
        elif current_status == ScenarioStatus.ACTIVE.value:
            actions.extend(['pause', 'stop'])
        elif current_status == ScenarioStatus.PAUSED.value:
            actions.extend(['resume', 'stop'])

        actions.append('reset')

        return actions

    async def start_scenario(self, scenario_id: str, duration_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Start a specific scenario"""
        logger.info(f"Starting scenario: {scenario_id}")

        # Validation checks
        if scenario_id not in self.config.get('scenarios', {}):
            return {'success': False, 'error': f'Scenario not found: {scenario_id}'}

        scenario_config = self.config['scenarios'][scenario_id]

        if not scenario_config.get('enabled', False):
            return {'success': False, 'error': f'Scenario not enabled: {scenario_id}'}

        if scenario_id in self.active_scenarios:
            current_status = self.active_scenarios[scenario_id].status
            if current_status in [ScenarioStatus.ACTIVE, ScenarioStatus.ACTIVATING]:
                return {'success': False, 'error': f'Scenario already running: {scenario_id}'}

        # Check concurrent scenario limits
        max_concurrent = self.config.get('global_settings', {}).get('max_concurrent', 2)
        active_count = len([s for s in self.active_scenarios.values()
                           if s.status == ScenarioStatus.ACTIVE])

        if active_count >= max_concurrent:
            return {'success': False, 'error': f'Maximum concurrent scenarios reached: {max_concurrent}'}

        try:
            # Create scenario state
            scenario_state = ScenarioState(
                scenario_id=scenario_id,
                name=scenario_config.get('name', scenario_id),
                status=ScenarioStatus.ACTIVATING,
                priority=ScenarioPriority(scenario_config.get('priority', 'medium')),
                enabled=True,
                configuration=scenario_config,
                metrics=ScenarioMetrics(),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # Set duration
            if duration_seconds is None:
                duration_seconds = self.config.get('global_settings', {}).get('default_duration', 3600)

            # Add to active scenarios
            self.active_scenarios[scenario_id] = scenario_state

            # Start scenario execution
            asyncio.create_task(self._execute_scenario(scenario_id, duration_seconds))

            logger.info(f"Scenario started successfully: {scenario_id}")
            return {
                'success': True,
                'scenario_id': scenario_id,
                'duration_seconds': duration_seconds,
                'status': scenario_state.status.value
            }

        except Exception as e:
            logger.error(f"Error starting scenario {scenario_id}: {e}")
            if scenario_id in self.active_scenarios:
                self.active_scenarios[scenario_id].status = ScenarioStatus.ERROR
                self.active_scenarios[scenario_id].error_message = str(e)
            return {'success': False, 'error': str(e)}

    async def _execute_scenario(self, scenario_id: str, duration_seconds: int) -> None:
        """Execute a scenario (internal method)"""
        try:
            scenario_state = self.active_scenarios[scenario_id]
            scenario_config = scenario_state.configuration

            # Update status to active
            scenario_state.status = ScenarioStatus.ACTIVE
            scenario_state.metrics.start_time = datetime.now()
            scenario_state.updated_at = datetime.now()

            logger.info(f"Executing scenario {scenario_id} for {duration_seconds} seconds")

            # Initialize scenario-specific execution
            if scenario_id == 'late_triage':
                await self._execute_late_triage(scenario_state, duration_seconds)
            elif scenario_id == 'missed_expedite':
                await self._execute_missed_expedite(scenario_state, duration_seconds)
            elif scenario_id == 'vip_handling':
                await self._execute_vip_handling(scenario_state, duration_seconds)
            elif scenario_id == 'global_disruption':
                await self._execute_global_disruption(scenario_state, duration_seconds)
            else:
                logger.warning(f"No specific execution handler for scenario: {scenario_id}")
                await asyncio.sleep(duration_seconds)

            # Complete scenario
            await self._complete_scenario(scenario_id)

        except Exception as e:
            logger.error(f"Error executing scenario {scenario_id}: {e}")
            if scenario_id in self.active_scenarios:
                self.active_scenarios[scenario_id].status = ScenarioStatus.ERROR
                self.active_scenarios[scenario_id].error_message = str(e)

    async def _execute_late_triage(self, scenario_state: ScenarioState, duration_seconds: int) -> None:
        """Execute late triage scenario using LateTriage implementation"""
        logger.info("Executing late triage scenario")

        # Create and execute LateTriage scenario
        late_triage = LateTriage(scenario_state.configuration)

        async def metrics_callback(execution_metrics):
            # Update scenario state metrics from execution
            scenario_state.metrics.events_triggered = execution_metrics.get('total_emails_delayed', 0)
            scenario_state.metrics.affected_orders = execution_metrics.get('sla_violations', 0)
            scenario_state.metrics.kpi_degradation['response_time'] = execution_metrics.get('average_delay_minutes', 0) * 4  # Scale to percentage
            scenario_state.metrics.kpi_degradation['customer_satisfaction'] = max(30, 95 - execution_metrics.get('escalations_triggered', 0) * 15)
            scenario_state.updated_at = datetime.now()

            # Record KPI degradation to real-time tracker
            avg_delay = execution_metrics.get('average_delay_minutes', 0)
            if avg_delay > 0:
                kpi_tracker.record_kpi_reading(KPIType.RESPONSE_TIME, 2.0 + avg_delay / 60.0, scenario_id)
                kpi_tracker.record_kpi_reading(KPIType.SLA_COMPLIANCE, max(85, 99.5 - execution_metrics.get('sla_violations', 0) * 5), scenario_id)

        # Execute the scenario
        execution_results = await late_triage.execute_scenario(duration_seconds, metrics_callback)

        # Update final metrics
        scenario_state.metrics.impact_score = execution_results.get('reputation_impact', 0)
        logger.info(f"Late triage scenario completed with {execution_results.get('total_emails_delayed', 0)} delayed emails")

    async def _execute_missed_expedite(self, scenario_state: ScenarioState, duration_seconds: int) -> None:
        """Execute missed expedite scenario using MissedExpedite implementation"""
        logger.info("Executing missed expedite scenario")

        # Create and execute MissedExpedite scenario
        missed_expedite = MissedExpedite(scenario_state.configuration)

        async def metrics_callback(execution_metrics):
            # Update scenario state metrics from execution
            scenario_state.metrics.events_triggered = execution_metrics.get('total_opportunities', 0)
            scenario_state.metrics.revenue_impact = execution_metrics.get('revenue_lost_euro', 0)
            scenario_state.metrics.affected_orders = execution_metrics.get('opportunities_missed', 0)
            scenario_state.metrics.kpi_degradation['revenue_loss'] = min(100, execution_metrics.get('revenue_lost_euro', 0) / 1000)  # Scale
            scenario_state.metrics.kpi_degradation['competitive_advantage'] = max(20, 100 - execution_metrics.get('competitor_switches', 0) * 25)
            scenario_state.updated_at = datetime.now()

        # Execute the scenario
        execution_results = await missed_expedite.execute_scenario(duration_seconds, metrics_callback)

        # Update final metrics
        scenario_state.metrics.impact_score = 100 - execution_results.get('detection_efficiency', 100)  # Invert for impact
        logger.info(f"Missed expedite scenario completed with €{execution_results.get('revenue_lost_euro', 0):,.0f} revenue lost")

    async def _execute_vip_handling(self, scenario_state: ScenarioState, duration_seconds: int) -> None:
        """Execute VIP handling scenario using VIPHandling implementation"""
        logger.info("Executing VIP handling scenario")

        # Create and execute VIPHandling scenario
        vip_handling = VIPHandling(scenario_state.configuration)

        async def metrics_callback(execution_metrics):
            # Update scenario state metrics from execution
            scenario_state.metrics.events_triggered = execution_metrics.get('total_vip_incidents', 0)
            scenario_state.metrics.impact_score = execution_metrics.get('reputation_damage_score', 0)
            scenario_state.metrics.affected_orders = execution_metrics.get('relationship_terminations', 0)
            scenario_state.metrics.kpi_degradation['reputation'] = min(60, execution_metrics.get('reputation_damage_score', 0) / 2)
            scenario_state.metrics.kpi_degradation['customer_satisfaction'] = max(20, 98 - execution_metrics.get('total_vip_incidents', 0) * 25)
            scenario_state.updated_at = datetime.now()

        # Execute the scenario
        execution_results = await vip_handling.execute_scenario(duration_seconds, metrics_callback)

        # Update final metrics
        scenario_state.metrics.revenue_impact = execution_results.get('high_value_incidents', 0) * 100000  # Estimate revenue at risk
        logger.info(f"VIP handling scenario completed with {execution_results.get('total_vip_incidents', 0)} incidents")

    async def _execute_global_disruption(self, scenario_state: ScenarioState, duration_seconds: int) -> None:
        """Execute global disruption scenario using GlobalDisruption implementation"""
        logger.info("Executing global disruption scenario")

        # Create and execute GlobalDisruption scenario
        global_disruption = GlobalDisruption(scenario_state.configuration)

        async def metrics_callback(execution_metrics):
            # Update scenario state metrics from execution
            scenario_state.metrics.events_triggered = execution_metrics.get('total_orders_affected', 0)
            scenario_state.metrics.affected_orders = execution_metrics.get('total_orders_affected', 0)
            scenario_state.metrics.impact_score = execution_metrics.get('disruption_severity', 1.0) * 20
            scenario_state.metrics.kpi_degradation['delivery_performance'] = min(90, execution_metrics.get('average_delay_days', 0) * 5)
            scenario_state.metrics.kpi_degradation['cost_efficiency'] = min(50, execution_metrics.get('average_cost_increase_percent', 0))
            scenario_state.updated_at = datetime.now()

        # Execute the scenario
        execution_results = await global_disruption.execute_scenario(duration_seconds, metrics_callback)

        # Update final metrics
        scenario_state.metrics.revenue_impact = execution_results.get('average_cost_increase_percent', 0) * 10000  # Estimate cost impact
        logger.info(f"Global disruption scenario completed with {execution_results.get('total_orders_affected', 0)} orders affected")

    async def _complete_scenario(self, scenario_id: str) -> None:
        """Complete scenario execution"""
        if scenario_id not in self.active_scenarios:
            return

        scenario_state = self.active_scenarios[scenario_id]
        scenario_state.status = ScenarioStatus.STOPPED
        scenario_state.metrics.end_time = datetime.now()

        if scenario_state.metrics.start_time:
            duration = scenario_state.metrics.end_time - scenario_state.metrics.start_time
            scenario_state.metrics.duration_seconds = int(duration.total_seconds())

        scenario_state.updated_at = datetime.now()

        # Add to history
        self.scenario_history.append({
            'scenario_id': scenario_id,
            'completed_at': scenario_state.metrics.end_time.isoformat(),
            'duration_seconds': scenario_state.metrics.duration_seconds,
            'metrics': asdict(scenario_state.metrics)
        })

        # Clean up after delay
        reset_delay = self.config.get('global_settings', {}).get('reset_delay', 300)
        await asyncio.sleep(reset_delay)

        if scenario_id in self.active_scenarios:
            del self.active_scenarios[scenario_id]

        logger.info(f"Scenario completed and cleaned up: {scenario_id}")

    async def stop_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """Stop a running scenario"""
        if scenario_id not in self.active_scenarios:
            return {'success': False, 'error': f'Scenario not active: {scenario_id}'}

        try:
            scenario_state = self.active_scenarios[scenario_id]
            scenario_state.status = ScenarioStatus.STOPPING
            scenario_state.updated_at = datetime.now()

            # Force completion
            await self._complete_scenario(scenario_id)

            logger.info(f"Scenario stopped: {scenario_id}")
            return {'success': True, 'scenario_id': scenario_id}

        except Exception as e:
            logger.error(f"Error stopping scenario {scenario_id}: {e}")
            return {'success': False, 'error': str(e)}

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        active_scenarios = list(self.active_scenarios.keys())

        return {
            'manager_status': 'running' if self.is_running else 'stopped',
            'active_scenarios_count': len(active_scenarios),
            'active_scenarios': active_scenarios,
            'configuration_valid': self.validate_configuration()['valid'],
            'last_update': self.last_update.isoformat(),
            'total_scenarios_available': len(self.config.get('scenarios', {})),
            'scenario_history_count': len(self.scenario_history)
        }

    def get_scenario_metrics(self, scenario_id: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for specific scenario or all scenarios"""
        if scenario_id:
            if scenario_id in self.active_scenarios:
                return asdict(self.active_scenarios[scenario_id].metrics)
            return {}

        # Return metrics for all active scenarios
        all_metrics = {}
        for sid, state in self.active_scenarios.items():
            all_metrics[sid] = asdict(state.metrics)

        return all_metrics

    def enable_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """Enable a scenario"""
        if scenario_id not in self.config.get('scenarios', {}):
            return {'success': False, 'error': f'Scenario not found: {scenario_id}'}

        self.config['scenarios'][scenario_id]['enabled'] = True

        # Save configuration (in real implementation, would save to file)
        logger.info(f"Scenario enabled: {scenario_id}")
        return {'success': True, 'scenario_id': scenario_id, 'enabled': True}

    def disable_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """Disable a scenario"""
        if scenario_id not in self.config.get('scenarios', {}):
            return {'success': False, 'error': f'Scenario not found: {scenario_id}'}

        # Stop scenario if currently running
        if scenario_id in self.active_scenarios:
            asyncio.create_task(self.stop_scenario(scenario_id))

        self.config['scenarios'][scenario_id]['enabled'] = False

        logger.info(f"Scenario disabled: {scenario_id}")
        return {'success': True, 'scenario_id': scenario_id, 'enabled': False}

    def reset_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """Reset scenario to initial state"""
        # Stop if running
        if scenario_id in self.active_scenarios:
            asyncio.create_task(self.stop_scenario(scenario_id))

        # Clear from history (optional)
        self.scenario_history = [h for h in self.scenario_history if h['scenario_id'] != scenario_id]

        logger.info(f"Scenario reset: {scenario_id}")
        return {'success': True, 'scenario_id': scenario_id}

    def get_real_time_kpi_metrics(self) -> Dict[str, Any]:
        """Get current real-time KPI metrics from tracker"""
        try:
            return {
                'current_kpis': kpi_tracker.get_current_kpi_values(),
                'alert_summary': kpi_tracker.get_alert_summary(hours=1),
                'active_scenarios': list(kpi_tracker.active_scenarios.keys()),
                'monitoring_status': kpi_tracker.is_monitoring,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting KPI metrics: {e}")
            return {
                'current_kpis': {},
                'alert_summary': {'alert_counts': {}, 'total_alerts': 0, 'recent_alerts': []},
                'active_scenarios': [],
                'monitoring_status': False,
                'error': str(e)
            }

    def get_kpi_history(self, kpi_type: str, hours: int = 1) -> List[Dict[str, Any]]:
        """Get KPI history for visualization"""
        try:
            from .kpi_tracker import KPIType
            kpi_enum = KPIType(kpi_type)
            return kpi_tracker.get_kpi_history(kpi_enum, hours)
        except Exception as e:
            logger.error(f"Error getting KPI history for {kpi_type}: {e}")
            return []


# Global instance
scenario_manager = ScenarioManager()

# API helper functions
def get_scenario_manager() -> ScenarioManager:
    """Get the global scenario manager instance"""
    return scenario_manager