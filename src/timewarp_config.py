"""
TimeWarp Configuration Manager - Global YAML Configuration System
Happy Buttons Release 2.1 - TimeWarp Professional

Manages all TimeWarp settings, agent configurations, and business rules from YAML files
"""

import yaml
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, time
import copy
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    """Agent configuration structure"""
    name: str
    email_types: List[str]
    processing_speed_multiplier: float
    timewarp_scaling: bool
    response_time_minutes: Dict[str, Any]
    auto_responses: bool
    escalation_rules: Dict[str, Any]
    failure_simulation: Dict[str, Any]

@dataclass
class MailboxConfig:
    """Mailbox configuration structure"""
    address: str
    display_name: str
    assigned_agents: List[str]
    auto_routing: bool
    response_templates: bool
    timewarp_priority: str
    max_emails_per_hour: int

class TimeWarpConfigManager:
    """
    TimeWarp Configuration Manager - Centralized configuration management

    Features:
    - YAML-based configuration
    - Agent behavior configuration
    - Mailbox routing configuration
    - Business rules management
    - Runtime configuration updates
    - Configuration validation
    """

    def __init__(self, config_path: str = "config/timewarp_settings.yaml"):
        self.config_path = config_path
        self.config = {}
        self.agents = {}
        self.mailboxes = {}
        self.last_modified = None

        # Load initial configuration
        self.load_configuration()

        logger.info(f"TimeWarp Configuration Manager initialized (config: {config_path})")

    def load_configuration(self) -> bool:
        """Load configuration from YAML file"""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Configuration file not found: {self.config_path}")
                self._create_default_configuration()
                return False

            # Check if file was modified
            modified_time = os.path.getmtime(self.config_path)
            if self.last_modified and modified_time <= self.last_modified:
                return True  # No changes

            with open(self.config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)

            # Parse agent configurations
            self._parse_agent_configs()

            # Parse mailbox configurations
            self._parse_mailbox_configs()

            # Validate configuration
            self._validate_configuration()

            self.last_modified = modified_time
            logger.info("TimeWarp configuration loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Error loading TimeWarp configuration: {e}")
            return False

    def save_configuration(self) -> bool:
        """Save current configuration to YAML file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.config, file, default_flow_style=False,
                         allow_unicode=True, sort_keys=False)

            self.last_modified = os.path.getmtime(self.config_path)
            logger.info("TimeWarp configuration saved successfully")
            return True

        except Exception as e:
            logger.error(f"Error saving TimeWarp configuration: {e}")
            return False

    def _parse_agent_configs(self):
        """Parse agent configurations into structured objects"""
        self.agents = {}
        agent_configs = self.config.get('agents', {})

        for agent_id, config in agent_configs.items():
            try:
                self.agents[agent_id] = AgentConfig(
                    name=config.get('name', agent_id),
                    email_types=config.get('email_types', []),
                    processing_speed_multiplier=config.get('processing_speed_multiplier', 1.0),
                    timewarp_scaling=config.get('timewarp_scaling', True),
                    response_time_minutes=config.get('response_time_minutes', {'base': 30}),
                    auto_responses=config.get('auto_responses', False),
                    escalation_rules=config.get('escalation_rules', {}),
                    failure_simulation=config.get('failure_simulation', {'enabled': False})
                )

                logger.debug(f"Loaded agent config: {agent_id}")

            except Exception as e:
                logger.error(f"Error parsing agent config {agent_id}: {e}")

    def _parse_mailbox_configs(self):
        """Parse mailbox configurations into structured objects"""
        self.mailboxes = {}
        mailbox_configs = self.config.get('mailboxes', {})

        for mailbox_id, config in mailbox_configs.items():
            try:
                self.mailboxes[mailbox_id] = MailboxConfig(
                    address=config.get('address', f"{mailbox_id}@h-bu.de"),
                    display_name=config.get('display_name', f"Happy Buttons {mailbox_id.title()}"),
                    assigned_agents=config.get('assigned_agents', []),
                    auto_routing=config.get('auto_routing', True),
                    response_templates=config.get('response_templates', True),
                    timewarp_priority=config.get('timewarp_priority', 'medium'),
                    max_emails_per_hour=config.get('max_emails_per_hour', 50)
                )

                logger.debug(f"Loaded mailbox config: {mailbox_id}")

            except Exception as e:
                logger.error(f"Error parsing mailbox config {mailbox_id}: {e}")

    def _validate_configuration(self) -> bool:
        """Validate configuration integrity"""
        errors = []

        # Validate agent configurations
        for agent_id, agent in self.agents.items():
            if not agent.email_types:
                errors.append(f"Agent {agent_id} has no email types assigned")

            if agent.processing_speed_multiplier <= 0:
                errors.append(f"Agent {agent_id} has invalid processing speed multiplier")

            if 'base' not in agent.response_time_minutes:
                errors.append(f"Agent {agent_id} missing base response time")

        # Validate mailbox configurations
        for mailbox_id, mailbox in self.mailboxes.items():
            if not mailbox.assigned_agents:
                errors.append(f"Mailbox {mailbox_id} has no assigned agents")

            # Check if assigned agents exist
            for agent_id in mailbox.assigned_agents:
                if agent_id not in self.agents:
                    errors.append(f"Mailbox {mailbox_id} references unknown agent: {agent_id}")

            if mailbox.max_emails_per_hour <= 0:
                errors.append(f"Mailbox {mailbox_id} has invalid email rate limit")

        # Validate email patterns
        email_patterns = self.config.get('email_patterns', {})
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        valid_periods = ['morning', 'afternoon', 'evening']

        for day in email_patterns:
            if day not in valid_days:
                errors.append(f"Invalid day in email patterns: {day}")
            else:
                for period in email_patterns[day]:
                    if period not in valid_periods:
                        errors.append(f"Invalid period in email patterns {day}: {period}")

        # Log validation results
        if errors:
            for error in errors:
                logger.error(f"Configuration validation error: {error}")
            return False
        else:
            logger.info("Configuration validation passed")
            return True

    def _create_default_configuration(self):
        """Create default configuration if none exists"""
        self.config = {
            'timewarp': {
                'default_level': 1,
                'auto_start': False,
                'email_generation': True,
                'max_level': 5,
                'ui_update_interval': 1000,
                'weekly_restart': True,
                'business_hours_only': False
            },
            'email_patterns': {
                'monday': {
                    'morning': {'customer_inquiry': 3, 'internal_coordination': 2},
                    'afternoon': {'quality_complaint': 1, 'logistics_coordination': 2}
                },
                'tuesday': {
                    'morning': {'customer_inquiry': 2, 'oem_order': 2},
                    'afternoon': {'quality_review': 1, 'production_planning': 1}
                }
            },
            'agents': {
                'customer_service': {
                    'name': 'Customer Service Team',
                    'email_types': ['customer_inquiry'],
                    'processing_speed_multiplier': 1.0,
                    'timewarp_scaling': True,
                    'response_time_minutes': {'base': 30},
                    'auto_responses': True,
                    'escalation_rules': {'complexity_threshold': 0.8},
                    'failure_simulation': {'enabled': False, 'failure_rate': 0.05}
                }
            },
            'mailboxes': {
                'info': {
                    'address': 'info@h-bu.de',
                    'display_name': 'Happy Buttons Info',
                    'assigned_agents': ['customer_service'],
                    'auto_routing': True,
                    'response_templates': True,
                    'timewarp_priority': 'medium',
                    'max_emails_per_hour': 50
                }
            }
        }

        self.save_configuration()
        logger.info("Default configuration created")

    # Configuration Access Methods

    def get_timewarp_settings(self) -> Dict[str, Any]:
        """Get TimeWarp core settings"""
        return self.config.get('timewarp', {})

    def get_email_patterns(self) -> Dict[str, Any]:
        """Get email generation patterns"""
        return self.config.get('email_patterns', {})

    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get configuration for specific agent"""
        return self.agents.get(agent_id)

    def get_all_agents(self) -> Dict[str, AgentConfig]:
        """Get all agent configurations"""
        return self.agents.copy()

    def get_mailbox_config(self, mailbox_id: str) -> Optional[MailboxConfig]:
        """Get configuration for specific mailbox"""
        return self.mailboxes.get(mailbox_id)

    def get_all_mailboxes(self) -> Dict[str, MailboxConfig]:
        """Get all mailbox configurations"""
        return self.mailboxes.copy()

    def get_business_rules(self) -> Dict[str, Any]:
        """Get business rules configuration"""
        return self.config.get('business_rules', {})

    def get_performance_settings(self) -> Dict[str, Any]:
        """Get performance settings"""
        return self.config.get('performance', {})

    def get_simulation_settings(self) -> Dict[str, Any]:
        """Get simulation and testing settings"""
        return self.config.get('simulation', {})

    # Agent Methods

    def get_agents_for_email_type(self, email_type: str) -> List[str]:
        """Get agent IDs that can handle specific email type"""
        agents = []
        for agent_id, agent in self.agents.items():
            if email_type in agent.email_types:
                agents.append(agent_id)
        return agents

    def get_agent_processing_time(self, agent_id: str, priority: str = 'medium',
                                 timewarp_multiplier: float = 1.0) -> float:
        """Calculate agent processing time considering TimeWarp scaling"""
        agent = self.agents.get(agent_id)
        if not agent:
            return 30.0  # Default 30 minutes

        base_time = agent.response_time_minutes.get('base', 30)
        priority_multipliers = agent.response_time_minutes.get('priority_multiplier', {})
        priority_mult = priority_multipliers.get(priority, 1.0)

        processing_time = base_time * priority_mult

        # Apply agent's processing speed multiplier
        processing_time *= agent.processing_speed_multiplier

        # Apply TimeWarp scaling if enabled
        if agent.timewarp_scaling and timewarp_multiplier > 1:
            processing_time /= timewarp_multiplier

        return max(0.1, processing_time)  # Minimum 0.1 minutes

    def is_agent_auto_response_enabled(self, agent_id: str) -> bool:
        """Check if agent has auto-response enabled"""
        agent = self.agents.get(agent_id)
        return agent.auto_responses if agent else False

    def should_escalate(self, agent_id: str, complexity: float,
                       email_volume: int) -> bool:
        """Determine if email should be escalated based on agent rules"""
        agent = self.agents.get(agent_id)
        if not agent:
            return False

        rules = agent.escalation_rules
        complexity_threshold = rules.get('complexity_threshold', 1.0)
        volume_threshold = rules.get('volume_threshold', float('inf'))

        return (complexity >= complexity_threshold or
                email_volume >= volume_threshold)

    # Mailbox Methods

    def get_mailbox_for_email(self, email_address: str) -> Optional[str]:
        """Get mailbox ID for email address"""
        for mailbox_id, mailbox in self.mailboxes.items():
            if mailbox.address.lower() == email_address.lower():
                return mailbox_id
        return None

    def get_agents_for_mailbox(self, mailbox_id: str) -> List[str]:
        """Get assigned agents for mailbox"""
        mailbox = self.mailboxes.get(mailbox_id)
        return mailbox.assigned_agents if mailbox else []

    def can_mailbox_process(self, mailbox_id: str, current_hourly_count: int) -> bool:
        """Check if mailbox can process more emails based on rate limit"""
        mailbox = self.mailboxes.get(mailbox_id)
        if not mailbox:
            return False

        return current_hourly_count < mailbox.max_emails_per_hour

    def get_mailbox_priority(self, mailbox_id: str) -> str:
        """Get TimeWarp priority for mailbox"""
        mailbox = self.mailboxes.get(mailbox_id)
        return mailbox.timewarp_priority if mailbox else 'medium'

    # Configuration Updates

    def update_agent_config(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """Update agent configuration"""
        try:
            if agent_id not in self.config.get('agents', {}):
                logger.error(f"Agent {agent_id} not found")
                return False

            # Update configuration
            agent_config = self.config['agents'][agent_id]
            agent_config.update(updates)

            # Reload parsed configurations
            self._parse_agent_configs()

            # Validate
            if self._validate_configuration():
                logger.info(f"Agent {agent_id} configuration updated")
                return True
            else:
                logger.error(f"Invalid configuration update for agent {agent_id}")
                return False

        except Exception as e:
            logger.error(f"Error updating agent {agent_id}: {e}")
            return False

    def update_timewarp_settings(self, updates: Dict[str, Any]) -> bool:
        """Update TimeWarp core settings"""
        try:
            timewarp_config = self.config.setdefault('timewarp', {})
            timewarp_config.update(updates)

            logger.info("TimeWarp settings updated")
            return True

        except Exception as e:
            logger.error(f"Error updating TimeWarp settings: {e}")
            return False

    def update_email_patterns(self, patterns: Dict[str, Any]) -> bool:
        """Update email generation patterns"""
        try:
            self.config['email_patterns'] = patterns
            logger.info("Email patterns updated")
            return True

        except Exception as e:
            logger.error(f"Error updating email patterns: {e}")
            return False

    # Utility Methods

    def reload_if_changed(self) -> bool:
        """Reload configuration if file was modified"""
        if not os.path.exists(self.config_path):
            return False

        modified_time = os.path.getmtime(self.config_path)
        if self.last_modified and modified_time > self.last_modified:
            logger.info("Configuration file changed, reloading...")
            return self.load_configuration()

        return True

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration"""
        return {
            'timewarp_enabled': self.config.get('timewarp', {}).get('email_generation', False),
            'default_speed_level': self.config.get('timewarp', {}).get('default_level', 1),
            'total_agents': len(self.agents),
            'total_mailboxes': len(self.mailboxes),
            'config_file': self.config_path,
            'last_modified': datetime.fromtimestamp(self.last_modified) if self.last_modified else None,
            'validation_status': 'valid' if self._validate_configuration() else 'invalid'
        }

    def export_config_for_ui(self) -> Dict[str, Any]:
        """Export configuration in format suitable for UI"""
        return {
            'timewarp': self.get_timewarp_settings(),
            'email_patterns': self.get_email_patterns(),
            'agents': {
                agent_id: {
                    'name': agent.name,
                    'email_types': agent.email_types,
                    'processing_speed': agent.processing_speed_multiplier,
                    'timewarp_scaling': agent.timewarp_scaling,
                    'auto_responses': agent.auto_responses,
                    'failure_simulation': agent.failure_simulation
                }
                for agent_id, agent in self.agents.items()
            },
            'mailboxes': {
                mailbox_id: {
                    'address': mailbox.address,
                    'display_name': mailbox.display_name,
                    'assigned_agents': mailbox.assigned_agents,
                    'auto_routing': mailbox.auto_routing,
                    'priority': mailbox.timewarp_priority,
                    'rate_limit': mailbox.max_emails_per_hour
                }
                for mailbox_id, mailbox in self.mailboxes.items()
            },
            'business_rules': self.get_business_rules(),
            'performance': self.get_performance_settings()
        }

# Global configuration manager instance
timewarp_config = None

def get_timewarp_config(config_path: str = "config/timewarp_settings.yaml") -> TimeWarpConfigManager:
    """Get or create the global TimeWarp configuration manager"""
    global timewarp_config
    if timewarp_config is None:
        timewarp_config = TimeWarpConfigManager(config_path)
    return timewarp_config

def reload_timewarp_config():
    """Force reload of TimeWarp configuration"""
    global timewarp_config
    if timewarp_config:
        timewarp_config.load_configuration()
    else:
        timewarp_config = TimeWarpConfigManager()

def get_agent_config(agent_id: str) -> Optional[AgentConfig]:
    """Quick access to agent configuration"""
    config_manager = get_timewarp_config()
    return config_manager.get_agent_config(agent_id)

def get_mailbox_config(mailbox_id: str) -> Optional[MailboxConfig]:
    """Quick access to mailbox configuration"""
    config_manager = get_timewarp_config()
    return config_manager.get_mailbox_config(mailbox_id)