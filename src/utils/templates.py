"""
Royal Courtesy Templates System for Happy Buttons - Python Implementation
Implements elegant, courteous communication style with Jinja2 templating
"""

import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound
import logging

logger = logging.getLogger(__name__)


class RoyalCourtesyTemplates:
    """
    Royal Courtesy Templates System for Happy Buttons
    Implements elegant, courteous communication style
    """

    def __init__(self, templates_path: Optional[Path] = None):
        self.templates_path = templates_path or Path('templates/replies')
        self.templates: Dict[str, str] = {}
        self.jinja_env = None
        self.company_signature = self._get_company_signature()

        # Template validation patterns
        self.royal_patterns = {
            'greetings': [
                r'dear\s+\w+',
                r'esteemed\s+\w+',
                r'valued\s+\w+',
                r'distinguished\s+\w+'
            ],
            'courtesy_language': [
                r'most\s+(delighted|grateful|pleased)',
                r'with\s+the\s+(greatest|utmost)',
                r'we\s+are\s+honoured',
                r'kindly\s+note'
            ],
            'formal_commitments': [
                r'shall\s+\w+',
                r'endeavour\s+to',
                r'strive\s+to',
                r'committed\s+to'
            ]
        }

        self._initialize_templates()

    def _initialize_templates(self) -> None:
        """Initialize templates from files or defaults"""
        try:
            if self.templates_path.exists():
                self._load_templates_from_files()
            else:
                self._initialize_default_templates()

            # Setup Jinja2 environment
            if self.templates_path.exists():
                self.jinja_env = Environment(
                    loader=FileSystemLoader(self.templates_path),
                    trim_blocks=True,
                    lstrip_blocks=True
                )

            logger.info(f"Initialized {len(self.templates)} royal courtesy templates")

        except Exception as e:
            logger.error(f"Template initialization failed: {str(e)}")
            self._initialize_default_templates()

    def _load_templates_from_files(self) -> None:
        """Load templates from template files"""
        try:
            for template_file in self.templates_path.glob('*.txt'):
                template_name = template_file.stem
                with open(template_file, 'r', encoding='utf-8') as f:
                    self.templates[template_name] = f.read()

            if not self.templates:
                self._initialize_default_templates()

        except Exception as e:
            logger.error(f"Failed to load templates from files: {str(e)}")
            self._initialize_default_templates()

    def _initialize_default_templates(self) -> None:
        """Initialize default Royal Courtesy templates"""
        self.templates = {
            'order_received': """Dear {{ customer_name | default('Esteemed Customer') }},

We are most delighted to confirm receipt of your gracious order and extend our heartfelt gratitude for choosing Happy Buttons GmbH as your trusted partner.

Your order has been received with the utmost care and shall be processed with our characteristic attention to detail. We shall endeavour to fulfill your requirements with the highest standards of excellence that have distinguished our service for years.

A member of our dedicated team shall contact you most promptly with order confirmation details and anticipated delivery schedule.

We remain at your distinguished service and look forward to exceeding your expectations.

{{ signature }}""",

            'generic_ack': """Dear {{ customer_name | default('Valued Correspondent') }},

Kindly note that we have received your esteemed communication and are most grateful for the trust you have placed in Happy Buttons GmbH.

Your message has been assigned to our most capable team members who shall review your requirements with the greatest attention and respond most promptly within our service commitment timeframe.

Should you require any immediate assistance, please do not hesitate to contact us directly, and we shall be delighted to serve you.

{{ signature }}""",

            'invoice_received': """Dear Esteemed Partner,

We gratefully acknowledge receipt of your invoice and extend our appreciation for your continued partnership with Happy Buttons GmbH.

Your invoice shall be processed forthwith through our accounts department with the care and attention it deserves. We shall ensure prompt processing in accordance with our agreed terms.

Should any clarification be required, our finance team shall reach out to you directly.

{{ signature }}""",

            'expedite_ack': """Dear {{ customer_name | default('Distinguished Customer') }},

We are honoured that you have selected Happy Buttons GmbH for your urgent requirements and deeply appreciate the confidence you have placed in our capabilities.

Your expedited request has been prioritised with immediate effect, and our team shall strive diligently to fulfil your needs within the accelerated timeframe of {{ urgent_hours | default('24') }} hours.

You may rest assured that despite the expedited nature of your request, we shall maintain the exemplary quality standards for which Happy Buttons is renowned.

We shall keep you informed of our progress and notify you immediately upon completion.

{{ signature }}""",

            'oem_priority_ack': """Dear {{ customer_name | default('Esteemed OEM Partner') }},

We are honoured to receive your communication and deeply value our prestigious partnership with your distinguished organization.

As one of our premier OEM partners, your request has been assigned the highest priority status and shall receive immediate attention from our specialized OEM support team.

Our dedicated account manager shall personally oversee your requirements and contact you within 2 hours to discuss your needs in detail.

We remain committed to providing you with the exceptional service that has made our partnership so successful.

{{ signature }}""",

            'complaint_ack': """Dear Valued Customer,

We have received your communication regarding your recent experience, and we are deeply concerned that our service has not met the exceptional standards you rightfully expect from Happy Buttons GmbH.

Please accept our sincere apologies for any inconvenience caused. Your concerns are of the utmost importance to us, and we are committed to resolving this matter to your complete satisfaction.

A senior member of our customer care team shall personally review your case and contact you within 2 hours to discuss a suitable resolution.

We value your relationship immensely and appreciate the opportunity to make this right.

{{ signature }}""",

            'quality_ack': """Dear Esteemed Customer,

We have received your communication regarding product quality, and we are profoundly concerned that our products have not met the exacting standards of excellence for which Happy Buttons GmbH is renowned.

Your feedback is invaluable to us, and we shall investigate this matter immediately with our quality assurance team. We are committed to understanding the root cause and implementing corrective measures.

Our quality manager shall personally contact you within 4 hours to discuss the specifics of your experience and determine the most appropriate course of action.

We stand firmly behind the quality of our products and shall ensure your complete satisfaction.

{{ signature }}""",

            'supplier_ack': """Dear Valued Supply Partner,

We gratefully acknowledge receipt of your communication and extend our appreciation for your continued partnership in our supply chain excellence.

Your message has been forwarded to our procurement team who shall review your submission with due diligence and respond appropriately within our standard processing timeframe.

We value our collaborative relationship and look forward to continued success together.

{{ signature }}""",

            'hr_ack': """Dear Prospective Colleague,

We are delighted to receive your inquiry regarding opportunities with Happy Buttons GmbH and are grateful for your interest in joining our distinguished team.

Your communication has been forwarded to our Human Resources department, who shall review your credentials with the attention they deserve and respond within 5 business days.

We appreciate your interest in our organization and wish you success in your career endeavours.

{{ signature }}""",

            'out_of_hours': """Dear Esteemed Customer,

We have received your valued communication outside our regular business hours and are most grateful for your patience.

Your message shall receive our immediate attention when our offices reopen at 8:00 AM, and you may expect our response within our standard service timeframe.

For urgent matters requiring immediate assistance, please contact our emergency service line, and we shall be delighted to assist you.

{{ signature }}"""
        }

    def generate_response(self, template_name: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate email response using appropriate template

        Args:
            template_name: Name of template to use
            context: Context data for template variables

        Returns:
            Dict containing generated email with subject and body
        """
        try:
            if template_name not in self.templates:
                raise ValueError(f"Template '{template_name}' not found")

            # Prepare context
            template_context = {
                'signature': self.company_signature,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                **(context or {})
            }

            # Get template content
            template_content = self.templates[template_name]

            # Render with Jinja2 if available, otherwise simple replacement
            if self.jinja_env:
                try:
                    template = self.jinja_env.from_string(template_content)
                    body = template.render(**template_context)
                except Exception as jinja_error:
                    logger.warning(f"Jinja2 rendering failed, using simple replacement: {str(jinja_error)}")
                    body = self._simple_template_render(template_content, template_context)
            else:
                body = self._simple_template_render(template_content, template_context)

            # Generate subject
            subject = self._generate_subject(template_name, template_context)

            return {
                'subject': subject,
                'body': body,
                'template_used': template_name,
                'timestamp': datetime.now().isoformat(),
                'style': 'royal_courtesy',
                'validation': self.validate_royal_courtesy(body)
            }

        except Exception as e:
            logger.error(f"Template generation failed: {str(e)}")
            return self._generate_error_response(str(e), context)

    def _simple_template_render(self, template: str, context: Dict[str, Any]) -> str:
        """Simple template rendering for fallback"""
        rendered = template

        for key, value in context.items():
            placeholder = f"{{{{ {key} }}}}"
            rendered = rendered.replace(placeholder, str(value))

        # Handle default values
        rendered = re.sub(r'\{\{\s*(\w+)\s*\|\s*default\([\'"]([^\'"]*)[\'"\]\s*\}\}',
                         r'\2', rendered)

        return rendered

    def _generate_subject(self, template_name: str, context: Dict[str, Any]) -> str:
        """Generate appropriate subject line"""
        subjects = {
            'order_received': 'Re: Order Confirmation - Thank You for Your Trust',
            'generic_ack': 'Re: Your Inquiry - We Are Delighted to Assist',
            'invoice_received': 'Re: Invoice Acknowledgment - Processing with Care',
            'expedite_ack': 'Re: Urgent Request - Priority Processing Initiated',
            'oem_priority_ack': 'Re: OEM Priority Request - Immediate Attention',
            'complaint_ack': 'Re: Your Concerns - Our Immediate Attention',
            'quality_ack': 'Re: Quality Matter - Our Personal Commitment',
            'supplier_ack': 'Re: Supply Partnership - Valued Communication',
            'hr_ack': 'Re: Career Opportunity - Interest Appreciated',
            'out_of_hours': 'Re: Your Message - We Shall Respond Promptly'
        }

        base_subject = subjects.get(template_name, 'Re: Your Communication - Happy Buttons GmbH')

        # Customize with context
        if context.get('order_number'):
            base_subject = base_subject.replace('Order Confirmation',
                                              f"Order #{context['order_number']} Confirmation")

        if context.get('invoice_number'):
            base_subject = base_subject.replace('Invoice Acknowledgment',
                                              f"Invoice #{context['invoice_number']} Acknowledgment")

        return base_subject

    def _get_company_signature(self) -> str:
        """Get company signature"""
        return """With the greatest pleasure,

The Happy Buttons Service Team
Happy Buttons GmbH
Email: info@h-bu.de
Web: www.h-bu.de

"We are most delighted to serve you.\""""

    def validate_royal_courtesy(self, content: str) -> Dict[str, Any]:
        """
        Validate content for royal courtesy standards

        Args:
            content: Content to validate

        Returns:
            Dict with validation results
        """
        validation = {
            'is_valid': True,
            'score': 0,
            'max_score': 100,
            'issues': [],
            'suggestions': []
        }

        content_lower = content.lower()

        # Check for required royal courtesy elements
        for category, patterns in self.royal_patterns.items():
            category_score = 0
            category_weight = {'greetings': 25, 'courtesy_language': 35, 'formal_commitments': 40}

            for pattern in patterns:
                if re.search(pattern, content_lower):
                    category_score = category_weight.get(category, 10)
                    break

            if category_score == 0:
                validation['issues'].append(f"Missing {category.replace('_', ' ')}")
                validation['suggestions'].append(f"Add {category.replace('_', ' ')} elements")

            validation['score'] += category_score

        # Check for inappropriate casual language
        casual_patterns = [
            (r'\b(hi|hey|thanks|ok|okay)\b', 'Casual greetings/language'),
            (r'!{2,}', 'Excessive exclamation marks'),
            (r'\?{2,}', 'Multiple question marks'),
            (r'[A-Z]{3,}', 'Excessive capitalization')
        ]

        for pattern, issue in casual_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                validation['issues'].append(issue)
                validation['score'] -= 10

        # Final validation
        validation['is_valid'] = validation['score'] >= 60 and len(validation['issues']) <= 2
        validation['score'] = max(0, min(100, validation['score']))

        return validation

    def _generate_error_response(self, error: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate error response for template failures"""
        return {
            'subject': 'Re: Your Communication - Happy Buttons GmbH',
            'body': f"""Dear Esteemed Customer,

We have received your valued communication and are most grateful for your correspondence.

Due to a temporary system consideration, we shall personally review your message and respond most promptly within our standard timeframe.

We appreciate your patience and understanding.

{self.company_signature}""",
            'template_used': 'error_fallback',
            'timestamp': datetime.now().isoformat(),
            'style': 'royal_courtesy',
            'error': error,
            'validation': {'is_valid': True, 'score': 85, 'issues': [], 'suggestions': []}
        }

    def get_available_templates(self) -> List[str]:
        """Get list of available template names"""
        return list(self.templates.keys())

    def add_template(self, name: str, content: str) -> None:
        """Add or update a template"""
        self.templates[name] = content
        logger.info(f"Added/updated template: {name}")

    def save_templates(self) -> None:
        """Save templates to files"""
        try:
            self.templates_path.mkdir(parents=True, exist_ok=True)

            for name, content in self.templates.items():
                template_file = self.templates_path / f"{name}.txt"
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(content)

            logger.info(f"Saved {len(self.templates)} templates to {self.templates_path}")

        except Exception as e:
            logger.error(f"Failed to save templates: {str(e)}")

    def test_template(self, template_name: str, test_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Test template generation with sample context"""
        if not test_context:
            test_context = {
                'customer_name': 'Mr. Smith',
                'order_number': '12345',
                'invoice_number': 'INV-678',
                'company_name': 'Test Company Ltd',
                'urgent_hours': '4',
                'issue_details': 'button quality'
            }

        try:
            result = self.generate_response(template_name, test_context)
            result['test_context'] = test_context
            result['test_successful'] = True

            return result

        except Exception as e:
            return {
                'test_successful': False,
                'error': str(e),
                'template_name': template_name,
                'test_context': test_context
            }

    def get_template_stats(self) -> Dict[str, Any]:
        """Get template system statistics"""
        total_content_length = sum(len(content) for content in self.templates.values())

        return {
            'total_templates': len(self.templates),
            'template_names': list(self.templates.keys()),
            'average_length': total_content_length // len(self.templates) if self.templates else 0,
            'jinja_enabled': self.jinja_env is not None,
            'templates_path': str(self.templates_path),
            'royal_pattern_categories': len(self.royal_patterns)
        }

    def bulk_validate_templates(self) -> Dict[str, Dict[str, Any]]:
        """Validate all templates for royal courtesy standards"""
        results = {}

        for template_name, template_content in self.templates.items():
            # Remove Jinja2 variables for validation
            clean_content = re.sub(r'\{\{[^}]+\}\}', '', template_content)
            results[template_name] = self.validate_royal_courtesy(clean_content)

        return results


# Utility functions
def create_template_context(customer_name: Optional[str] = None,
                          order_number: Optional[str] = None,
                          invoice_number: Optional[str] = None,
                          company_name: Optional[str] = None,
                          urgent_hours: Optional[str] = None,
                          issue_details: Optional[str] = None) -> Dict[str, Any]:
    """Create template context from parameters"""
    context = {}

    if customer_name:
        context['customer_name'] = customer_name
    if order_number:
        context['order_number'] = order_number
    if invoice_number:
        context['invoice_number'] = invoice_number
    if company_name:
        context['company_name'] = company_name
    if urgent_hours:
        context['urgent_hours'] = urgent_hours
    if issue_details:
        context['issue_details'] = issue_details

    return context


if __name__ == "__main__":
    # Test the template system
    def test_templates():
        templates = RoyalCourtesyTemplates()

        print("=== Royal Courtesy Templates Test ===")
        print(f"Available templates: {templates.get_available_templates()}")

        # Test various templates
        test_cases = [
            ('order_received', {'customer_name': 'Mr. Johnson', 'order_number': 'ORD-2024-001'}),
            ('oem_priority_ack', {'company_name': 'OEM Manufacturing Ltd'}),
            ('complaint_ack', {'issue_details': 'defective buttons'}),
            ('expedite_ack', {'urgent_hours': '6'})
        ]

        for template_name, context in test_cases:
            print(f"\n--- Testing {template_name} ---")
            result = templates.test_template(template_name, context)

            if result['test_successful']:
                print(f"Subject: {result['subject']}")
                print(f"Validation Score: {result['validation']['score']}/100")
                print(f"Valid: {result['validation']['is_valid']}")
                if result['validation']['issues']:
                    print(f"Issues: {result['validation']['issues']}")
            else:
                print(f"Test failed: {result['error']}")

        # Bulk validation
        print(f"\n--- Bulk Validation Results ---")
        bulk_results = templates.bulk_validate_templates()
        for template_name, validation in bulk_results.items():
            print(f"{template_name}: {validation['score']}/100 ({'✓' if validation['is_valid'] else '✗'})")

        print(f"\n--- System Statistics ---")
        stats = templates.get_template_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

    test_templates()
