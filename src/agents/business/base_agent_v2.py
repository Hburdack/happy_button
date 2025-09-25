"""
Base Agent Framework for Happy Buttons Release 2
Enhanced agent system with event handling and coordination
"""

import time
import logging
import json
import os
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
import yaml

class AgentStatus(Enum):
    """Agent status states"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class AgentTask:
    id: str
    type: str
    priority: TaskPriority
    data: Dict[str, Any]
    created_at: float = field(default_factory=time.time)
    assigned_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class AgentEvent:
    id: str
    type: str
    source_agent: str
    target_agent: Optional[str]
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

@dataclass
class AgentMetrics:
    tasks_processed: int = 0
    tasks_successful: int = 0
    tasks_failed: int = 0
    avg_processing_time: float = 0.0
    last_activity: float = 0.0
    uptime_start: float = field(default_factory=time.time)

class BaseAgent(ABC):
    """Base class for all Happy Buttons business agents"""

    def __init__(self, agent_id: str, config_path: str = "sim/config/company_release2.yaml"):
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"Agent.{agent_id}")
        self.status = AgentStatus.IDLE
        self.config = self._load_config(config_path)

        # Agent state
        self.task_queue: List[AgentTask] = []
        self.current_task: Optional[AgentTask] = None
        self.metrics = AgentMetrics()

        # Event system
        self.event_handlers: Dict[str, Callable] = {}
        self.event_queue: List[AgentEvent] = []

        # Storage directories
        self._setup_storage()

        # Coordination hooks (for Claude Flow integration)
        self.coordination_hooks = {
            'pre_task': [],
            'post_task': [],
            'session_restore': [],
            'post_edit': []
        }

        self.logger.info(f"Agent {agent_id} initialized")

    def _load_config(self, config_path: str) -> dict:
        """Load agent configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.error(f"Config file not found: {config_path}")
            return {}

    def _setup_storage(self):
        """Setup agent storage directories"""
        self.storage_dir = f"data/agents/{self.agent_id}"
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(f"{self.storage_dir}/tasks", exist_ok=True)
        os.makedirs(f"{self.storage_dir}/events", exist_ok=True)
        os.makedirs(f"{self.storage_dir}/memory", exist_ok=True)

    @abstractmethod
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process a task - must be implemented by subclasses"""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        pass

    async def assign_task(self, task: AgentTask) -> bool:
        """Assign a task to this agent"""
        try:
            # Pre-task hook
            await self._run_pre_task_hooks(task)

            # Add to queue
            task.assigned_at = time.time()
            self.task_queue.append(task)
            self.task_queue.sort(key=lambda t: t.priority.value, reverse=True)

            self.logger.info(f"Task {task.id} assigned (priority: {task.priority.value})")
            return True

        except Exception as e:
            self.logger.error(f"Error assigning task {task.id}: {e}")
            return False

    async def process_next_task(self) -> Optional[Dict[str, Any]]:
        """Process the next task in queue"""
        if not self.task_queue or self.status != AgentStatus.IDLE:
            return None

        task = self.task_queue.pop(0)
        return await self._execute_task(task)

    async def _execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a single task"""
        self.current_task = task
        self.status = AgentStatus.BUSY
        start_time = time.time()

        try:
            self.logger.info(f"Processing task {task.id} (type: {task.type})")

            # Process the task
            result = await self.process_task(task)

            # Update task
            task.completed_at = time.time()
            task.result = result

            # Update metrics
            processing_time = task.completed_at - start_time
            self._update_metrics(processing_time, True)

            # Post-task hook
            await self._run_post_task_hooks(task)

            # Save task result
            self._save_task_result(task)

            self.logger.info(f"Task {task.id} completed successfully in {processing_time:.2f}s")
            return result

        except Exception as e:
            # Handle error
            task.error = str(e)
            task.completed_at = time.time()

            processing_time = task.completed_at - start_time
            self._update_metrics(processing_time, False)

            self.status = AgentStatus.ERROR
            self.logger.error(f"Task {task.id} failed after {processing_time:.2f}s: {e}")

            return {'error': str(e), 'task_id': task.id}

        finally:
            self.current_task = None
            if self.status != AgentStatus.ERROR:
                self.status = AgentStatus.IDLE

    def _update_metrics(self, processing_time: float, success: bool):
        """Update agent performance metrics"""
        self.metrics.tasks_processed += 1
        self.metrics.last_activity = time.time()

        if success:
            self.metrics.tasks_successful += 1
        else:
            self.metrics.tasks_failed += 1

        # Update average processing time
        total_time = self.metrics.avg_processing_time * (self.metrics.tasks_processed - 1)
        self.metrics.avg_processing_time = (total_time + processing_time) / self.metrics.tasks_processed

    def _save_task_result(self, task: AgentTask):
        """Save task result to storage"""
        try:
            task_file = f"{self.storage_dir}/tasks/{task.id}.json"
            task_data = {
                'id': task.id,
                'type': task.type,
                'priority': task.priority.value,
                'data': task.data,
                'created_at': task.created_at,
                'assigned_at': task.assigned_at,
                'completed_at': task.completed_at,
                'result': task.result,
                'error': task.error,
                'processing_time': (task.completed_at or 0) - (task.assigned_at or 0)
            }

            with open(task_file, 'w') as f:
                json.dump(task_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving task result: {e}")

    async def emit_event(self, event_type: str, data: Dict[str, Any],
                        target_agent: Optional[str] = None):
        """Emit an event to other agents"""
        event = AgentEvent(
            id=f"{self.agent_id}_{int(time.time())}_{len(self.event_queue)}",
            type=event_type,
            source_agent=self.agent_id,
            target_agent=target_agent,
            data=data
        )

        # Save event
        self._save_event(event)

        # Broadcast to coordination system
        await self._broadcast_event(event)

        self.logger.debug(f"Emitted event: {event_type} to {target_agent or 'ALL'}")

    def _save_event(self, event: AgentEvent):
        """Save event to storage"""
        try:
            event_file = f"{self.storage_dir}/events/{event.id}.json"
            event_data = {
                'id': event.id,
                'type': event.type,
                'source_agent': event.source_agent,
                'target_agent': event.target_agent,
                'data': event.data,
                'timestamp': event.timestamp
            }

            with open(event_file, 'w') as f:
                json.dump(event_data, f, indent=2)

            # Also save to global events directory for dashboard
            global_events_dir = "data/events"
            os.makedirs(global_events_dir, exist_ok=True)
            global_event_file = f"{global_events_dir}/agent_event_{event.id}.json"

            with open(global_event_file, 'w') as f:
                json.dump(event_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving event: {e}")

    async def _broadcast_event(self, event: AgentEvent):
        """Broadcast event to agent coordination system"""
        # This would integrate with actual message bus in production
        pass

    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler"""
        self.event_handlers[event_type] = handler

    async def handle_event(self, event: AgentEvent):
        """Handle incoming event"""
        if event.type in self.event_handlers:
            try:
                await self.event_handlers[event.type](event)
                self.logger.debug(f"Handled event: {event.type}")
            except Exception as e:
                self.logger.error(f"Error handling event {event.type}: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        uptime = time.time() - self.metrics.uptime_start
        return {
            'agent_id': self.agent_id,
            'status': self.status.value,
            'capabilities': self.get_capabilities(),
            'current_task': self.current_task.id if self.current_task else None,
            'queue_size': len(self.task_queue),
            'metrics': {
                'tasks_processed': self.metrics.tasks_processed,
                'tasks_successful': self.metrics.tasks_successful,
                'tasks_failed': self.metrics.tasks_failed,
                'success_rate': (self.metrics.tasks_successful / max(self.metrics.tasks_processed, 1)) * 100,
                'avg_processing_time': self.metrics.avg_processing_time,
                'uptime_hours': uptime / 3600,
                'last_activity': self.metrics.last_activity
            }
        }

    # Claude Flow Integration Hooks
    async def _run_pre_task_hooks(self, task: AgentTask):
        """Run pre-task coordination hooks"""
        for hook in self.coordination_hooks['pre_task']:
            try:
                await hook(task)
            except Exception as e:
                self.logger.warning(f"Pre-task hook failed: {e}")

    async def _run_post_task_hooks(self, task: AgentTask):
        """Run post-task coordination hooks"""
        for hook in self.coordination_hooks['post_task']:
            try:
                await hook(task)
            except Exception as e:
                self.logger.warning(f"Post-task hook failed: {e}")

    def add_coordination_hook(self, hook_type: str, hook_func: Callable):
        """Add coordination hook for Claude Flow integration"""
        if hook_type in self.coordination_hooks:
            self.coordination_hooks[hook_type].append(hook_func)

    # Memory Management
    def store_memory(self, key: str, value: Any, namespace: str = "default"):
        """Store data in agent memory"""
        try:
            memory_dir = f"{self.storage_dir}/memory/{namespace}"
            os.makedirs(memory_dir, exist_ok=True)

            memory_file = f"{memory_dir}/{key}.json"
            memory_data = {
                'key': key,
                'value': value,
                'timestamp': time.time(),
                'agent_id': self.agent_id
            }

            with open(memory_file, 'w') as f:
                json.dump(memory_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error storing memory {key}: {e}")

    def retrieve_memory(self, key: str, namespace: str = "default") -> Any:
        """Retrieve data from agent memory"""
        try:
            memory_file = f"{self.storage_dir}/memory/{namespace}/{key}.json"

            if os.path.exists(memory_file):
                with open(memory_file, 'r') as f:
                    memory_data = json.load(f)
                    return memory_data['value']

            return None

        except Exception as e:
            self.logger.error(f"Error retrieving memory {key}: {e}")
            return None

    async def shutdown(self):
        """Gracefully shutdown agent"""
        self.logger.info(f"Shutting down agent {self.agent_id}")

        # Complete current task if any
        if self.current_task and self.status == AgentStatus.BUSY:
            self.logger.info("Waiting for current task to complete...")
            # In a real implementation, we'd wait for task completion

        # Save final state
        status_data = self.get_status()
        status_file = f"{self.storage_dir}/final_status.json"

        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)

        self.status = AgentStatus.OFFLINE
        self.logger.info(f"Agent {self.agent_id} shutdown complete")

# Demo implementation for testing
class DemoAgent(BaseAgent):
    """Demo agent implementation for testing"""

    def __init__(self):
        super().__init__("demo_agent")

    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Demo task processing"""
        await asyncio.sleep(0.1)  # Simulate processing time

        return {
            'status': 'completed',
            'result': f"Processed {task.type} task",
            'data_processed': len(str(task.data))
        }

    def get_capabilities(self) -> List[str]:
        """Demo capabilities"""
        return ['demo_processing', 'test_execution', 'data_handling']

# Testing
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def test_agent():
        agent = DemoAgent()

        # Create test task
        task = AgentTask(
            id="test_001",
            type="demo_task",
            priority=TaskPriority.NORMAL,
            data={'message': 'Hello, Agent!'}
        )

        # Process task
        await agent.assign_task(task)
        result = await agent.process_next_task()

        print(f"Task result: {result}")
        print(f"Agent status: {agent.get_status()}")

        await agent.shutdown()

    asyncio.run(test_agent())