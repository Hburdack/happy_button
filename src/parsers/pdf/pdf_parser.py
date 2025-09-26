"""
PDF Parser for Happy Buttons Release 2
Parses order and invoice PDFs to JSON schema
"""

try:
    import pdfplumber  # type: ignore
except ImportError:  # pragma: no cover - optional dependency in some envs
    pdfplumber = None

import PyPDF2
import re
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import os

@dataclass
class ParsedOrderItem:
    sku: str
    name: str
    quantity: int
    unit_price: float
    total_price: float

@dataclass
class ParsedOrder:
    order_number: str
    customer_name: str
    customer_email: str
    customer_address: str
    items: List[ParsedOrderItem]
    subtotal: float
    tax: float
    total: float
    order_date: str
    delivery_address: str
    special_instructions: str = ""

@dataclass
class ParsedInvoice:
    invoice_number: str
    order_number: str
    customer_name: str
    customer_address: str
    invoice_date: str
    due_date: str
    items: List[ParsedOrderItem]
    subtotal: float
    tax: float
    total: float
    payment_terms: str = ""

class PDFParser:
    """Parse order and invoice PDFs to structured JSON"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Regex patterns for different PDF formats
        self.patterns = {
            'order_number': [
                r'(?:Order|Bestellung|Order No\.?|Bestellnummer)[:\s#]*(\w+)',
                r'ORDER[:\s#]*([A-Z0-9-]+)',
                r'PO[:\s#]*([A-Z0-9-]+)'
            ],
            'invoice_number': [
                r'(?:Invoice|Rechnung|Invoice No\.?|Rechnungsnummer)[:\s#]*(\w+)',
                r'INVOICE[:\s#]*([A-Z0-9-]+)',
                r'RE[:\s#]*([A-Z0-9-]+)'
            ],
            'email': [
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ],
            'date': [
                r'(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{1,2}\.\d{1,2}\.\d{4})'
            ],
            'money': [
                r'€\s*(\d+[.,]\d{2})',
                r'(\d+[.,]\d{2})\s*€',
                r'EUR\s*(\d+[.,]\d{2})',
                r'(\d+[.,]\d{2})\s*EUR'
            ]
        }

    def parse_pdf(self, pdf_path: str, document_type: str = "auto") -> Optional[Union[ParsedOrder, ParsedInvoice]]:
        """Parse PDF file and return structured data"""
        if not os.path.exists(pdf_path):
            self.logger.error(f"PDF file not found: {pdf_path}")
            return None

        try:
            # Extract text from PDF
            text = self._extract_text(pdf_path)
            if not text:
                return None

            # Determine document type if auto
            if document_type == "auto":
                document_type = self._detect_document_type(text)

            # Parse based on type
            if document_type == "order":
                return self._parse_order(text)
            elif document_type == "invoice":
                return self._parse_invoice(text)
            else:
                self.logger.error(f"Unknown document type: {document_type}")
                return None

        except Exception as e:
            self.logger.error(f"Error parsing PDF {pdf_path}: {e}")
            return None

    def _extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF using pdfplumber (primary) and PyPDF2 (fallback)"""
        text = ""

        # Try pdfplumber first (better for tables) when available
        if pdfplumber is not None:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"

                if text.strip():
                    return text

            except Exception as e:
                self.logger.warning(f"pdfplumber failed for {pdf_path}: {e}")
        else:
            self.logger.debug("pdfplumber not installed; falling back to PyPDF2")

        # Fallback to PyPDF2
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

        except Exception as e:
            self.logger.error(f"PyPDF2 also failed for {pdf_path}: {e}")

        return text

    def _detect_document_type(self, text: str) -> str:
        """Detect if document is order or invoice"""
        text_lower = text.lower()

        invoice_keywords = ['invoice', 'rechnung', 'bill', 'payment due', 'due date']
        order_keywords = ['order', 'bestellung', 'purchase order', 'po number', 'delivery']

        invoice_score = sum(1 for keyword in invoice_keywords if keyword in text_lower)
        order_score = sum(1 for keyword in order_keywords if keyword in text_lower)

        if invoice_score > order_score:
            return "invoice"
        elif order_score > 0:
            return "order"
        else:
            return "unknown"

    def _parse_order(self, text: str) -> Optional[ParsedOrder]:
        """Parse order-specific information"""
        try:
            # Extract basic information
            order_number = self._extract_pattern(text, 'order_number')
            customer_name = self._extract_customer_name(text)
            customer_email = self._extract_pattern(text, 'email')
            customer_address = self._extract_address(text)
            order_date = self._extract_pattern(text, 'date')

            # Extract items (this is the complex part)
            items = self._extract_items(text)

            # Calculate totals
            subtotal = sum(item.total_price for item in items)
            tax = self._extract_tax(text, subtotal)
            total = subtotal + tax

            # Extract additional information
            delivery_address = self._extract_delivery_address(text)
            special_instructions = self._extract_special_instructions(text)

            order = ParsedOrder(
                order_number=order_number or f"ORD_{int(time.time())}",
                customer_name=customer_name or "Unknown Customer",
                customer_email=customer_email or "",
                customer_address=customer_address or "",
                items=items,
                subtotal=subtotal,
                tax=tax,
                total=total,
                order_date=order_date or "",
                delivery_address=delivery_address or customer_address or "",
                special_instructions=special_instructions
            )

            return order

        except Exception as e:
            self.logger.error(f"Error parsing order: {e}")
            return None

    def _parse_invoice(self, text: str) -> Optional[ParsedInvoice]:
        """Parse invoice-specific information"""
        try:
            # Extract basic information
            invoice_number = self._extract_pattern(text, 'invoice_number')
            order_number = self._extract_pattern(text, 'order_number')
            customer_name = self._extract_customer_name(text)
            customer_address = self._extract_address(text)
            invoice_date = self._extract_pattern(text, 'date')
            due_date = self._extract_due_date(text)

            # Extract items
            items = self._extract_items(text)

            # Calculate totals
            subtotal = sum(item.total_price for item in items)
            tax = self._extract_tax(text, subtotal)
            total = subtotal + tax

            # Payment terms
            payment_terms = self._extract_payment_terms(text)

            invoice = ParsedInvoice(
                invoice_number=invoice_number or f"INV_{int(time.time())}",
                order_number=order_number or "",
                customer_name=customer_name or "Unknown Customer",
                customer_address=customer_address or "",
                invoice_date=invoice_date or "",
                due_date=due_date or "",
                items=items,
                subtotal=subtotal,
                tax=tax,
                total=total,
                payment_terms=payment_terms
            )

            return invoice

        except Exception as e:
            self.logger.error(f"Error parsing invoice: {e}")
            return None

    def _extract_pattern(self, text: str, pattern_type: str) -> str:
        """Extract information using regex patterns"""
        if pattern_type not in self.patterns:
            return ""

        for pattern in self.patterns[pattern_type]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_customer_name(self, text: str) -> str:
        """Extract customer name from text"""
        # Look for common patterns
        patterns = [
            r'(?:Bill to|Ship to|Customer|Kunde)[:\n\s]*([A-Za-z\s]+)(?:\n|$)',
            r'(?:Name|Firma)[:\s]*([A-Za-z\s]+)(?:\n|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2 and not re.match(r'^\d+$', name):  # Not just numbers
                    return name

        return ""

    def _extract_address(self, text: str) -> str:
        """Extract address information"""
        # This is a simplified implementation
        # Real implementation would be more sophisticated
        lines = text.split('\n')
        address_lines = []

        for i, line in enumerate(lines):
            line = line.strip()
            # Look for address-like patterns
            if re.search(r'\d+.*(?:street|str|avenue|ave|road|rd)', line, re.IGNORECASE):
                address_lines.append(line)
                # Include next few lines that might be part of address
                for j in range(1, 3):
                    if i + j < len(lines):
                        next_line = lines[i + j].strip()
                        if next_line and len(next_line) < 50:
                            address_lines.append(next_line)

        return '\n'.join(address_lines)

    def _extract_items(self, text: str) -> List[ParsedOrderItem]:
        """Extract line items from document"""
        items = []

        # Split text into lines for processing
        lines = text.split('\n')

        # Look for tabular data patterns
        for i, line in enumerate(lines):
            line = line.strip()

            # Skip empty lines or headers
            if not line or len(line) < 10:
                continue

            # Look for patterns that might be item lines
            # This is a simplified pattern - real implementation would be more robust
            item_match = re.search(r'(\w+[-_]\w+)\s+(.+?)\s+(\d+)\s+(\d+[.,]\d{2})\s+(\d+[.,]\d{2})', line)

            if item_match:
                try:
                    sku = item_match.group(1)
                    name = item_match.group(2).strip()
                    quantity = int(item_match.group(3))
                    unit_price = float(item_match.group(4).replace(',', '.'))
                    total_price = float(item_match.group(5).replace(',', '.'))

                    item = ParsedOrderItem(
                        sku=sku,
                        name=name,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=total_price
                    )
                    items.append(item)

                except (ValueError, AttributeError) as e:
                    self.logger.debug(f"Failed to parse item line: {line} - {e}")

        # If no items found, create a placeholder
        if not items:
            self.logger.warning("No items extracted, creating placeholder")
            items.append(ParsedOrderItem(
                sku="UNKNOWN",
                name="Items as per document",
                quantity=1,
                unit_price=0.0,
                total_price=0.0
            ))

        return items

    def _extract_tax(self, text: str, subtotal: float) -> float:
        """Extract tax amount"""
        tax_patterns = [
            r'(?:tax|vat|mwst)[:\s]*€?\s*(\d+[.,]\d{2})',
            r'(\d+[.,]\d{2})\s*€?\s*(?:tax|vat|mwst)',
            r'19%.*?(\d+[.,]\d{2})',  # Common German VAT
        ]

        for pattern in tax_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', '.'))
                except ValueError:
                    continue

        # If no explicit tax found, assume 19% VAT
        return round(subtotal * 0.19, 2)

    def _extract_delivery_address(self, text: str) -> str:
        """Extract delivery address"""
        # Look for "Ship to", "Delivery", etc.
        delivery_patterns = [
            r'(?:Ship to|Delivery|Lieferadresse)[:\n\s]*([A-Za-z0-9\s\n,.-]+?)(?:\n\n|\n[A-Z])',
        ]

        for pattern in delivery_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_special_instructions(self, text: str) -> str:
        """Extract special instructions or notes"""
        instruction_patterns = [
            r'(?:special instructions|notes|remarks|bemerkungen)[:\n\s]*([^\n]+)',
            r'(?:please|bitte)[:\s]*([^\n]+)',
        ]

        for pattern in instruction_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_due_date(self, text: str) -> str:
        """Extract due date from invoice"""
        due_patterns = [
            r'(?:due date|fällig|payment due)[:\s]*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})',
            r'(?:due|fällig)[:\s]*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})',
        ]

        for pattern in due_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return ""

    def _extract_payment_terms(self, text: str) -> str:
        """Extract payment terms"""
        terms_patterns = [
            r'(?:payment terms|zahlungsbedingungen)[:\s]*([^\n]+)',
            r'(?:terms|bedingungen)[:\s]*([^\n]+)',
        ]

        for pattern in terms_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return "Net 30 days"  # Default

    def to_json(self, parsed_data: Union[ParsedOrder, ParsedInvoice]) -> str:
        """Convert parsed data to JSON"""
        try:
            if isinstance(parsed_data, ParsedOrder):
                data = {
                    'type': 'order',
                    'order_number': parsed_data.order_number,
                    'customer': {
                        'name': parsed_data.customer_name,
                        'email': parsed_data.customer_email,
                        'address': parsed_data.customer_address
                    },
                    'items': [
                        {
                            'sku': item.sku,
                            'name': item.name,
                            'quantity': item.quantity,
                            'unit_price': item.unit_price,
                            'total_price': item.total_price
                        } for item in parsed_data.items
                    ],
                    'totals': {
                        'subtotal': parsed_data.subtotal,
                        'tax': parsed_data.tax,
                        'total': parsed_data.total
                    },
                    'dates': {
                        'order_date': parsed_data.order_date
                    },
                    'delivery': {
                        'address': parsed_data.delivery_address,
                        'instructions': parsed_data.special_instructions
                    }
                }
            elif isinstance(parsed_data, ParsedInvoice):
                data = {
                    'type': 'invoice',
                    'invoice_number': parsed_data.invoice_number,
                    'order_number': parsed_data.order_number,
                    'customer': {
                        'name': parsed_data.customer_name,
                        'address': parsed_data.customer_address
                    },
                    'items': [
                        {
                            'sku': item.sku,
                            'name': item.name,
                            'quantity': item.quantity,
                            'unit_price': item.unit_price,
                            'total_price': item.total_price
                        } for item in parsed_data.items
                    ],
                    'totals': {
                        'subtotal': parsed_data.subtotal,
                        'tax': parsed_data.tax,
                        'total': parsed_data.total
                    },
                    'dates': {
                        'invoice_date': parsed_data.invoice_date,
                        'due_date': parsed_data.due_date
                    },
                    'payment': {
                        'terms': parsed_data.payment_terms
                    }
                }
            else:
                raise ValueError("Unknown data type")

            return json.dumps(data, indent=2)

        except Exception as e:
            self.logger.error(f"Error converting to JSON: {e}")
            return "{}"

# Demo usage and testing
if __name__ == "__main__":
    import time

    logging.basicConfig(level=logging.INFO)

    parser = PDFParser()
    print("PDF Parser initialized")

    # Demo: Create a simple test for the parser
    test_order_text = """
    ORDER NUMBER: ORD-2024-001
    Customer: Test Customer
    Email: test@customer.com

    Items:
    BTN-001    Red Button    100    2.50    250.00
    BTN-002    Blue Button   50     5.00    250.00

    Subtotal: 500.00
    VAT 19%: 95.00
    Total: 595.00
    """

    print("Parser ready for PDF processing")
    print("Note: This demo shows the structure. Real PDFs would be parsed from files.")
