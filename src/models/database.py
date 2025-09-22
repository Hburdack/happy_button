"""
Database models for Happy Buttons Webshop
Royal Courtesy Business Intelligence System
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
import json

class Database:
    """Database manager for Happy Buttons webshop and business intelligence"""

    def __init__(self, db_path: str = "happy_buttons.db"):
        self.db_path = os.path.join(os.path.dirname(__file__), '..', '..', db_path)
        self.init_database()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Initialize all database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                stock_quantity INTEGER NOT NULL DEFAULT 0,
                description TEXT,
                image_url TEXT,
                specifications TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                customer_email TEXT NOT NULL,
                customer_phone TEXT,
                customer_company TEXT,
                shipping_address TEXT NOT NULL,
                billing_address TEXT,
                total_amount DECIMAL(10,2) NOT NULL,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Order items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                total_price DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

        # Teams table for human representation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                department TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                photo_url TEXT,
                email TEXT,
                phone TEXT,
                supervisor_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supervisor_id) REFERENCES teams(id)
            )
        ''')

        # KPIs table for business intelligence
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kpis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                value DECIMAL(10,4) NOT NULL,
                target DECIMAL(10,4) NOT NULL,
                department TEXT,
                category TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

        # Initialize sample data
        self.init_sample_data()

    def init_sample_data(self):
        """Initialize sample products and teams"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if products already exist
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            self.insert_sample_products()

        # Check if teams already exist
        cursor.execute("SELECT COUNT(*) FROM teams")
        if cursor.fetchone()[0] == 0:
            self.insert_sample_teams()

        # Check if KPIs already exist
        cursor.execute("SELECT COUNT(*) FROM kpis")
        if cursor.fetchone()[0] == 0:
            self.insert_sample_kpis()

        conn.close()

    def insert_sample_products(self):
        """Insert sample Happy Buttons products"""
        products = [
            {
                'name': 'Navy Blue Premium Buttons',
                'category': 'Premium',
                'price': 2.50,
                'stock_quantity': 5000,
                'description': 'High-quality navy blue buttons perfect for premium garments. Made from durable materials with royal finish.',
                'specifications': '{"diameter": "15mm", "material": "Premium Plastic", "color": "Navy Blue", "finish": "Glossy"}'
            },
            {
                'name': 'Custom Logo Buttons',
                'category': 'Custom',
                'price': 5.00,
                'stock_quantity': 2500,
                'description': 'Customizable buttons with your company logo. Perfect for corporate apparel and branding.',
                'specifications': '{"diameter": "20mm", "material": "Metal", "customization": "Logo Embossing", "min_order": "500 units"}'
            },
            {
                'name': 'Eco-Friendly Wooden Buttons',
                'category': 'Eco-Friendly',
                'price': 3.75,
                'stock_quantity': 3200,
                'description': 'Sustainable wooden buttons made from responsibly sourced materials. Perfect for eco-conscious brands.',
                'specifications': '{"diameter": "18mm", "material": "Sustainable Wood", "finish": "Natural", "certification": "FSC Certified"}'
            },
            {
                'name': 'BMW Custom Buttons',
                'category': 'OEM',
                'price': 8.50,
                'stock_quantity': 1500,
                'description': 'Exclusive OEM buttons for BMW corporate apparel. Premium quality with BMW specifications.',
                'specifications': '{"diameter": "22mm", "material": "Premium Metal", "color": "BMW Blue", "logo": "BMW Embossed"}'
            },
            {
                'name': 'Audi Signature Buttons',
                'category': 'OEM',
                'price': 9.00,
                'stock_quantity': 1200,
                'description': 'High-end signature buttons for Audi corporate collections. Precision engineered to Audi standards.',
                'specifications': '{"diameter": "20mm", "material": "Titanium Alloy", "color": "Audi Silver", "logo": "Four Rings"}'
            },
            {
                'name': 'Standard White Buttons',
                'category': 'Standard',
                'price': 1.25,
                'stock_quantity': 10000,
                'description': 'Classic white buttons for everyday use. Reliable quality at an affordable price.',
                'specifications': '{"diameter": "12mm", "material": "Standard Plastic", "color": "White", "finish": "Matte"}'
            },
            {
                'name': 'Black Formal Buttons',
                'category': 'Formal',
                'price': 2.00,
                'stock_quantity': 7500,
                'description': 'Elegant black buttons for formal wear. Perfect for suits, blazers, and professional attire.',
                'specifications': '{"diameter": "16mm", "material": "Premium Plastic", "color": "Deep Black", "finish": "Satin"}'
            },
            {
                'name': 'Colorful Kids Buttons',
                'category': 'Kids',
                'price': 1.75,
                'stock_quantity': 6000,
                'description': 'Fun and colorful buttons for children\'s clothing. Safe, durable, and vibrant colors.',
                'specifications': '{"diameter": "14mm", "material": "Child-Safe Plastic", "colors": "Rainbow Mix", "safety": "Lead-Free"}'
            }
        ]

        conn = self.get_connection()
        cursor = conn.cursor()

        for product in products:
            cursor.execute('''
                INSERT INTO products (name, category, price, stock_quantity, description, specifications)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                product['name'], product['category'], product['price'],
                product['stock_quantity'], product['description'], product['specifications']
            ))

        conn.commit()
        conn.close()

    def insert_sample_teams(self):
        """Insert sample team members"""
        teams = [
            # Management Team
            {'name': 'Sir Charles Wellington', 'role': 'CEO', 'department': 'Management', 'email': 'c.wellington@h-bu.de'},
            {'name': 'Lady Margaret Thornfield', 'role': 'COO', 'department': 'Management', 'email': 'm.thornfield@h-bu.de'},
            {'name': 'Lord Henry Blackwood', 'role': 'CFO', 'department': 'Management', 'email': 'h.blackwood@h-bu.de'},

            # Orders Team
            {'name': 'Ms. Victoria Sterling', 'role': 'Orders Manager', 'department': 'Orders', 'email': 'v.sterling@h-bu.de'},
            {'name': 'Mr. James Pemberton', 'role': 'Order Processor', 'department': 'Orders', 'email': 'j.pemberton@h-bu.de'},
            {'name': 'Ms. Emily Ashworth', 'role': 'Order Coordinator', 'department': 'Orders', 'email': 'e.ashworth@h-bu.de'},

            # OEM Team
            {'name': 'Sir Alexander Beaumont', 'role': 'OEM Director', 'department': 'OEM', 'email': 'a.beaumont@h-bu.de'},
            {'name': 'Ms. Isabella Fairfax', 'role': 'BMW Account Manager', 'department': 'OEM', 'email': 'i.fairfax@h-bu.de'},
            {'name': 'Mr. Nicholas Hartwell', 'role': 'Audi Account Manager', 'department': 'OEM', 'email': 'n.hartwell@h-bu.de'},

            # Quality Team
            {'name': 'Dr. Eleanor Whitmore', 'role': 'Quality Director', 'department': 'Quality', 'email': 'e.whitmore@h-bu.de'},
            {'name': 'Mr. Theodore Bramwell', 'role': 'QC Inspector', 'department': 'Quality', 'email': 't.bramwell@h-bu.de'},
            {'name': 'Ms. Charlotte Kensington', 'role': 'Compliance Officer', 'department': 'Quality', 'email': 'c.kensington@h-bu.de'},

            # Support Team
            {'name': 'Ms. Penelope Brightwater', 'role': 'Support Manager', 'department': 'Support', 'email': 'p.brightwater@h-bu.de'},
            {'name': 'Mr. Oliver Westfield', 'role': 'Customer Service Rep', 'department': 'Support', 'email': 'o.westfield@h-bu.de'},
            {'name': 'Ms. Sophia Glenmore', 'role': 'Technical Support', 'department': 'Support', 'email': 's.glenmore@h-bu.de'},

            # Logistics Team
            {'name': 'Mr. Frederick Moorhouse', 'role': 'Logistics Director', 'department': 'Logistics', 'email': 'f.moorhouse@h-bu.de'},
            {'name': 'Ms. Arabella Stockton', 'role': 'Shipping Coordinator', 'department': 'Logistics', 'email': 'a.stockton@h-bu.de'},
            {'name': 'Mr. Rupert Ashford', 'role': 'Warehouse Manager', 'department': 'Logistics', 'email': 'r.ashford@h-bu.de'},
        ]

        conn = self.get_connection()
        cursor = conn.cursor()

        for team_member in teams:
            cursor.execute('''
                INSERT INTO teams (name, role, department, email)
                VALUES (?, ?, ?, ?)
            ''', (team_member['name'], team_member['role'], team_member['department'], team_member['email']))

        conn.commit()
        conn.close()

    def insert_sample_kpis(self):
        """Insert sample KPI metrics for business intelligence"""
        kpis = [
            # Business Operations KPIs
            {'metric_name': 'Auto-handled Email Share', 'value': 74.5, 'target': 70.0, 'department': 'Email Processing', 'category': 'Automation'},
            {'metric_name': 'Average Response Time (hours)', 'value': 0.8, 'target': 1.0, 'department': 'Email Processing', 'category': 'Performance'},
            {'metric_name': 'On-time Shipment Rate', 'value': 92.3, 'target': 90.0, 'department': 'Logistics', 'category': 'Operations'},
            {'metric_name': 'Customer Satisfaction Score', 'value': 98.7, 'target': 95.0, 'department': 'Support', 'category': 'Quality'},
            {'metric_name': 'Order Processing Efficiency', 'value': 95.2, 'target': 90.0, 'department': 'Orders', 'category': 'Performance'},

            # info@h-bu.de Specific KPIs
            {'metric_name': 'Email Triage Accuracy', 'value': 96.8, 'target': 95.0, 'department': 'Info Center', 'category': 'Accuracy'},
            {'metric_name': 'Royal Courtesy Compliance', 'value': 99.1, 'target': 98.0, 'department': 'Info Center', 'category': 'Quality'},
            {'metric_name': 'Daily Email Volume', 'value': 847, 'target': 1000, 'department': 'Info Center', 'category': 'Volume'},
            {'metric_name': 'Escalation Rate', 'value': 12.3, 'target': 15.0, 'department': 'Info Center', 'category': 'Efficiency'},
            {'metric_name': 'Response Time SLA Compliance', 'value': 88.9, 'target': 85.0, 'department': 'Info Center', 'category': 'Performance'},

            # Financial KPIs
            {'metric_name': 'Monthly Revenue (K€)', 'value': 2847.5, 'target': 2500.0, 'department': 'Finance', 'category': 'Revenue'},
            {'metric_name': 'Order Value Average (€)', 'value': 156.7, 'target': 150.0, 'department': 'Orders', 'category': 'Revenue'},
            {'metric_name': 'Production Efficiency', 'value': 87.4, 'target': 85.0, 'department': 'Manufacturing', 'category': 'Operations'},
            {'metric_name': 'Inventory Turnover', 'value': 4.2, 'target': 4.0, 'department': 'Logistics', 'category': 'Efficiency'},

            # Quality & Compliance KPIs
            {'metric_name': 'Product Quality Score', 'value': 99.3, 'target': 98.0, 'department': 'Quality', 'category': 'Quality'},
            {'metric_name': 'ISO Compliance Rate', 'value': 100.0, 'target': 100.0, 'department': 'Quality', 'category': 'Compliance'},
            {'metric_name': 'OEM Customer Retention', 'value': 97.8, 'target': 95.0, 'department': 'OEM', 'category': 'Retention'},
            {'metric_name': 'Premium Order Share', 'value': 34.6, 'target': 30.0, 'department': 'OEM', 'category': 'Revenue'},

            # Staff & Operations KPIs
            {'metric_name': 'Team Productivity Index', 'value': 94.1, 'target': 90.0, 'department': 'HR', 'category': 'Performance'},
            {'metric_name': 'Staff Satisfaction Score', 'value': 91.7, 'target': 88.0, 'department': 'HR', 'category': 'Satisfaction'},
            {'metric_name': 'Training Completion Rate', 'value': 96.4, 'target': 95.0, 'department': 'HR', 'category': 'Development'},

            # Technology & Innovation KPIs
            {'metric_name': 'System Uptime', 'value': 99.8, 'target': 99.5, 'department': 'IT', 'category': 'Reliability'},
            {'metric_name': 'Digital Process Adoption', 'value': 82.3, 'target': 80.0, 'department': 'IT', 'category': 'Innovation'},
            {'metric_name': 'Data Processing Accuracy', 'value': 99.6, 'target': 99.0, 'department': 'IT', 'category': 'Accuracy'}
        ]

        conn = self.get_connection()
        cursor = conn.cursor()

        for kpi in kpis:
            cursor.execute('''
                INSERT INTO kpis (metric_name, value, target, department, category)
                VALUES (?, ?, ?, ?, ?)
            ''', (kpi['metric_name'], kpi['value'], kpi['target'], kpi['department'], kpi['category']))

        conn.commit()
        conn.close()


class ProductModel:
    """Product model for webshop"""

    def __init__(self, db: Database):
        self.db = db

    def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all products"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products ORDER BY category, name")
        products = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return products

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()

        conn.close()
        return dict(row) if row else None

    def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get products by category"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products WHERE category = ? ORDER BY name", (category,))
        products = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return products

    def update_stock(self, product_id: int, quantity_sold: int) -> bool:
        """Update stock quantity after sale"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE products
            SET stock_quantity = stock_quantity - ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND stock_quantity >= ?
        ''', (quantity_sold, product_id, quantity_sold))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success


class OrderModel:
    """Order model for webshop"""

    def __init__(self, db: Database):
        self.db = db

    def create_order(self, order_data: Dict[str, Any], items: List[Dict[str, Any]]) -> int:
        """Create new order with items"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            # Insert order
            cursor.execute('''
                INSERT INTO orders (customer_name, customer_email, customer_phone,
                                  customer_company, shipping_address, billing_address,
                                  total_amount, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order_data['customer_name'], order_data['customer_email'],
                order_data.get('customer_phone'), order_data.get('customer_company'),
                order_data['shipping_address'], order_data.get('billing_address'),
                order_data['total_amount'], order_data.get('notes')
            ))

            order_id = cursor.lastrowid

            # Insert order items
            for item in items:
                cursor.execute('''
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?)
                ''', (order_id, item['product_id'], item['quantity'],
                     item['unit_price'], item['total_price']))

            conn.commit()
            return order_id

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get order with items by ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Get order details
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order_row = cursor.fetchone()

        if not order_row:
            conn.close()
            return None

        order = dict(order_row)

        # Get order items
        cursor.execute('''
            SELECT oi.*, p.name, p.category
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order_id,))

        order['items'] = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return order

    def update_order_status(self, order_id: int, status: str) -> bool:
        """Update order status"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE orders
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, order_id))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success


class TeamModel:
    """Team member management model"""

    def __init__(self, database: Database):
        self.db = database

    def get_all_teams(self) -> List[Dict[str, Any]]:
        """Get all team members"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM teams
            ORDER BY department, role
        ''')

        teams = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return teams

    def get_teams_by_department(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get teams organized by department"""
        teams = self.get_all_teams()
        departments = {}

        for team_member in teams:
            dept = team_member['department']
            if dept not in departments:
                departments[dept] = []
            departments[dept].append(team_member)

        return departments

    def get_team_member_by_id(self, team_id: int) -> Optional[Dict[str, Any]]:
        """Get specific team member by ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_department_stats(self) -> Dict[str, Any]:
        """Get department statistics"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                department,
                COUNT(*) as member_count,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count
            FROM teams
            GROUP BY department
            ORDER BY member_count DESC
        ''')

        stats = {}
        total_members = 0
        for row in cursor.fetchall():
            dept_data = dict(row)
            stats[dept_data['department']] = dept_data
            total_members += dept_data['member_count']

        stats['_total'] = {'total_members': total_members, 'total_departments': len(stats)}
        conn.close()

        return stats

    def search_team_members(self, query: str) -> List[Dict[str, Any]]:
        """Search team members by name, role, or department"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM teams
            WHERE name LIKE ? OR role LIKE ? OR department LIKE ?
            ORDER BY name
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    def update_team_member_status(self, team_id: int, status: str) -> bool:
        """Update team member status"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE teams
            SET status = ?
            WHERE id = ?
        ''', (status, team_id))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success


class KPIModel:
    """KPI metrics model for business intelligence"""

    def __init__(self, database: Database):
        self.db = database

    def get_all_kpis(self) -> List[Dict[str, Any]]:
        """Get all KPI metrics"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM kpis
            ORDER BY department, category, metric_name
        ''')

        kpis = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return kpis

    def get_kpis_by_department(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get KPIs organized by department"""
        kpis = self.get_all_kpis()
        departments = {}

        for kpi in kpis:
            dept = kpi['department']
            if dept not in departments:
                departments[dept] = []
            departments[dept].append(kpi)

        return departments

    def get_kpis_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get KPIs organized by category"""
        kpis = self.get_all_kpis()
        categories = {}

        for kpi in kpis:
            cat = kpi['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(kpi)

        return categories

    def get_info_center_kpis(self) -> List[Dict[str, Any]]:
        """Get KPIs specific to info@h-bu.de email processing"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM kpis
            WHERE department = 'Info Center' OR department = 'Email Processing'
            ORDER BY category, metric_name
        ''')

        kpis = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return kpis

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Get performance statistics
        cursor.execute('''
            SELECT
                COUNT(*) as total_metrics,
                AVG(CASE WHEN value >= target THEN 1.0 ELSE 0.0 END) * 100 as metrics_on_target,
                AVG((value / target) * 100) as avg_performance,
                COUNT(DISTINCT department) as departments_tracked,
                COUNT(DISTINCT category) as categories_tracked
            FROM kpis
            WHERE target > 0
        ''')

        summary = dict(cursor.fetchone())

        # Get top performing departments
        cursor.execute('''
            SELECT
                department,
                AVG((value / target) * 100) as avg_performance,
                COUNT(*) as metric_count
            FROM kpis
            WHERE target > 0
            GROUP BY department
            ORDER BY avg_performance DESC
            LIMIT 5
        ''')

        summary['top_departments'] = [dict(row) for row in cursor.fetchall()]

        # Get areas needing attention
        cursor.execute('''
            SELECT
                metric_name,
                department,
                value,
                target,
                ((value / target) * 100) as performance_percent
            FROM kpis
            WHERE value < target
            ORDER BY (value / target) ASC
            LIMIT 5
        ''')

        summary['improvement_areas'] = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return summary

    def get_business_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate business optimization recommendations"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        recommendations = []

        # Check email processing performance
        cursor.execute('''
            SELECT * FROM kpis
            WHERE department IN ('Info Center', 'Email Processing')
            AND value < target
        ''')

        underperforming_email = cursor.fetchall()
        if underperforming_email:
            recommendations.append({
                'area': 'Email Processing',
                'priority': 'High',
                'issue': f"{len(underperforming_email)} email metrics below target",
                'recommendation': 'Optimize email routing algorithms and increase automation coverage',
                'impact': 'Improved customer response times and reduced manual workload'
            })

        # Check financial performance
        cursor.execute('''
            SELECT * FROM kpis
            WHERE category = 'Revenue' AND value >= target
        ''')

        strong_revenue = cursor.fetchall()
        if len(strong_revenue) >= 2:
            recommendations.append({
                'area': 'Revenue Growth',
                'priority': 'Medium',
                'issue': 'Strong revenue performance indicates growth opportunity',
                'recommendation': 'Expand premium product line and OEM partnerships',
                'impact': 'Increased market share and higher profit margins'
            })

        # Check operational efficiency
        cursor.execute('''
            SELECT AVG((value / target) * 100) as avg_ops_performance
            FROM kpis
            WHERE category IN ('Operations', 'Efficiency')
        ''')

        ops_performance = cursor.fetchone()[0]
        if ops_performance > 95:
            recommendations.append({
                'area': 'Operational Excellence',
                'priority': 'Low',
                'issue': 'Exceptional operational performance achieved',
                'recommendation': 'Document best practices and replicate across all facilities',
                'impact': 'Standardized excellence and knowledge transfer'
            })

        # Check technology adoption
        cursor.execute('''
            SELECT * FROM kpis
            WHERE department = 'IT' AND metric_name LIKE '%Adoption%'
            AND value < target
        ''')

        tech_gaps = cursor.fetchall()
        if tech_gaps:
            recommendations.append({
                'area': 'Digital Transformation',
                'priority': 'Medium',
                'issue': 'Technology adoption gaps identified',
                'recommendation': 'Implement comprehensive digital training program',
                'impact': 'Enhanced productivity and competitive advantage'
            })

        conn.close()
        return recommendations

    def update_kpi_value(self, kpi_id: int, new_value: float) -> bool:
        """Update KPI value"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE kpis
            SET value = ?, timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_value, kpi_id))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success


# Initialize database instance
db = Database()
product_model = ProductModel(db)
order_model = OrderModel(db)
team_model = TeamModel(db)
kpi_model = KPIModel(db)