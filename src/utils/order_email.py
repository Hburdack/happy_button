"""
Order to Email Integration System
Generates emails from webshop orders and integrates with email processing flow
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import tempfile


class OrderEmailGenerator:
    """Generates emails and PDFs from webshop orders"""

    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'templates')
        self.attachments_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'attachments')
        os.makedirs(self.attachments_dir, exist_ok=True)

    def generate_order_email(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Generate order confirmation email with royal courtesy style"""

        # Create order items summary
        items_summary = []
        for item in order['items']:
            items_summary.append(f"• {item['name']} (Qty: {item['quantity']}) - €{item['total_price']:.2f}")

        items_text = "\n".join(items_summary)

        # Generate royal courtesy email content
        email_content = f"""Most Esteemed Customer,

We are delighted to confirm the receipt of your order and extend our most sincere gratitude for choosing Happy Buttons GmbH for your button requirements.

ORDER DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Order Number: HB-{order['id']:06d}
Customer: {order['customer_name']}
Email: {order['customer_email']}
{f"Company: {order['customer_company']}" if order.get('customer_company') else ""}
Order Date: {datetime.fromisoformat(order['created_at']).strftime('%d %B %Y at %H:%M')}

ORDERED ITEMS:
{items_text}

Shipping Address:
{order['shipping_address']}

ORDER TOTAL: €{order['total_amount']:.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRODUCTION & DELIVERY INFORMATION:
Your order is being forwarded to our production facilities and will be processed with the utmost care and attention to detail. We anticipate dispatch within 5-7 business days, contingent upon current production schedules.

For premium orders exceeding €500, we shall endeavour to expedite processing within 3-5 business days.

Should you require any modifications to your order or have specific delivery requirements, kindly contact us at your earliest convenience.

We remain at your distinguished service and look forward to exceeding your expectations.

With our most respectful regards,

The Happy Buttons GmbH Team
orders@h-bu.de
+49 (0) 123 456 789

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Happy Buttons GmbH - Royal Quality Since 1847
Manufacturing Excellence | Global Distribution | Premium Service
Production Sites: China, Poland, Mexico, Moldova
Distribution Centers: New York, Maryland
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

        # Generate PDF attachment
        pdf_path = self.generate_order_pdf(order)

        # Create email structure for email processing system
        email_data = {
            'id': f'order_{order["id"]}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'from': order['customer_email'],
            'from_name': order['customer_name'],
            'to': 'orders@h-bu.de',
            'subject': f'Order Confirmation - HB-{order["id"]:06d} - €{order["total_amount"]:.2f}',
            'content': email_content,
            'timestamp': datetime.now().isoformat(),
            'time_ago': 'gerade eben',
            'routed_to': 'orders@h-bu.de',
            'priority': 'high' if order['total_amount'] > 500 else 'normal',
            'status': 'processed',
            'category': 'order',
            'size': f'{len(email_content)//1024 + 1}KB',
            'attachments': 1,
            'attachments_list': [{
                'name': f'Order_HB-{order["id"]:06d}.pdf',
                'size': '45KB',
                'type': 'PDF',
                'url': f'/api/emails/attachment/order_{order["id"]}/Order_HB-{order["id"]:06d}.pdf',
                'icon': 'fas fa-file-pdf'
            }],
            'processing_time': '250ms',
            'auto_reply_sent': True,
            'escalation_level': None,
            'importance': 'high' if order['total_amount'] > 500 else 'normal',
            'read_receipt_requested': True if order['total_amount'] > 1000 else False,
            'pdf_path': pdf_path
        }

        return email_data

    def generate_order_pdf(self, order: Dict[str, Any]) -> str:
        """Generate professional order PDF"""

        # Create PDF file path
        filename = f'Order_HB-{order["id"]:06d}.pdf'
        pdf_path = os.path.join(self.attachments_dir, filename)

        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),
            alignment=TA_CENTER,
            spaceAfter=30
        )

        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#3730a3'),
            spaceBefore=20,
            spaceAfter=10
        )

        # Company Header
        story.append(Paragraph("HAPPY BUTTONS GmbH", title_style))
        story.append(Paragraph("Royal Quality Since 1847", styles['Normal']))
        story.append(Spacer(1, 20))

        # Order Information
        story.append(Paragraph("ORDER CONFIRMATION", header_style))

        order_info_data = [
            ['Order Number:', f'HB-{order["id"]:06d}'],
            ['Order Date:', datetime.fromisoformat(order['created_at']).strftime('%d %B %Y at %H:%M')],
            ['Customer:', order['customer_name']],
            ['Email:', order['customer_email']],
        ]

        if order.get('customer_company'):
            order_info_data.append(['Company:', order['customer_company']])

        if order.get('customer_phone'):
            order_info_data.append(['Phone:', order['customer_phone']])

        order_info_table = Table(order_info_data, colWidths=[2*inch, 4*inch])
        order_info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        story.append(order_info_table)
        story.append(Spacer(1, 20))

        # Shipping Address
        story.append(Paragraph("SHIPPING ADDRESS", header_style))
        story.append(Paragraph(order['shipping_address'].replace('\n', '<br/>'), styles['Normal']))
        story.append(Spacer(1, 20))

        # Order Items
        story.append(Paragraph("ORDERED ITEMS", header_style))

        items_data = [['Product', 'Category', 'Quantity', 'Unit Price', 'Total']]

        for item in order['items']:
            items_data.append([
                item['name'],
                item.get('category', 'Standard'),
                str(item['quantity']),
                f"€{item['unit_price']:.2f}",
                f"€{item['total_price']:.2f}"
            ])

        # Add total row
        items_data.append(['', '', '', 'TOTAL:', f"€{order['total_amount']:.2f}"])

        items_table = Table(items_data, colWidths=[2.5*inch, 1*inch, 0.8*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3730a3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e0e7ff')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(items_table)
        story.append(Spacer(1, 30))

        # Footer Information
        story.append(Paragraph("PRODUCTION & DELIVERY", header_style))
        production_text = """
        Your order will be processed at our state-of-the-art facilities and dispatched within 5-7 business days.
        For premium orders exceeding €500, we expedite processing to 3-5 business days.

        Production Sites: China, Poland, Mexico, Moldova
        Distribution Centers: New York, Maryland

        For any inquiries regarding your order, please contact:
        orders@h-bu.de | +49 (0) 123 456 789
        """
        story.append(Paragraph(production_text, styles['Normal']))

        # Build PDF
        doc.build(story)

        return pdf_path

    def integrate_with_email_system(self, email_data: Dict[str, Any]) -> bool:
        """Integrate generated email with existing email processing system"""
        try:
            # This would typically save to the email processing queue
            # For now, we'll simulate by logging the email

            print(f"📧 Generated Order Email:")
            print(f"   From: {email_data['from']}")
            print(f"   To: {email_data['to']}")
            print(f"   Subject: {email_data['subject']}")
            print(f"   Order Amount: €{email_data.get('order_amount', 'N/A')}")
            print(f"   Priority: {email_data['priority']}")
            print(f"   PDF Attachment: {email_data['attachments_list'][0]['name'] if email_data['attachments_list'] else 'None'}")

            # TODO: Integrate with actual email processing system
            # This could involve:
            # 1. Adding to email queue database
            # 2. Triggering email processing workflow
            # 3. Sending actual email via SMTP
            # 4. Updating email history for dashboard display

            return True

        except Exception as e:
            print(f"Error integrating email with system: {e}")
            return False


# Global instance
order_email_generator = OrderEmailGenerator()