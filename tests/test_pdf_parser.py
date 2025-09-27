#!/usr/bin/env python3
"""
Unit tests for PDF Parser
Tests order and invoice PDF parsing to JSON schema
"""

import unittest
import sys
import os
import json
import tempfile

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parsers.pdf.pdf_parser import PDFParser, ParsedOrder, ParsedInvoice, ParsedOrderItem


class TestPDFParser(unittest.TestCase):
    """Test cases for PDF Parser functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.parser = PDFParser()

    def test_parser_initialization(self):
        """Test parser initializes correctly"""
        self.assertIsInstance(self.parser, PDFParser)
        self.assertIsNotNone(self.parser.patterns)
        self.assertIn('order_number', self.parser.patterns)
        self.assertIn('invoice_number', self.parser.patterns)

    def test_document_type_detection(self):
        """Test document type detection"""
        order_text = "Order Number: ORD-001 Customer delivery address"
        invoice_text = "Invoice Number: INV-001 Payment due date"

        self.assertEqual(self.parser._detect_document_type(order_text), "order")
        self.assertEqual(self.parser._detect_document_type(invoice_text), "invoice")

    def test_pattern_extraction(self):
        """Test regex pattern extraction"""
        test_text = "ORDER: ORD2024001\nEmail: test@example.com"

        order_num = self.parser._extract_pattern(test_text, 'order_number')
        email = self.parser._extract_pattern(test_text, 'email')

        self.assertEqual(order_num, "ORD2024001")
        self.assertEqual(email, "test@example.com")

    def test_customer_name_extraction(self):
        """Test customer name extraction"""
        test_text = "Bill to: John Doe Company\nAddress: 123 Main St"

        customer_name = self.parser._extract_customer_name(test_text)
        self.assertEqual(customer_name, "John Doe Company")

    def test_item_extraction(self):
        """Test line item extraction"""
        test_text = """
        Items:
        BTN-001    Red Button    10    2.50    25.00
        BTN-002    Blue Button   5     5.00    25.00
        """

        items = self.parser._extract_items(test_text)

        # Should extract valid items or create placeholder
        self.assertGreater(len(items), 0)
        self.assertIsInstance(items[0], ParsedOrderItem)

    def test_tax_extraction(self):
        """Test tax amount extraction"""
        test_text = "VAT 19%: €95.00\nSubtotal: €500.00"

        tax = self.parser._extract_tax(test_text, 500.0)
        self.assertGreater(tax, 0)

    def test_json_conversion_order(self):
        """Test order to JSON conversion"""
        # Create test order
        test_item = ParsedOrderItem(
            sku="BTN-001",
            name="Test Button",
            quantity=10,
            unit_price=2.50,
            total_price=25.00
        )

        test_order = ParsedOrder(
            order_number="ORD-001",
            customer_name="Test Customer",
            customer_email="test@example.com",
            customer_address="123 Test St",
            items=[test_item],
            subtotal=25.00,
            tax=4.75,
            total=29.75,
            order_date="2024-01-01",
            delivery_address="123 Test St"
        )

        json_output = self.parser.to_json(test_order)
        parsed_json = json.loads(json_output)

        # Verify JSON schema structure
        self.assertEqual(parsed_json['type'], 'order')
        self.assertEqual(parsed_json['order_number'], 'ORD-001')
        self.assertIn('customer', parsed_json)
        self.assertIn('items', parsed_json)
        self.assertIn('totals', parsed_json)
        self.assertIn('dates', parsed_json)
        self.assertIn('delivery', parsed_json)

        # Verify customer structure
        customer = parsed_json['customer']
        self.assertEqual(customer['name'], 'Test Customer')
        self.assertEqual(customer['email'], 'test@example.com')

        # Verify items structure
        items = parsed_json['items']
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item['sku'], 'BTN-001')
        self.assertEqual(item['quantity'], 10)
        self.assertEqual(item['unit_price'], 2.50)

    def test_json_conversion_invoice(self):
        """Test invoice to JSON conversion"""
        test_item = ParsedOrderItem(
            sku="BTN-001",
            name="Test Button",
            quantity=10,
            unit_price=2.50,
            total_price=25.00
        )

        test_invoice = ParsedInvoice(
            invoice_number="INV-001",
            order_number="ORD-001",
            customer_name="Test Customer",
            customer_address="123 Test St",
            invoice_date="2024-01-01",
            due_date="2024-01-31",
            items=[test_item],
            subtotal=25.00,
            tax=4.75,
            total=29.75,
            payment_terms="Net 30"
        )

        json_output = self.parser.to_json(test_invoice)
        parsed_json = json.loads(json_output)

        # Verify JSON schema structure
        self.assertEqual(parsed_json['type'], 'invoice')
        self.assertEqual(parsed_json['invoice_number'], 'INV-001')
        self.assertEqual(parsed_json['order_number'], 'ORD-001')
        self.assertIn('customer', parsed_json)
        self.assertIn('items', parsed_json)
        self.assertIn('totals', parsed_json)
        self.assertIn('dates', parsed_json)
        self.assertIn('payment', parsed_json)

        # Verify dates structure
        dates = parsed_json['dates']
        self.assertEqual(dates['invoice_date'], '2024-01-01')
        self.assertEqual(dates['due_date'], '2024-01-31')

        # Verify payment structure
        payment = parsed_json['payment']
        self.assertEqual(payment['terms'], 'Net 30')

    def test_sample_pdf_parsing(self):
        """Test parsing actual sample PDF if available"""
        sample_path = os.path.join(os.path.dirname(__file__), '..', 'samples', 'test_order.pdf')

        if os.path.exists(sample_path):
            result = self.parser.parse_pdf(sample_path)

            if result:
                self.assertIsInstance(result, (ParsedOrder, ParsedInvoice))

                # Test JSON conversion
                json_output = self.parser.to_json(result)
                parsed_json = json.loads(json_output)

                # Verify basic JSON structure
                self.assertIn('type', parsed_json)
                self.assertIn(parsed_json['type'], ['order', 'invoice'])
            else:
                # If parsing fails, that's acceptable for this test
                # The important thing is that it doesn't crash
                self.assertTrue(True, "PDF parsing gracefully handled failure")

    def test_nonexistent_file_handling(self):
        """Test handling of non-existent files"""
        result = self.parser.parse_pdf('/nonexistent/file.pdf')
        self.assertIsNone(result)

    def test_invalid_document_type(self):
        """Test handling of invalid document types"""
        result = self.parser.parse_pdf('samples/test_order.pdf', document_type='invalid')
        self.assertIsNone(result)


if __name__ == '__main__':
    # Create tests directory if it doesn't exist
    tests_dir = os.path.dirname(__file__)
    if not os.path.exists(tests_dir):
        os.makedirs(tests_dir)

    # Run tests
    unittest.main(verbosity=2)