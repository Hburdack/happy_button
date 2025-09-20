"""
Happy Buttons Email Parser - Python Implementation
Handles parsing of incoming emails and extraction of metadata
"""

import re
import email.message
import email.parser
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from PyPDF2 import PdfReader
import io
import logging

logger = logging.getLogger(__name__)


@dataclass
class EmailMetadata:
    """Email metadata extracted during parsing"""
    is_oem: bool = False
    priority: str = "medium"
    category: str = "general"
    has_order_pdf: bool = False
    has_invoice_pdf: bool = False
    is_urgent: bool = False
    keywords: List[str] = field(default_factory=list)
    confidence_score: float = 0.0


@dataclass
class AttachmentInfo:
    """Information about email attachments"""
    filename: str
    content_type: str
    size: int
    is_pdf: bool = False
    extracted_text: str = ""
    content: Optional[bytes] = None


@dataclass
class SenderInfo:
    """Information about email sender"""
    email: str
    name: str = ""
    domain: str = ""


@dataclass
class ParsedEmail:
    """Complete parsed email structure"""
    id: str
    timestamp: datetime
    sender: SenderInfo
    recipient: str
    subject: str
    body: str
    attachments: List[AttachmentInfo]
    metadata: EmailMetadata
    raw_headers: Dict[str, str] = field(default_factory=dict)


class EmailParser:
    """
    Email Parser for Happy Buttons Agentic Simulation
    Handles parsing of incoming emails and extraction of metadata
    """

    def __init__(self):
        self.supported_attachment_types = ['.pdf', '.doc', '.docx', '.txt']

        # Business-specific keywords for classification
        self.keywords = {
            'order': ['order', 'purchase', 'buy', 'quote', 'quotation', 'po number'],
            'invoice': ['invoice', 'bill', 'payment', 'due', 'amount', 'remittance'],
            'supplier': ['delivery', 'shipment', 'supplier', 'vendor', 'stock', 'inventory'],
            'complaint': ['complaint', 'issue', 'problem', 'defect', 'quality', 'wrong', 'damaged'],
            'urgent': ['urgent', 'asap', 'immediate', 'emergency', 'rush', 'critical'],
            'logistics': ['shipping', 'tracking', 'warehouse', 'distribution', 'freight'],
            'hr': ['employment', 'job', 'career', 'hr', 'human resources', 'benefits'],
            'finance': ['payment', 'billing', 'accounting', 'finance', 'credit', 'debit']
        }

        # OEM domains (from config)
        self.oem_domains = ['oem1.com']

        # Patterns for value extraction
        self.patterns = {
            'email': re.compile(r'<([^>]+)>'),
            'amount': re.compile(r'\$[\d,]+\.?\d*'),
            'order_number': re.compile(r'(?:order|po)\s*#?\s*(\w+)', re.IGNORECASE),
            'invoice_number': re.compile(r'(?:invoice|inv)\s*#?\s*(\w+)', re.IGNORECASE),
            'date': re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}')
        }

    async def parse_email(self, email_data: Union[str, bytes, email.message.EmailMessage]) -> ParsedEmail:
        """
        Parse incoming email and extract metadata

        Args:
            email_data: Raw email data or email.message.EmailMessage object

        Returns:
            ParsedEmail: Parsed email with metadata
        """
        try:
            # Convert to EmailMessage if needed
            if isinstance(email_data, (str, bytes)):
                msg = email.message_from_string(email_data) if isinstance(email_data, str) else email.message_from_bytes(email_data)
            else:
                msg = email_data

            # Generate unique ID
            email_id = self._generate_email_id()

            # Extract basic email components
            sender = self._extract_sender(msg)
            recipient = self._extract_recipient(msg)
            subject = msg.get('Subject', '')
            body = self._extract_body(msg)

            # Process attachments
            attachments = await self._parse_attachments(msg)

            # Generate metadata
            metadata = self._analyze_content(subject, body, attachments, sender)

            # Create parsed email object
            parsed_email = ParsedEmail(
                id=email_id,
                timestamp=datetime.now(),
                sender=sender,
                recipient=recipient,
                subject=subject,
                body=body,
                attachments=attachments,
                metadata=metadata,
                raw_headers=dict(msg.items())
            )

            logger.info(f"Successfully parsed email {email_id} from {sender.email}")
            return parsed_email

        except Exception as e:
            logger.error(f"Email parsing failed: {str(e)}")
            raise Exception(f"Email parsing failed: {str(e)}")

    def _generate_email_id(self) -> str:
        """Generate unique email ID"""
        return f"email_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"

    def _extract_sender(self, msg: email.message.EmailMessage) -> SenderInfo:
        """Extract sender information from email"""
        from_header = msg.get('From', '')

        # Try to extract email from angle brackets
        email_match = self.patterns['email'].search(from_header)
        if email_match:
            sender_email = email_match.group(1)
            sender_name = from_header.replace(f'<{sender_email}>', '').strip()
        else:
            # Fallback: assume the whole field is email
            parts = from_header.split()
            sender_email = parts[-1] if parts else ''
            sender_name = ' '.join(parts[:-1]) if len(parts) > 1 else ''

        # Extract domain
        domain = sender_email.split('@')[1] if '@' in sender_email else ''

        return SenderInfo(
            email=sender_email,
            name=sender_name.strip('"'),
            domain=domain
        )

    def _extract_recipient(self, msg: email.message.EmailMessage) -> str:
        """Extract recipient email"""
        return msg.get('To', 'info@h-bu.de')

    def _extract_body(self, msg: email.message.EmailMessage) -> str:
        """Extract email body text"""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif part.get_content_type() == "text/html" and not body:
                    # Use HTML as fallback if no plain text
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

        return body.strip()

    async def _parse_attachments(self, msg: email.message.EmailMessage) -> List[AttachmentInfo]:
        """Parse email attachments"""
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    attachment = await self._process_attachment(part)
                    if attachment:
                        attachments.append(attachment)

        return attachments

    async def _process_attachment(self, part: email.message.EmailMessage) -> Optional[AttachmentInfo]:
        """Process individual attachment"""
        try:
            filename = part.get_filename() or 'unknown'
            content_type = part.get_content_type()
            content = part.get_payload(decode=True)
            size = len(content) if content else 0

            # Check if PDF
            is_pdf = self._is_pdf(filename, content_type)

            # Extract text from PDF if possible
            extracted_text = ""
            if is_pdf and content:
                try:
                    extracted_text = await self._extract_pdf_text(content)
                except Exception as e:
                    logger.warning(f"PDF text extraction failed for {filename}: {str(e)}")

            return AttachmentInfo(
                filename=filename,
                content_type=content_type,
                size=size,
                is_pdf=is_pdf,
                extracted_text=extracted_text,
                content=content
            )

        except Exception as e:
            logger.error(f"Attachment processing failed: {str(e)}")
            return None

    def _is_pdf(self, filename: str, content_type: str) -> bool:
        """Check if attachment is PDF"""
        return (filename.lower().endswith('.pdf') or
                'pdf' in content_type.lower())

    async def _extract_pdf_text(self, content: bytes) -> str:
        """Extract text from PDF content"""
        try:
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)

            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"

            return text.strip()

        except Exception as e:
            logger.error(f"PDF text extraction error: {str(e)}")
            return ""

    def _analyze_content(self, subject: str, body: str,
                        attachments: List[AttachmentInfo],
                        sender: SenderInfo) -> EmailMetadata:
        """Analyze email content and generate metadata"""

        # Combine all text for analysis
        full_text = f"{subject} {body}".lower()

        # Add attachment text
        for attachment in attachments:
            if attachment.extracted_text:
                full_text += f" {attachment.extracted_text.lower()}"

        # Initialize metadata
        metadata = EmailMetadata()

        # Check if OEM customer
        metadata.is_oem = sender.domain in self.oem_domains

        # Categorize email
        metadata.category = self._categorize_email(full_text)

        # Check for urgent keywords
        metadata.is_urgent = self._contains_keywords(full_text, self.keywords['urgent'])

        # Check for PDF types
        metadata.has_order_pdf = self._has_order_pdf(attachments, full_text)
        metadata.has_invoice_pdf = self._has_invoice_pdf(attachments, full_text)

        # Extract keywords
        metadata.keywords = self._extract_keywords(full_text)

        # Determine priority
        metadata.priority = self._determine_priority(metadata, full_text)

        # Calculate confidence score
        metadata.confidence_score = self._calculate_confidence(metadata, full_text)

        return metadata

    def _categorize_email(self, content: str) -> str:
        """Categorize email based on content"""
        scores = {}

        for category, keywords in self.keywords.items():
            if category == 'urgent':  # Skip urgent as it's not a category
                continue

            score = sum(1 for keyword in keywords if keyword in content)
            if score > 0:
                scores[category] = score

        # Return category with highest score
        if scores:
            return max(scores, key=scores.get)

        return 'general'

    def _contains_keywords(self, content: str, keywords: List[str]) -> bool:
        """Check if content contains any of the specified keywords"""
        return any(keyword in content for keyword in keywords)

    def _has_order_pdf(self, attachments: List[AttachmentInfo], content: str) -> bool:
        """Check if email contains order-related PDF"""
        # Check attachments
        for attachment in attachments:
            if attachment.is_pdf:
                attachment_text = f"{attachment.filename} {attachment.extracted_text}".lower()
                if self._contains_keywords(attachment_text, self.keywords['order']):
                    return True

        # Check if order PDF mentioned in content
        return 'order.pdf' in content or 'purchase.pdf' in content

    def _has_invoice_pdf(self, attachments: List[AttachmentInfo], content: str) -> bool:
        """Check if email contains invoice-related PDF"""
        # Check attachments
        for attachment in attachments:
            if attachment.is_pdf:
                attachment_text = f"{attachment.filename} {attachment.extracted_text}".lower()
                if self._contains_keywords(attachment_text, self.keywords['invoice']):
                    return True

        # Check if invoice PDF mentioned in content
        return 'invoice.pdf' in content or 'bill.pdf' in content

    def _extract_keywords(self, content: str) -> List[str]:
        """Extract relevant keywords from content"""
        found_keywords = []

        for category, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword in content and keyword not in found_keywords:
                    found_keywords.append(keyword)

        return found_keywords

    def _determine_priority(self, metadata: EmailMetadata, content: str) -> str:
        """Determine email priority level"""
        score = 50  # Base score

        # OEM customer bonus
        if metadata.is_oem:
            score += 30

        # Urgent keywords
        if metadata.is_urgent:
            score += 25

        # PDF attachments indicate formal business
        if metadata.has_order_pdf or metadata.has_invoice_pdf:
            score += 15

        # Complaint handling
        if metadata.category == 'complaint':
            score += 20

        # High value indicators
        amounts = self.patterns['amount'].findall(content)
        if amounts:
            max_amount = max(float(amount.replace('$', '').replace(',', ''))
                           for amount in amounts)
            if max_amount > 10000:
                score += 20

        # Determine priority level
        if score >= 80:
            return 'critical'
        elif score >= 60:
            return 'high'
        elif score >= 40:
            return 'medium'
        else:
            return 'low'

    def _calculate_confidence(self, metadata: EmailMetadata, content: str) -> float:
        """Calculate confidence score for the analysis"""
        confidence = 0.5  # Base confidence

        # Boost confidence for clear indicators
        if metadata.has_order_pdf or metadata.has_invoice_pdf:
            confidence += 0.3

        if len(metadata.keywords) > 3:
            confidence += 0.2

        if metadata.is_oem:
            confidence += 0.1

        # Check for clear patterns
        if (self.patterns['order_number'].search(content) or
            self.patterns['invoice_number'].search(content)):
            confidence += 0.2

        return min(confidence, 1.0)

    def validate_parsed_email(self, parsed_email: ParsedEmail) -> bool:
        """Validate parsed email object"""
        required_fields = ['id', 'timestamp', 'sender', 'recipient', 'subject', 'body', 'metadata']

        for field in required_fields:
            if not hasattr(parsed_email, field):
                return False

        # Validate sender email format
        if '@' not in parsed_email.sender.email:
            return False

        return True

    def get_parsing_stats(self) -> Dict[str, Any]:
        """Get parsing statistics"""
        return {
            'supported_types': self.supported_attachment_types,
            'keyword_categories': list(self.keywords.keys()),
            'oem_domains': self.oem_domains,
            'total_keywords': sum(len(keywords) for keywords in self.keywords.values())
        }


# Utility functions for external use
async def create_test_email_async(sender: str, subject: str, body: str,
                                 attachments: Optional[List[Dict]] = None) -> ParsedEmail:
    """Create a test email for development/testing (async version)"""
    parser = EmailParser()

    # Create mock email message
    msg = email.message.EmailMessage()
    msg['From'] = sender
    msg['To'] = 'info@h-bu.de'
    msg['Subject'] = subject
    msg.set_content(body)

    # Add attachments if provided
    if attachments:
        for att in attachments:
            msg.add_attachment(
                att.get('content', b''),
                maintype='application',
                subtype='pdf' if att.get('filename', '').endswith('.pdf') else 'octet-stream',
                filename=att.get('filename', 'attachment')
            )

    return await parser.parse_email(msg)

def create_test_email(sender: str, subject: str, body: str,
                     attachments: Optional[List[Dict]] = None) -> ParsedEmail:
    """Create a test email for development/testing (sync version)"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, we can't use asyncio.run()
            # This is a simplified sync version for testing
            parser = EmailParser()

            # Create simplified ParsedEmail for testing
            # (classes already imported above)

            sender_parts = sender.split('<')
            if len(sender_parts) == 2:
                sender_name = sender_parts[0].strip()
                sender_email = sender_parts[1].rstrip('>')
            else:
                sender_name = ""
                sender_email = sender

            domain = sender_email.split('@')[1] if '@' in sender_email else ''

            sender_info = SenderInfo(
                email=sender_email,
                name=sender_name,
                domain=domain
            )

            # Create metadata
            metadata = parser._analyze_content(subject, body, [], sender_info)

            return ParsedEmail(
                id=parser._generate_email_id(),
                timestamp=datetime.now(),
                sender=sender_info,
                recipient='info@h-bu.de',
                subject=subject,
                body=body,
                attachments=[],
                metadata=metadata
            )
    except:
        pass

    # Fallback to async version
    return asyncio.run(create_test_email_async(sender, subject, body, attachments))


if __name__ == "__main__":
    # Test the parser
    import asyncio

    async def test_parser():
        parser = EmailParser()

        # Create test email
        test_email = create_test_email(
            sender='John Smith <john@oem1.com>',
            subject='Urgent Order Request - Need Immediate Quote',
            body='We need an urgent quote for 10,000 red buttons. Please process ASAP. Order value approximately $5,000.',
            attachments=[{
                'filename': 'order_specs.pdf',
                'content': b'PDF content here'
            }]
        )

        print(f"Parsed email ID: {test_email.id}")
        print(f"Sender: {test_email.sender.name} <{test_email.sender.email}>")
        print(f"Category: {test_email.metadata.category}")
        print(f"Priority: {test_email.metadata.priority}")
        print(f"Is OEM: {test_email.metadata.is_oem}")
        print(f"Is Urgent: {test_email.metadata.is_urgent}")
        print(f"Keywords: {test_email.metadata.keywords}")
        print(f"Confidence: {test_email.metadata.confidence_score:.2f}")

    asyncio.run(test_parser())