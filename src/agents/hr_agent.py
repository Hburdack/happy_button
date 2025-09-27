"""
HR Agent for Happy Buttons Release 2
Handles human resources, employee relations, recruitment, and workplace management
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .base_agent import BaseAgent, AgentResponse, AgentTask
from .agent_email_dispatcher import TaskTypes

try:
    from email_processing.parser import ParsedEmail
    from email_processing.router import RoutingDecision
except ImportError:
    from ..email_processing.parser import ParsedEmail
    from ..email_processing.router import RoutingDecision

logger = logging.getLogger(__name__)


class HRAgent(BaseAgent):
    """
    HR Agent - Handles hr@h-bu.de
    Manages employee relations, recruitment, compliance, and workplace issues
    """

    def __init__(self, agent_id: str = "hr-001"):
        super().__init__(agent_id, "hr_agent", {
            'employee_count': 45,
            'departments': ['Production', 'Logistics', 'Finance', 'Quality', 'Management', 'HR'],
            'working_hours': '08:00-17:00',
            'overtime_threshold': 40,  # hours per week
            'vacation_approval_threshold': 5,  # days requiring management approval
            'compliance_areas': ['GDPR', 'Labor Law', 'Safety Regulations'],
            'recruitment_active': True
        })
        self.employee_database = self._initialize_employee_database()

    def _initialize_employee_database(self):
        """Initialize simulated employee database"""
        return {
            'total_employees': self.config['employee_count'],
            'by_department': {
                'Production': 18,
                'Logistics': 8,
                'Finance': 5,
                'Quality': 4,
                'Management': 6,
                'HR': 4
            },
            'active_recruitments': 3,
            'pending_approvals': 7
        }

    async def _process_email_impl(self, parsed_email: ParsedEmail,
                                 routing_decision: RoutingDecision,
                                 task: AgentTask) -> AgentResponse:
        """Process HR-related emails"""

        hr_analysis = await self._analyze_hr_request(parsed_email)

        response_data = {
            'action': 'hr_processed',
            'request_type': hr_analysis['type'],
            'hr_analysis': hr_analysis['analysis'],
            'priority_level': hr_analysis['priority'],
            'compliance_check': hr_analysis.get('compliance_status', 'cleared')
        }

        coordination_notes = []

        # Handle different types of HR requests
        if hr_analysis['type'] == 'recruitment_request':
            recruitment_data = hr_analysis['recruitment_data']

            success = await self.send_task_email(
                to_agent='management_agent',
                task_type=TaskTypes.RECRUITMENT_APPROVAL,
                content=f"New Position Recruitment Request\n\nPosition: {recruitment_data['position_title']}\nDepartment: {recruitment_data['department']}\nUrgency: {recruitment_data['urgency']}\nJustification: {recruitment_data['justification']}\n\nBudget Impact:\n- Annual Salary Range: €{recruitment_data['salary_min']:,} - €{recruitment_data['salary_max']:,}\n- Total Cost (incl. benefits): €{recruitment_data['total_cost']:,}\n- Budget Availability: {recruitment_data['budget_status']}\n\nRecruitment Plan:\n- Posting Duration: {recruitment_data['posting_duration']} weeks\n- Interview Process: {recruitment_data['interview_process']}\n- Expected Start Date: {recruitment_data['start_date']}\n\nManager approval required to proceed with recruitment.",
                priority="high",
                data={
                    'position': recruitment_data['position_title'],
                    'department': recruitment_data['department'],
                    'budget_impact': recruitment_data['total_cost'],
                    'recruitment_priority': recruitment_data['urgency']
                },
                due_hours=24
            )
            if success:
                coordination_notes.append("Sent recruitment approval request to management")

        elif hr_analysis['type'] == 'employee_issue':
            issue_data = hr_analysis['issue_data']

            if issue_data['severity'] == 'critical':
                success = await self.send_task_email(
                    to_agent='management_agent',
                    task_type=TaskTypes.ESCALATION,
                    content=f"CRITICAL HR ISSUE - IMMEDIATE ATTENTION REQUIRED\n\nIssue Type: {issue_data['issue_type']}\nEmployee: {issue_data['employee_reference']}\nDepartment: {issue_data['department']}\nSeverity: {issue_data['severity']}\nReported: {issue_data['reported_date']}\n\nIssue Summary:\n{issue_data['issue_summary']}\n\nImmediate Actions Taken:\n{issue_data['immediate_actions']}\n\nLegal/Compliance Risk: {issue_data['compliance_risk']}\nRecommended Actions:\n{issue_data['recommended_actions']}\n\nThis issue requires immediate management intervention.",
                    priority="critical",
                    data={
                        'issue_type': issue_data['issue_type'],
                        'severity': issue_data['severity'],
                        'compliance_risk': issue_data['compliance_risk'],
                        'requires_immediate_action': True
                    },
                    due_hours=2
                )
                if success:
                    coordination_notes.append("Escalated critical HR issue to management")

        elif hr_analysis['type'] == 'time_off_request':
            time_off_data = hr_analysis['time_off_data']

            if time_off_data['requires_management_approval']:
                success = await self.send_task_email(
                    to_agent='management_agent',
                    task_type=TaskTypes.TIME_OFF_APPROVAL,
                    content=f"Extended Time Off Approval Required\n\nEmployee: {time_off_data['employee_reference']}\nDepartment: {time_off_data['department']}\nRequest Type: {time_off_data['request_type']}\nDuration: {time_off_data['duration']} days\nDates: {time_off_data['start_date']} to {time_off_data['end_date']}\n\nImpact Analysis:\n- Department Coverage: {time_off_data['coverage_status']}\n- Critical Projects Affected: {time_off_data['project_impact']}\n- Backup Arrangements: {time_off_data['backup_plan']}\n\nHR Recommendation: {time_off_data['hr_recommendation']}\n\nManagement approval required due to duration exceeding {self.config['vacation_approval_threshold']} days.",
                    priority="medium",
                    data={
                        'employee': time_off_data['employee_reference'],
                        'duration': time_off_data['duration'],
                        'department_impact': time_off_data['coverage_status']
                    },
                    due_hours=48
                )
                if success:
                    coordination_notes.append("Sent time-off approval request to management")

        elif hr_analysis['type'] == 'compliance_issue':
            compliance_data = hr_analysis['compliance_data']

            success = await self.send_task_email(
                to_agent='management_agent',
                task_type=TaskTypes.COMPLIANCE_ALERT,
                content=f"COMPLIANCE ISSUE DETECTED\n\nCompliance Area: {compliance_data['area']}\nSeverity: {compliance_data['severity']}\nDeadline: {compliance_data['deadline']}\nRegulatory Body: {compliance_data['regulatory_body']}\n\nIssue Description:\n{compliance_data['description']}\n\nRequired Actions:\n{compliance_data['required_actions']}\n\nRisk Assessment:\n- Financial Risk: €{compliance_data['financial_risk']:,}\n- Reputational Risk: {compliance_data['reputational_risk']}\n- Legal Risk: {compliance_data['legal_risk']}\n\nRecommended Timeline:\n{compliance_data['timeline']}",
                priority="high",
                data={
                    'compliance_area': compliance_data['area'],
                    'deadline': compliance_data['deadline'],
                    'risk_level': compliance_data['severity']
                },
                due_hours=4
            )
            if success:
                coordination_notes.append("Sent compliance alert to management")

        elif hr_analysis['type'] == 'training_request':
            training_data = hr_analysis['training_data']

            success = await self.send_task_email(
                to_agent='finance_agent',
                task_type=TaskTypes.TRAINING_BUDGET,
                content=f"Training Program Budget Approval\n\nProgram: {training_data['program_name']}\nParticipants: {training_data['participant_count']} employees\nDepartments: {training_data['departments']}\nTotal Cost: €{training_data['total_cost']:,}\n\nProgram Details:\n- Duration: {training_data['duration']}\n- Provider: {training_data['provider']}\n- Format: {training_data['format']}\n- Certification: {training_data['certification']}\n\nBusiness Justification:\n{training_data['justification']}\n\nExpected ROI:\n{training_data['expected_roi']}\n\nBudget approval requested for training expenditure.",
                priority="medium",
                data={
                    'training_cost': training_data['total_cost'],
                    'participant_count': training_data['participant_count'],
                    'department': training_data['departments']
                },
                due_hours=72
            )
            if success:
                coordination_notes.append("Sent training budget request to finance")

        # Determine auto-reply
        auto_reply = self._select_hr_reply(hr_analysis)

        return AgentResponse(
            task_id=task.id,
            agent_id=self.agent_id,
            status="success",
            response_data=response_data,
            auto_reply=auto_reply,
            next_actions=self._determine_hr_actions(hr_analysis),
            coordination_notes=coordination_notes
        )

    async def _analyze_hr_request(self, parsed_email: ParsedEmail) -> Dict[str, Any]:
        """Analyze HR request and determine type and requirements"""
        content = f"{parsed_email.subject} {parsed_email.body}".lower()

        # Determine request type
        if any(word in content for word in ['hiring', 'recruit', 'position', 'job', 'vacancy']):
            request_type = 'recruitment_request'
        elif any(word in content for word in ['complaint', 'harassment', 'discrimination', 'issue', 'problem']):
            request_type = 'employee_issue'
        elif any(word in content for word in ['vacation', 'time off', 'leave', 'absence', 'holiday']):
            request_type = 'time_off_request'
        elif any(word in content for word in ['compliance', 'regulation', 'audit', 'gdpr', 'legal']):
            request_type = 'compliance_issue'
        elif any(word in content for word in ['training', 'development', 'course', 'certification']):
            request_type = 'training_request'
        elif any(word in content for word in ['payroll', 'salary', 'benefits', 'compensation']):
            request_type = 'payroll_inquiry'
        else:
            request_type = 'general_inquiry'

        # Determine priority
        if any(word in content for word in ['urgent', 'emergency', 'critical', 'harassment', 'discrimination']):
            priority = 'critical'
        elif any(word in content for word in ['asap', 'important', 'deadline', 'compliance']):
            priority = 'high'
        else:
            priority = 'medium'

        # Base analysis
        analysis = {
            'type': request_type,
            'priority': priority,
            'requester': parsed_email.sender.email,
            'timestamp': datetime.now().isoformat()
        }

        # Add type-specific analysis
        if request_type == 'recruitment_request':
            analysis.update(self._analyze_recruitment_request(content))
        elif request_type == 'employee_issue':
            analysis.update(self._analyze_employee_issue(content))
        elif request_type == 'time_off_request':
            analysis.update(self._analyze_time_off_request(content))
        elif request_type == 'compliance_issue':
            analysis.update(self._analyze_compliance_issue(content))
        elif request_type == 'training_request':
            analysis.update(self._analyze_training_request(content))

        return analysis

    def _analyze_recruitment_request(self, content: str) -> Dict[str, Any]:
        """Analyze recruitment request"""
        # Extract position information
        position_keywords = {
            'production': 'Production Operator',
            'logistics': 'Logistics Coordinator',
            'finance': 'Finance Analyst',
            'quality': 'Quality Inspector',
            'manager': 'Department Manager',
            'engineer': 'Process Engineer'
        }

        position_title = 'General Position'
        department = 'General'
        for keyword, title in position_keywords.items():
            if keyword in content:
                position_title = title
                department = keyword.capitalize()
                break

        # Determine urgency
        urgency = 'high' if any(word in content for word in ['urgent', 'asap', 'immediate']) else 'medium'

        # Estimate salary range (simplified)
        salary_ranges = {
            'Production Operator': (35000, 45000),
            'Logistics Coordinator': (40000, 50000),
            'Finance Analyst': (45000, 55000),
            'Quality Inspector': (38000, 48000),
            'Department Manager': (60000, 80000),
            'Process Engineer': (50000, 65000),
            'General Position': (35000, 45000)
        }

        salary_min, salary_max = salary_ranges.get(position_title, (35000, 45000))
        total_cost = int(salary_max * 1.3)  # Include benefits and overhead

        recruitment_data = {
            'position_title': position_title,
            'department': department,
            'urgency': urgency,
            'justification': f'Department request for {position_title} position',
            'salary_min': salary_min,
            'salary_max': salary_max,
            'total_cost': total_cost,
            'budget_status': 'Available' if total_cost < 60000 else 'Requires approval',
            'posting_duration': 2 if urgency == 'high' else 3,
            'interview_process': 'Phone screening + 2 in-person interviews',
            'start_date': (datetime.now() + timedelta(weeks=6)).date().isoformat()
        }

        return {
            'analysis': f'Recruitment request for {position_title} in {department} department',
            'recruitment_data': recruitment_data,
            'compliance_status': 'cleared'
        }

    def _analyze_employee_issue(self, content: str) -> Dict[str, Any]:
        """Analyze employee issue"""
        # Determine issue type and severity
        if any(word in content for word in ['harassment', 'discrimination', 'bullying']):
            issue_type = 'Workplace Harassment/Discrimination'
            severity = 'critical'
            compliance_risk = 'high'
        elif any(word in content for word in ['safety', 'accident', 'injury']):
            issue_type = 'Workplace Safety'
            severity = 'high'
            compliance_risk = 'medium'
        elif any(word in content for word in ['performance', 'productivity', 'attendance']):
            issue_type = 'Performance Management'
            severity = 'medium'
            compliance_risk = 'low'
        else:
            issue_type = 'General Employee Concern'
            severity = 'medium'
            compliance_risk = 'low'

        # Generate employee reference (anonymized)
        employee_reference = f"EMP-{datetime.now().strftime('%Y%m%d')}-{hash(content) % 1000:03d}"

        # Determine department (simplified)
        department = 'Production'  # Default
        for dept in self.config['departments']:
            if dept.lower() in content:
                department = dept
                break

        immediate_actions = self._generate_immediate_actions(issue_type, severity)
        recommended_actions = self._generate_recommended_actions(issue_type, severity)

        issue_data = {
            'issue_type': issue_type,
            'severity': severity,
            'employee_reference': employee_reference,
            'department': department,
            'reported_date': datetime.now().date().isoformat(),
            'issue_summary': f'{issue_type} reported in {department} department',
            'immediate_actions': immediate_actions,
            'compliance_risk': compliance_risk,
            'recommended_actions': recommended_actions
        }

        return {
            'analysis': f'{issue_type} - {severity} severity',
            'issue_data': issue_data,
            'compliance_status': 'investigation_required' if severity == 'critical' else 'monitoring'
        }

    def _analyze_time_off_request(self, content: str) -> Dict[str, Any]:
        """Analyze time off request"""
        # Extract duration information
        duration_match = re.search(r'(\d+)\s*(?:days?|weeks?)', content)
        if duration_match:
            duration = int(duration_match.group(1))
            if 'week' in duration_match.group(0):
                duration *= 5  # Convert weeks to days
        else:
            duration = 5  # Default assumption

        # Determine request type
        if any(word in content for word in ['vacation', 'holiday']):
            request_type = 'Annual Leave'
        elif any(word in content for word in ['sick', 'medical']):
            request_type = 'Sick Leave'
        elif any(word in content for word in ['personal', 'emergency']):
            request_type = 'Personal Leave'
        else:
            request_type = 'General Leave'

        # Generate dates
        start_date = (datetime.now() + timedelta(weeks=2)).date()
        end_date = start_date + timedelta(days=duration-1)

        # Determine if management approval required
        requires_management = duration > self.config['vacation_approval_threshold']

        # Simulate impact analysis
        department = 'Production'  # Simplified
        coverage_status = 'Adequate backup available' if duration <= 5 else 'Coverage challenges expected'
        project_impact = 'Minimal impact' if duration <= 3 else 'Some project delays possible'
        backup_plan = 'Cross-training colleague available' if duration <= 7 else 'Temporary replacement needed'

        hr_recommendation = 'Approve' if duration <= 10 else 'Approve with conditions'

        time_off_data = {
            'request_type': request_type,
            'duration': duration,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'requires_management_approval': requires_management,
            'employee_reference': f"EMP-{hash(content) % 1000:03d}",
            'department': department,
            'coverage_status': coverage_status,
            'project_impact': project_impact,
            'backup_plan': backup_plan,
            'hr_recommendation': hr_recommendation
        }

        return {
            'analysis': f'{request_type} request for {duration} days',
            'time_off_data': time_off_data,
            'compliance_status': 'policy_compliant'
        }

    def _analyze_compliance_issue(self, content: str) -> Dict[str, Any]:
        """Analyze compliance issue"""
        # Determine compliance area
        if 'gdpr' in content or 'data' in content:
            area = 'GDPR/Data Protection'
            regulatory_body = 'Data Protection Authority'
            financial_risk = 20000000  # Max GDPR fine
        elif 'safety' in content or 'health' in content:
            area = 'Workplace Safety'
            regulatory_body = 'Occupational Safety Authority'
            financial_risk = 50000
        elif 'labor' in content or 'employment' in content:
            area = 'Labor Law'
            regulatory_body = 'Labor Relations Board'
            financial_risk = 25000
        else:
            area = 'General Compliance'
            regulatory_body = 'Regulatory Authority'
            financial_risk = 10000

        # Determine severity and timeline
        if any(word in content for word in ['audit', 'investigation', 'violation']):
            severity = 'critical'
            deadline = (datetime.now() + timedelta(days=7)).date().isoformat()
        elif any(word in content for word in ['review', 'update', 'policy']):
            severity = 'medium'
            deadline = (datetime.now() + timedelta(days=30)).date().isoformat()
        else:
            severity = 'low'
            deadline = (datetime.now() + timedelta(days=60)).date().isoformat()

        required_actions = self._generate_compliance_actions(area, severity)
        timeline = self._generate_compliance_timeline(severity)

        compliance_data = {
            'area': area,
            'severity': severity,
            'deadline': deadline,
            'regulatory_body': regulatory_body,
            'description': f'{area} compliance issue requiring attention',
            'required_actions': required_actions,
            'financial_risk': financial_risk,
            'reputational_risk': 'high' if severity == 'critical' else 'medium',
            'legal_risk': 'high' if severity == 'critical' else 'low',
            'timeline': timeline
        }

        return {
            'analysis': f'{area} compliance issue - {severity} severity',
            'compliance_data': compliance_data,
            'compliance_status': 'action_required'
        }

    def _analyze_training_request(self, content: str) -> Dict[str, Any]:
        """Analyze training request"""
        # Determine training type
        if 'safety' in content:
            program_name = 'Workplace Safety Certification'
            cost_per_person = 500
        elif 'quality' in content:
            program_name = 'Quality Management Training'
            cost_per_person = 750
        elif 'leadership' in content or 'management' in content:
            program_name = 'Leadership Development Program'
            cost_per_person = 1200
        else:
            program_name = 'Professional Development Training'
            cost_per_person = 600

        # Estimate participants
        participant_match = re.search(r'(\d+)\s*(?:people|employees|participants)', content)
        participant_count = int(participant_match.group(1)) if participant_match else 5

        total_cost = participant_count * cost_per_person

        training_data = {
            'program_name': program_name,
            'participant_count': participant_count,
            'departments': 'Multiple departments',
            'total_cost': total_cost,
            'duration': '2 days',
            'provider': 'Professional Training Institute',
            'format': 'In-person workshop',
            'certification': 'Yes',
            'justification': f'Skills development for {participant_count} employees in {program_name}',
            'expected_roi': 'Improved productivity and compliance, reduced errors'
        }

        return {
            'analysis': f'Training request: {program_name} for {participant_count} participants',
            'training_data': training_data,
            'compliance_status': 'budget_approval_required'
        }

    def _generate_immediate_actions(self, issue_type: str, severity: str) -> str:
        """Generate immediate actions for employee issues"""
        if severity == 'critical':
            if 'Harassment' in issue_type:
                return '- Separate parties immediately\n- Document all details\n- Initiate formal investigation\n- Notify legal counsel'
            elif 'Safety' in issue_type:
                return '- Secure accident scene\n- Provide medical attention\n- Document incident\n- Report to authorities'
        else:
            return '- Document complaint\n- Schedule meeting with employee\n- Review relevant policies\n- Begin informal investigation'

    def _generate_recommended_actions(self, issue_type: str, severity: str) -> str:
        """Generate recommended actions for employee issues"""
        if severity == 'critical':
            return '- Formal investigation by external party\n- Potential disciplinary action\n- Policy review and training\n- Legal consultation'
        else:
            return '- Manager coaching\n- Performance improvement plan\n- Additional training\n- Regular follow-up meetings'

    def _generate_compliance_actions(self, area: str, severity: str) -> str:
        """Generate compliance actions"""
        actions = {
            'GDPR/Data Protection': '- Review data processing activities\n- Update privacy policies\n- Conduct staff training\n- Implement technical safeguards',
            'Workplace Safety': '- Conduct safety audit\n- Update safety procedures\n- Provide safety training\n- Review incident reports',
            'Labor Law': '- Review employment contracts\n- Update HR policies\n- Conduct compliance training\n- Audit timekeeping practices'
        }
        return actions.get(area, '- Conduct compliance review\n- Update relevant policies\n- Provide staff training\n- Document corrective actions')

    def _generate_compliance_timeline(self, severity: str) -> str:
        """Generate compliance timeline"""
        if severity == 'critical':
            return '- Week 1: Immediate assessment and documentation\n- Week 2: Implement corrective actions\n- Week 3: Review and validate compliance\n- Week 4: Final reporting and closure'
        else:
            return '- Month 1: Assessment and planning\n- Month 2: Implementation of changes\n- Month 3: Training and communication\n- Month 4: Review and validation'

    def _select_hr_reply(self, analysis: Dict) -> str:
        """Select appropriate auto-reply template"""
        if analysis['type'] == 'recruitment_request':
            return 'hr_recruitment_ack'
        elif analysis['type'] == 'employee_issue':
            return 'hr_issue_ack'
        elif analysis['type'] == 'time_off_request':
            return 'hr_timeoff_ack'
        elif analysis['type'] == 'compliance_issue':
            return 'hr_compliance_ack'
        elif analysis['type'] == 'training_request':
            return 'hr_training_ack'
        else:
            return 'hr_ack'

    def _determine_hr_actions(self, analysis: Dict) -> List[str]:
        """Determine next actions based on HR analysis"""
        actions = []

        if analysis['type'] == 'recruitment_request':
            actions.extend([
                "Submit recruitment approval request",
                "Prepare job description and posting",
                "Coordinate with hiring manager"
            ])
        elif analysis['type'] == 'employee_issue':
            if analysis['priority'] == 'critical':
                actions.extend([
                    "Initiate immediate investigation",
                    "Document all evidence",
                    "Ensure employee safety"
                ])
            else:
                actions.extend([
                    "Schedule employee meeting",
                    "Review relevant policies",
                    "Develop action plan"
                ])
        elif analysis['type'] == 'time_off_request':
            if analysis['time_off_data']['requires_management_approval']:
                actions.extend([
                    "Submit approval request to management",
                    "Coordinate coverage arrangements",
                    "Update leave tracking system"
                ])
            else:
                actions.extend([
                    "Approve time off request",
                    "Update leave balance",
                    "Notify department manager"
                ])
        elif analysis['type'] == 'compliance_issue':
            actions.extend([
                "Assess compliance requirements",
                "Develop corrective action plan",
                "Schedule compliance training"
            ])
        elif analysis['type'] == 'training_request':
            actions.extend([
                "Submit budget approval request",
                "Research training providers",
                "Coordinate scheduling with departments"
            ])

        # Common actions
        actions.append("Update HR records")
        if analysis['priority'] == 'critical':
            actions.append("Monitor situation closely")

        return actions

    def get_agent_capabilities(self) -> Dict[str, Any]:
        return {
            'recruitment_management': True,
            'employee_relations': True,
            'compliance_monitoring': True,
            'training_coordination': True,
            'time_off_management': True,
            'policy_administration': True,
            'incident_management': True,
            'employee_count': self.config['employee_count'],
            'departments': self.config['departments'],
            'compliance_areas': self.config['compliance_areas'],
            'vacation_approval_threshold': self.config['vacation_approval_threshold']
        }

    def validate_email_for_agent(self, parsed_email: ParsedEmail) -> bool:
        content = f"{parsed_email.subject} {parsed_email.body}".lower()
        hr_keywords = [
            'hr', 'human resources', 'employee', 'recruitment', 'hiring',
            'vacation', 'leave', 'training', 'compliance', 'harassment',
            'safety', 'payroll', 'benefits'
        ]
        return any(keyword in content for keyword in hr_keywords)


if __name__ == "__main__":
    # Test the HR agent
    async def test_hr_agent():
        agent = HRAgent()
        print(f"HR Agent: {agent.agent_id}")
        print(f"Capabilities: {agent.get_agent_capabilities()}")

    asyncio.run(test_hr_agent())