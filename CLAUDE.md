# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Happy Buttons Agentic Simulation System** - An advanced email processing and business automation system featuring:

- **Multi-agent architecture** with Claude Flow integration
- **Real-time web dashboard** with full-stack Flask/Bootstrap interface
- **Python-based email processing pipeline** with intelligent routing
- **Business intelligence KPI tracking** and analytics
- **E-commerce integration** with cart and checkout functionality
- **Royal courtesy communication** templates and validation

This is a production-ready system demonstrating AI-powered business process automation with comprehensive testing and monitoring.

## Development Commands

### Core Operations
```bash
# Run email processing demo
cd src && python main.py

# Start web dashboard (port 80)
cd dashboard && python app.py

# Start background email service (port 8081)
python src/service.py

# Run comprehensive test suite
python -m pytest tests/ -v

# Build project (placeholder)
npm run build

# Run development mode
npm run dev
```

### Testing Commands
```bash
# Run all tests with verbose output
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_email_system.py::TestEmailParser -v
python -m pytest tests/test_email_system.py::TestEmailRouter -v
python -m pytest tests/test_email_system.py::TestBusinessAgents -v

# Generate test coverage reports
python -m pytest tests/ --cov=src --cov-report=html
```

### System Monitoring
```bash
# Check service health
curl http://localhost:8081/health

# View detailed system stats
curl http://localhost:8081/stats

# Monitor metrics (Prometheus format)
curl http://localhost:8081/metrics
```

## Architecture Overview

### Core System Components

#### 1. Email Processing Pipeline (`src/email_processing/`)
- **Parser** (`parser.py`): Advanced email parsing with PDF attachment support, OEM detection, urgency classification
- **Router** (`router.py`): Intelligent routing with 10+ rules, SLA calculation, escalation management

#### 2. Multi-Agent System (`src/agents/`)
- **BaseAgent** (`base_agent.py`): Abstract base with Claude Flow integration, memory persistence, coordination hooks
- **Business Agents** (`business_agents.py`): 6 specialized agents (Info, Orders, OEM, Supplier, Quality, Management)
- **Agent Coordinator**: Orchestrates multi-agent workflows with task distribution

#### 3. Web Dashboard System (`dashboard/`)
- **Flask Application** (`app.py`): Full-featured web server with WebSocket support
- **Real-time Interface**: Live email processing feed, agent monitoring, KPI analytics
- **E-commerce Module**: Product catalog, cart management, secure checkout
- **Business Intelligence**: Interactive charts, performance metrics, optimization recommendations

#### 4. Template & Communication System (`src/utils/`)
- **Royal Courtesy Templates** (`templates.py`): 9 professional templates with Jinja2 rendering
- **Template Validation**: Royal courtesy scoring system (60+ points required)
- **Order Processing** (`order_email.py`): Automated order confirmation generation

### Technology Stack

- **Backend**: Python 3.8+ with asyncio, Flask, FastAPI, SQLAlchemy
- **Frontend**: Bootstrap 5, Chart.js, WebSockets
- **Email Processing**: Built-in email library, PyPDF2 for attachments
- **Document Processing**: python-docx, reportlab for PDF generation
- **Coordination**: Claude Flow MCP integration for agent orchestration
- **Database**: SQLite with better-sqlite3 via Node.js bindings
- **Testing**: pytest with asyncio support and coverage reporting
- **Code Quality**: black (formatting), flake8 (linting), mypy (type checking)

## Configuration System

### Business Configuration (`config/company.yaml`)
- SLA definitions: 2h (critical), 4h (OEM), 12h (default), 24h (expedite)
- 10 specialized email routing destinations
- Priority escalation rules and thresholds
- OEM customer domain definitions

### Agent Configuration (`config/units/`)
- Individual agent capabilities and specializations
- Processing thresholds and validation rules
- Coordination patterns and memory keys

### Email Settings (`config/email_settings.yaml`)
- Routing rules and keyword matching
- Auto-reply template assignments
- KPI targets and monitoring thresholds

## Claude Flow Integration

This project uses **Claude Flow MCP integration** for advanced agent coordination:

### Agent Coordination Protocol
Every spawned agent follows the coordination lifecycle:

1. **Pre-task**: `npx claude-flow@alpha hooks pre-task --description "[task]"`
2. **Session Restore**: `npx claude-flow@alpha hooks session-restore --session-id "swarm-[id]"`
3. **Processing**: Agent executes with memory coordination and progress tracking
4. **Post-edit**: `npx claude-flow@alpha hooks post-edit --file "[file]" --memory-key "swarm/[agent]/[step]"`
5. **Post-task**: `npx claude-flow@alpha hooks post-task --task-id "[task]"`

### Memory & State Management
- **Cross-session persistence**: Agents maintain state across restarts
- **Shared memory**: Coordination data stored in `.swarm/memory/`
- **Performance metrics**: Real-time tracking of processing times and success rates

### Configuration (`claude-flow.config.json`)
```json
{
  "features": {
    "autoTopologySelection": true,
    "parallelExecution": true,
    "neuralTraining": true,
    "bottleneckAnalysis": true,
    "smartAutoSpawning": true,
    "selfHealingWorkflows": true,
    "crossSessionMemory": true,
    "githubIntegration": true
  },
  "performance": {
    "maxAgents": 10,
    "defaultTopology": "hierarchical",
    "executionStrategy": "parallel",
    "tokenOptimization": true,
    "cacheEnabled": true,
    "telemetryLevel": "detailed"
  }
}
```

## Development Patterns

### Working with Agents
```python
# Create and coordinate agents
from agents.business_agents import create_business_agents
from agents.base_agent import AgentCoordinator

coordinator = AgentCoordinator()
agents = create_business_agents()

# Process emails through agent pipeline
for agent_name, agent in agents.items():
    await coordinator.register_agent(agent)

result = await coordinator.route_to_agent(parsed_email, routing_decision)
```

### Adding New Business Logic
1. **Email Categories**: Extend keywords in `EmailParser.keywords`
2. **Routing Rules**: Add rules in `EmailRouter.routing_rules`
3. **Templates**: Create new templates in `templates/replies/`
4. **Agents**: Implement new agents inheriting from `BaseAgent`

### Dashboard Development
```python
# Add new dashboard endpoints
@app.route('/api/new-feature')
def new_feature_api():
    # Business logic here
    return jsonify(data)

# Real-time updates via WebSocket
@socketio.on('request_update')
def handle_update():
    emit('data_update', get_latest_data())
```

## Testing Strategy

### Test Structure (`tests/test_email_system.py`)
- **Email Parser Tests**: OEM detection, urgency classification, category determination
- **Router Tests**: Routing logic, priority handling, escalation scenarios
- **Agent Tests**: Individual agent capabilities and coordination
- **Template Tests**: Royal courtesy validation and generation
- **Integration Tests**: Complete email processing workflows
- **Performance Tests**: System metrics and bottleneck analysis

### Test Data Management
- Use `create_test_email()` for consistent test email generation
- Mock external dependencies (SMTP, file system) in unit tests
- PDF generators in `pdf_generator.py` for reproducible test documents

## Performance & Monitoring

### Key Metrics Tracked
- **Auto-handling rate**: Target ≥70% of emails processed without human intervention
- **Average response time**: Target ≤1 hour for email acknowledgment
- **On-time shipping**: Target ≥90% of orders shipped within SLA
- **Escalation rate**: Target ≤15% of emails requiring management review

### System Health Endpoints
- `GET /health`: Basic service health status
- `GET /stats`: Detailed system metrics and agent status
- `GET /metrics`: Prometheus-compatible metrics for monitoring

### Performance Optimizations
- Async/await patterns throughout the codebase
- Memory-efficient email parsing with streaming
- Database connection pooling and query optimization
- WebSocket for real-time dashboard updates without polling

## Common Troubleshooting

### Import Issues
The project uses a custom `email_processing` package that can conflict with Python's built-in `email` module. All imports use absolute paths from the `src` directory.

### Dependencies
Install all required packages:
```bash
pip install -r requirements.txt
```

Key packages include:
- Flask, FastAPI, uvicorn (web servers)
- PyPDF2, python-docx (document processing)
- PyYAML, Jinja2 (configuration and templates)
- pytest, pytest-asyncio, pytest-cov (testing)
- black, flake8, mypy (code quality)
- reportlab (PDF generation)
- flask-socketio (real-time features)

### Port Conflicts
- Dashboard runs on port 80 (requires sudo on Linux)
- Health service runs on port 8081
- Use `sudo python dashboard/app.py` if needed for port 80 access

## Security Considerations

- No hardcoded secrets or API keys in codebase
- Email content sanitization and XSS prevention
- Input validation for all user-facing endpoints
- Audit trails for all agent actions and business decisions
- Royal courtesy template validation prevents inappropriate automated responses

## Code Style Guidelines

- **Modular Design**: Keep files under 500 lines where possible
- **Async First**: Use async/await for I/O operations
- **Type Hints**: Include type annotations for function signatures
- **Error Handling**: Comprehensive try/catch with detailed logging
- **Documentation**: Docstrings for all public methods and classes
- **Testing**: Write tests before implementing new features
- **Code Quality Tools**:
  - `black` for code formatting
  - `flake8` for linting
  - `mypy` for type checking
  - `pytest-cov` for test coverage

---

**Note**: This system demonstrates production-ready AI agent coordination with comprehensive business process automation. The architecture supports horizontal scaling and can be extended with additional business units and processing capabilities.