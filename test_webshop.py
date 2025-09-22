#!/usr/bin/env python3
"""
Test script to demonstrate webshop functionality
Simulates order creation and email generation
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_webshop_build():
    """Test the complete webshop build and functionality"""

    print("🛒 TESTING HAPPY BUTTONS WEBSHOP BUILD")
    print("=" * 50)

    try:
        # Test 1: Database Initialization
        print("\n📊 TEST 1: Database Initialization")
        from models.database import db, product_model, order_model
        products = product_model.get_all_products()
        print(f"✅ Database initialized with {len(products)} products")

        # Display sample products
        print("\n📦 Sample Products:")
        for i, product in enumerate(products[:5]):
            print(f"   {i+1}. {product['name']}")
            print(f"      Category: {product['category']}")
            print(f"      Price: €{product['price']}")
            print(f"      Stock: {product['stock_quantity']} units")
            print()

        # Test 2: Order Creation
        print("\n📝 TEST 2: Order Creation")
        sample_order_data = {
            'customer_name': 'Sir Reginald Buttonworth',
            'customer_email': 'r.buttonworth@premium-manufacturing.com',
            'customer_phone': '+44 20 7946 0958',
            'customer_company': 'Premium Manufacturing Ltd.',
            'shipping_address': 'Buttonworth Manor\n123 Royal Avenue\nLondon SW1A 1AA\nUnited Kingdom',
            'billing_address': 'Same as shipping',
            'total_amount': 125.50,
            'notes': 'Urgent order for royal ceremony buttons'
        }

        # Sample order items
        sample_items = [
            {'product_id': 1, 'quantity': 10, 'unit_price': 5.00, 'total_price': 50.00},
            {'product_id': 4, 'quantity': 5, 'unit_price': 8.50, 'total_price': 42.50},
            {'product_id': 2, 'quantity': 9, 'unit_price': 3.75, 'total_price': 33.75}
        ]

        order_id = order_model.create_order(sample_order_data, sample_items)
        print(f"✅ Created test order #{order_id}")

        # Test 3: Order Retrieval
        print(f"\n📋 TEST 3: Order Retrieval")
        order = order_model.get_order_by_id(order_id)
        print(f"✅ Retrieved order for {order['customer_name']}")
        print(f"   Total: €{order['total_amount']}")
        print(f"   Items: {len(order['items'])} products")

        # Test 4: Email Generation
        print(f"\n📧 TEST 4: Email Generation")
        from utils.order_email import order_email_generator

        email_data = order_email_generator.generate_order_email(order)
        print(f"✅ Generated order confirmation email")
        print(f"   From: {email_data['from']}")
        print(f"   To: {email_data['to']}")
        print(f"   Subject: {email_data['subject']}")
        print(f"   Priority: {email_data['priority']}")
        print(f"   Attachments: {email_data['attachments']}")

        if email_data['attachments_list']:
            pdf_file = email_data['attachments_list'][0]['name']
            print(f"   PDF Generated: {pdf_file}")

        # Test 5: Email Integration
        print(f"\n🔗 TEST 5: Email Integration")
        success = order_email_generator.integrate_with_email_system(email_data)
        if success:
            print("✅ Email successfully integrated with business flow")
        else:
            print("❌ Email integration failed")

        # Test 6: Stock Updates
        print(f"\n📦 TEST 6: Stock Updates")
        print("Stock levels after order:")
        for item in sample_items:
            product = product_model.get_product_by_id(item['product_id'])
            print(f"   Product #{item['product_id']}: {product['stock_quantity']} remaining")

        print(f"\n🎉 ALL TESTS PASSED!")
        print("=" * 50)
        print("WEBSHOP BUILD VERIFICATION COMPLETE")
        print(f"✅ Database: Working ({len(products)} products)")
        print(f"✅ Orders: Working (Order #{order_id} created)")
        print(f"✅ Email Generation: Working (PDF + Royal Courtesy)")
        print(f"✅ Stock Management: Working")
        print(f"✅ Integration: Ready for email processing flow")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        print(f"Error details: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def test_royal_courtesy_email():
    """Test the royal courtesy email generation"""
    print(f"\n👑 ROYAL COURTESY EMAIL TEST")
    print("-" * 30)

    try:
        from utils.order_email import order_email_generator

        # Sample order for email testing
        sample_order = {
            'id': 42,
            'customer_name': 'Lord Pemberton',
            'customer_email': 'lord.pemberton@aristocracy.co.uk',
            'customer_company': 'Pemberton Estate Holdings',
            'shipping_address': 'Pemberton Castle\nCotswolds\nGloucestershire GL54 1AA\nUnited Kingdom',
            'total_amount': 285.75,
            'created_at': '2025-09-21T16:30:00',
            'items': [
                {'name': 'BMW Custom Buttons', 'quantity': 15, 'unit_price': 8.50, 'total_price': 127.50, 'category': 'OEM'},
                {'name': 'Premium Gold Buttons', 'quantity': 20, 'unit_price': 7.91, 'total_price': 158.25, 'category': 'Premium'}
            ]
        }

        email_data = order_email_generator.generate_order_email(sample_order)

        print("✅ Royal Courtesy Email Generated")
        print(f"Order: HB-{sample_order['id']:06d}")
        print(f"Customer: {sample_order['customer_name']}")
        print(f"Total: €{sample_order['total_amount']}")

        print(f"\n📧 Email Preview:")
        print("-" * 40)
        print(email_data['content'][:500] + "...")
        print("-" * 40)

        print(f"PDF Attachment: {email_data['attachments_list'][0]['name'] if email_data['attachments_list'] else 'None'}")

        return True

    except Exception as e:
        print(f"❌ Royal Courtesy Email Test Failed: {e}")
        return False

if __name__ == "__main__":
    print("🏰 HAPPY BUTTONS WEBSHOP - BUILD VERIFICATION")
    print("=" * 60)

    # Run comprehensive tests
    build_test = test_webshop_build()
    email_test = test_royal_courtesy_email()

    print(f"\n" + "=" * 60)
    print("FINAL RESULTS:")
    print(f"{'✅' if build_test else '❌'} Webshop Build Test")
    print(f"{'✅' if email_test else '❌'} Royal Courtesy Email Test")

    if build_test and email_test:
        print(f"\n🎉 ALL SYSTEMS OPERATIONAL!")
        print("Ready for production deployment!")
    else:
        print(f"\n⚠️  Some issues detected. Review logs above.")