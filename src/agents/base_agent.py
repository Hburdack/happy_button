"""
Base Agent Framework for Happy Buttons Agentic Simulation
Provides foundation for all business unit agents with Claude Flow integration
"""

import asyncio
import logging
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import json
import uuid

from email.parser import ParsedEmail
from email.router import RoutingDecision

logger = logging.getLogger(__name__)


@dataclass
class AgentTask:
    """Represents a task for an agent to process"""
    id: str
    email_id: str
    task_type: str
    priority: str
    data: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    assigned_agent: Optional[str] = None
    completion_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class AgentMemory:
    """Agent memory for coordination and learning"""
    agent_id: str
    session_id: str
    memories: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class AgentResponse:
    """Response from agent processing"""
    task_id: str
    agent_id: str
    status: str  # success, error, pending
    response_data: Dict[str, Any]
    auto_reply: Optional[str] = None
    next_actions: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    coordination_notes: List[str] = field(default_factory=list)


class BaseAgent(ABC):
    """
    Base class for all Happy Buttons business agents
    Integrates with Claude Flow for coordination and memory
    """

    def __init__(self, agent_id: str, agent_type: str, config: Optional[Dict] = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config or {}
        self.session_id = f"swarm-{uuid.uuid4().hex[:8]}"

        # Agent state
        self.is_active = False
        self.task_queue: List[AgentTask] = []
        self.processed_tasks = 0
        self.error_count = 0

        # Memory and coordination
        self.memory = AgentMemory(
            agent_id=self.agent_id,
            session_id=self.session_id
        )

        # Performance metrics
        self.metrics = {
            'tasks_processed': 0,
            'avg_processing_time': 0.0,
            'success_rate': 1.0,
            'last_activity': datetime.now()
        }

        logger.info(f"Initialized {self.agent_type} agent: {self.agent_id}")

    async def start(self) -> None:
        """Start the agent and initialize Claude Flow hooks"""
        try:
            self.is_active = True

            # Initialize Claude Flow coordination
            await self._run_claude_flow_hook('pre-task', {
                'description': f'Starting {self.agent_type} agent',
                'agent_id': self.agent_id
            })

            # Restore session if available
            await self._run_claude_flow_hook('session-restore', {
                'session_id': self.session_id
            })

            logger.info(f"Agent {self.agent_id} started successfully")

        except Exception as e:
            logger.error(f"Failed to start agent {self.agent_id}: {str(e)}")
            raise

    async def stop(self) -> None:
        """Stop the agent and finalize coordination"""
        try:
            self.is_active = False

            # Run post-task hooks
            await self._run_claude_flow_hook('post-task', {
                'task_id': self.agent_id,
                'metrics': self.metrics
            })

            # End session
            await self._run_claude_flow_hook('session-end', {
                'export_metrics': True,
                'session_id': self.session_id
            })

            logger.info(f"Agent {self.agent_id} stopped")

        except Exception as e:
            logger.error(f"Error stopping agent {self.agent_id}: {str(e)}")

    async def process_email(self, parsed_email: ParsedEmail,
                           routing_decision: RoutingDecision) -> AgentResponse:
        """
        Main method to process an email
        Template method pattern - calls abstract methods
        """
        task_id = f"task_{uuid.uuid4().hex[:8]}"

        try:
            # Create task
            task = AgentTask(
                id=task_id,
                email_id=parsed_email.id,
                task_type='email_processing',
                priority=routing_decision.priority,
                data={
                    'email': parsed_email,
                    'routing': routing_decision
                }
            )

            # Add to queue
            self.task_queue.append(task)
            task.assigned_agent = self.agent_id
            task.status = "processing"

            start_time = datetime.now()

            # Run Claude Flow pre-processing hook
            await self._coordinate_pre_processing(task)

            # Call abstract method for agent-specific processing
            response = await self._process_email_impl(parsed_email, routing_decision, task)

            # Update task status
            task.status = "completed" if response.status == "success" else "error"
            task.completion_time = datetime.now()
            task.result = response.response_data

            # Update metrics
            processing_time = (task.completion_time - start_time).total_seconds()
            await self._update_metrics(processing_time, response.status == "success")

            # Run Claude Flow post-processing hook
            await self._coordinate_post_processing(task, response)

            return response

        except Exception as e:
            logger.error(f"Agent {self.agent_id} processing failed: {str(e)}")
            return AgentResponse(
                task_id=task_id,
                agent_id=self.agent_id,
                status="error",
                response_data={'error': str(e)},
                metrics={'processing_time': 0, 'error': True}
            )

    @abstractmethod
    async def _process_email_impl(self, parsed_email: ParsedEmail,
                                 routing_decision: RoutingDecision,
                                 task: AgentTask) -> AgentResponse:
        """
        Abstract method for agent-specific email processing
        Must be implemented by each business unit agent
        """
        pass

    @abstractmethod
    def get_agent_capabilities(self) -> Dict[str, Any]:
        """
        Return agent capabilities and specializations
        """
        pass

    @abstractmethod
    def validate_email_for_agent(self, parsed_email: ParsedEmail) -> bool:
        """
        Validate if this agent can handle the given email
        """
        pass

    async def _coordinate_pre_processing(self, task: AgentTask) -> None:
        """Run Claude Flow coordination before processing"""
        try:
            # Store task in memory for coordination
            await self._store_in_memory(f"task/{task.id}", {
                'task_id': task.id,
                'email_id': task.email_id,
                'priority': task.priority,
                'agent_id': self.agent_id,
                'status': task.status,
                'timestamp': task.created_at.isoformat()
            })

            # Notify other agents
            await self._run_claude_flow_hook('notify', {
                'message': f"{self.agent_type} agent processing {task.email_id}",
                'task_id': task.id,
                'agent_id': self.agent_id
            })

        except Exception as e:
            logger.warning(f"Pre-processing coordination failed: {str(e)}")

    async def _coordinate_post_processing(self, task: AgentTask,
                                        response: AgentResponse) -> None:
        """Run Claude Flow coordination after processing"""
        try:
            # Update memory with results
            await self._store_in_memory(f"result/{task.id}", {
                'task_id': task.id,
                'status': response.status,
                'completion_time': task.completion_time.isoformat() if task.completion_time else None,
                'agent_id': self.agent_id,
                'auto_reply': response.auto_reply,
                'metrics': response.metrics
            })

            # Run post-edit hook for coordination
            await self._run_claude_flow_hook('post-edit', {
                'file': f"memory/agent_{self.agent_id}",
                'memory_key': f"swarm/{self.agent_id}/{task.id}",
                'action': 'task_completed'
            })

        except Exception as e:
            logger.warning(f"Post-processing coordination failed: {str(e)}")

    async def _run_claude_flow_hook(self, hook_type: str, params: Dict[str, Any]) -> None:
        """Run Claude Flow hook for coordination"""
        try:
            # Build command
            cmd = [
                'npx', 'claude-flow@alpha', 'hooks', hook_type
            ]

            # Add parameters
            for key, value in params.items():
                cmd.extend([f'--{key}', str(value)])

            # Run command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.warning(f"Claude Flow hook {hook_type} failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.warning(f"Claude Flow hook {hook_type} timed out")
        except Exception as e:
            logger.warning(f"Claude Flow hook {hook_type} error: {str(e)}")

    async def _store_in_memory(self, key: str, data: Dict[str, Any]) -> None:
        """Store data in agent memory for coordination"""
        try:
            self.memory.memories[key] = data
            self.memory.last_updated = datetime.now()

            # Optional: Persist to file system for Claude Flow access
            memory_dir = Path('.swarm/memory')
            memory_dir.mkdir(parents=True, exist_ok=True)

            memory_file = memory_dir / f"agent_{self.agent_id}.json"
            with open(memory_file, 'w') as f:
                json.dump({
                    'agent_id': self.agent_id,
                    'session_id': self.session_id,
                    'memories': self.memory.memories,
                    'metrics': self.memory.metrics,
                    'last_updated': self.memory.last_updated.isoformat()
                }, f, indent=2)

        except Exception as e:
            logger.warning(f"Memory storage failed: {str(e)}")

    async def _update_metrics(self, processing_time: float, success: bool) -> None:
        """Update agent performance metrics"""
        self.processed_tasks += 1
        if not success:
            self.error_count += 1

        # Update average processing time
        current_avg = self.metrics['avg_processing_time']
        self.metrics['avg_processing_time'] = (
            (current_avg * (self.processed_tasks - 1) + processing_time) /
            self.processed_tasks
        )

        # Update success rate
        self.metrics['success_rate'] = (
            (self.processed_tasks - self.error_count) / self.processed_tasks
        )

        # Update counters
        self.metrics['tasks_processed'] = self.processed_tasks
        self.metrics['last_activity'] = datetime.now()

        # Store in memory
        self.memory.metrics = self.metrics

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'is_active': self.is_active,
            'session_id': self.session_id,
            'queue_size': len(self.task_queue),
            'processed_tasks': self.processed_tasks,
            'error_count': self.error_count,
            'metrics': self.metrics,
            'capabilities': self.get_agent_capabilities()
        }

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get agent memory summary for coordination"""
        return {
            'agent_id': self.agent_id,
            'session_id': self.session_id,
            'memory_keys': list(self.memory.memories.keys()),
            'memory_size': len(self.memory.memories),
            'last_updated': self.memory.last_updated.isoformat(),
            'metrics': self.memory.metrics
        }

    async def coordinate_with_agent(self, other_agent_id: str,
                                   message: str, data: Optional[Dict] = None) -> None:
        """Send coordination message to another agent"""
        try:
            coordination_data = {
                'from_agent': self.agent_id,
                'to_agent': other_agent_id,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'data': data or {}
            }

            await self._store_in_memory(f"coordination/{other_agent_id}", coordination_data)

            # Use Claude Flow for agent coordination
            await self._run_claude_flow_hook('notify', {
                'message': f"Coordination from {self.agent_id} to {other_agent_id}: {message}",
                'target_agent': other_agent_id
            })

        except Exception as e:
            logger.error(f"Agent coordination failed: {str(e)}")

    def clear_completed_tasks(self) -> int:
        """Clear completed tasks from queue and return count"""
        completed_count = 0
        remaining_tasks = []

        for task in self.task_queue:
            if task.status in ['completed', 'error']:
                completed_count += 1
            else:
                remaining_tasks.append(task)

        self.task_queue = remaining_tasks
        return completed_count

    async def health_check(self) -> Dict[str, Any]:
        """Perform agent health check"""
        return {
            'agent_id': self.agent_id,
            'healthy': self.is_active and self.error_count < 10,
            'error_rate': self.error_count / max(self.processed_tasks, 1),
            'last_activity': self.metrics['last_activity'].isoformat(),
            'queue_health': len(self.task_queue) < 100,  # Queue not overwhelmed
            'memory_health': len(self.memory.memories) < 1000  # Memory not bloated
        }


class AgentCoordinator:
    """Coordinates multiple agents using Claude Flow"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.active_sessions: Dict[str, str] = {}

    async def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the coordinator"""
        self.agents[agent.agent_id] = agent
        self.active_sessions[agent.agent_id] = agent.session_id
        await agent.start()
        logger.info(f"Registered agent {agent.agent_id}")

    async def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            await agent.stop()
            del self.agents[agent_id]
            if agent_id in self.active_sessions:
                del self.active_sessions[agent_id]
            logger.info(f"Unregistered agent {agent_id}")

    async def route_to_agent(self, parsed_email: ParsedEmail,
                           routing_decision: RoutingDecision) -> Optional[AgentResponse]:
        """Route email to appropriate agent based on routing decision"""
        # Find agent that can handle this email
        for agent in self.agents.values():
            if agent.validate_email_for_agent(parsed_email):
                return await agent.process_email(parsed_email, routing_decision)

        logger.warning(f"No agent found for email {parsed_email.id}")
        return None

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'total_agents': len(self.agents),
            'active_agents': sum(1 for agent in self.agents.values() if agent.is_active),
            'agents': {
                agent_id: agent.get_status()
                for agent_id, agent in self.agents.items()
            }
        }


# Utility functions
def create_agent_task(email_id: str, task_type: str, priority: str,
                     data: Dict[str, Any]) -> AgentTask:
    """Create a new agent task"""
    return AgentTask(
        id=f"task_{uuid.uuid4().hex[:8]}",
        email_id=email_id,
        task_type=task_type,
        priority=priority,
        data=data
    )


if __name__ == "__main__":
    # Test the base agent framework
    class TestAgent(BaseAgent):
        async def _process_email_impl(self, parsed_email, routing_decision, task):
            return AgentResponse(
                task_id=task.id,
                agent_id=self.agent_id,
                status="success",
                response_data={'test': 'processed'},
                auto_reply="Test response"
            )

        def get_agent_capabilities(self):
            return {'test': True}

        def validate_email_for_agent(self, parsed_email):
            return True

    async def test_agent():
        agent = TestAgent("test-001", "test_agent")
        print(f"Created agent: {agent.agent_id}")
        print(f"Status: {agent.get_status()}")

    asyncio.run(test_agent())