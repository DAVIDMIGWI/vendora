"""Script to seed database with sample data"""
from app import create_app
from models import db
from models.user import User
from models.vendor import Vendor
from models.category import Category
from models.product import Product
from decimal import Decimal

def seed_data():
    """Add sample data to database"""
    app = create_app('development')
    
    with app.app_context():
        print("🌱 Seeding database with sample data...\n")
        
        # Create Categories
        print("Creating categories...")
        categories_data = [
            {'name': 'Mama Mboga', 'slug': 'mama-mboga'},
            {'name': 'Fruits', 'slug': 'fruits'},
            {'name': 'Butcher', 'slug': 'butcher'},
            {'name': 'Kiosk', 'slug': 'kiosk'},
            {'name': 'Bakery', 'slug': 'bakery'},
        ]
        
        categories = {}
        for cat_data in categories_data:
            category = Category.query.filter_by(slug=cat_data['slug']).first()
            if not category:
                category = Category(name=cat_data['name'], slug=cat_data['slug'])
                db.session.add(category)
                db.session.flush()
            categories[cat_data['slug']] = category
            print(f"  ✓ {category.name}")
        
        db.session.commit()
        
        # Create Sample Buyers
        print("\nCreating buyers...")
        buyers_data = [
            {
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': '0712345678',
                'password': 'password123'
            },
            {
                'name': 'Jane Smith',
                'email': 'jane@example.com',
                'phone': '0723456789',
                'password': 'password123'
            }
        ]
        
        buyers = []
        for buyer_data in buyers_data:
            user = User.query.filter_by(email=buyer_data['email']).first()
            if not user:
                user = User(
                    name=buyer_data['name'],
                    email=buyer_data['email'],
                    phone=buyer_data['phone'],
                    role='BUYER'
                )
                user.set_password(buyer_data['password'])
                db.session.add(user)
                buyers.append(user)
                print(f"  ✓ {user.name} ({user.email})")
            else:
                buyers.append(user)
                print(f"  - {user.name} already exists")
        
        db.session.commit()
        
        # Create Sample Vendors
        print("\nCreating vendors...")
        vendors_data = [
            {
                'name': 'Mary Wanjiku',
                'email': 'mary@vendor.com',
                'phone': '0734567890',
                'password': 'vendor123',
                'shop_name': 'Fresh Greens Market',
                'business_type': 'Mama Mboga',
                'location': 'Westlands, Nairobi',
                'working_hours': 'Mon-Sat 6AM-8PM',
                'delivery_note': 'Fresh vegetables delivered daily. Minimum order KSh 200.',
                'status': 'APPROVED'
            },
            {
                'name': 'Peter Kamau',
                'email': 'peter@vendor.com',
                'phone': '0745678901',
                'password': 'vendor123',
                'shop_name': 'Kamau Butchery & More',
                'business_type': 'Butcher & Kiosk',
                'location': 'Kilimani, Nairobi',
                'working_hours': 'Mon-Sun 7AM-9PM',
                'delivery_note': 'Fresh meat and groceries. Free delivery for orders above KSh 500.',
                'status': 'APPROVED'
            }
        ]
        
        vendors = []
        for vendor_data in vendors_data:
            user = User.query.filter_by(email=vendor_data['email']).first()
            if not user:
                user = User(
                    name=vendor_data['name'],
                    email=vendor_data['email'],
                    phone=vendor_data['phone'],
                    role='VENDOR'
                )
                user.set_password(vendor_data['password'])
                db.session.add(user)
                db.session.flush()
                
                vendor = Vendor(
                    user_id=user.id,
                    shop_name=vendor_data['shop_name'],
                    business_type=vendor_data['business_type'],
                    phone=vendor_data['phone'],
                    location=vendor_data['location'],
                    working_hours=vendor_data['working_hours'],
                    delivery_note=vendor_data['delivery_note'],
                    status=vendor_data['status'],
                    is_online=True
                )
                db.session.add(vendor)
                vendors.append(vendor)
                print(f"  ✓ {vendor.shop_name} - {user.name}")
            else:
                vendor = user.vendor_profile
                if vendor:
                    vendors.append(vendor)
                    print(f"  - {vendor.shop_name} already exists")
        
        db.session.commit()
        
        # Create Products for Fresh Greens Market
        print("\nCreating products for Fresh Greens Market...")
        fresh_greens_products = [
            {
                'name': 'Fresh Sukuma Wiki (Kales)',
                'description': 'Fresh, organic sukuma wiki, perfect for your daily meals',
                'category': 'mama-mboga',
                'price': 50.00,
                'unit': 'bunch'
            },
            {
                'name': 'Tomatoes',
                'description': 'Fresh, ripe tomatoes from local farms',
                'category': 'mama-mboga',
                'price': 120.00,
                'unit': 'kg'
            },
            {
                'name': 'Onions',
                'description': 'Fresh red onions, perfect for cooking',
                'category': 'mama-mboga',
                'price': 100.00,
                'unit': 'kg'
            },
            {
                'name': 'Carrots',
                'description': 'Fresh, sweet carrots',
                'category': 'mama-mboga',
                'price': 80.00,
                'unit': 'kg'
            },
            {
                'name': 'Cabbage',
                'description': 'Fresh, crisp cabbage',
                'category': 'mama-mboga',
                'price': 60.00,
                'unit': 'piece'
            },
            {
                'name': 'Spinach',
                'description': 'Fresh, green spinach leaves',
                'category': 'mama-mboga',
                'price': 40.00,
                'unit': 'bunch'
            },
            {
                'name': 'Bananas',
                'description': 'Sweet, ripe bananas',
                'category': 'fruits',
                'price': 150.00,
                'unit': 'bunch'
            },
            {
                'name': 'Oranges',
                'description': 'Fresh, juicy oranges',
                'category': 'fruits',
                'price': 200.00,
                'unit': 'kg'
            }
        ]
        
        if vendors:
            vendor1 = vendors[0]
            for prod_data in fresh_greens_products:
                product = Product.query.filter_by(
                    vendor_id=vendor1.id,
                    name=prod_data['name']
                ).first()
                if not product:
                    product = Product(
                        vendor_id=vendor1.id,
                        category_id=categories[prod_data['category']].id if prod_data['category'] in categories else None,
                        name=prod_data['name'],
                        description=prod_data['description'],
                        price=Decimal(str(prod_data['price'])),
                        unit=prod_data['unit'],
                        is_active=True
                    )
                    db.session.add(product)
                    print(f"  ✓ {product.name} - KSh {product.price}/{product.unit}")
            
            db.session.commit()
        
        # Create Products for Kamau Butchery
        print("\nCreating products for Kamau Butchery & More...")
        butchery_products = [
            {
                'name': 'Beef Stew Meat',
                'description': 'Fresh, tender beef cut for stewing',
                'category': 'butcher',
                'price': 450.00,
                'unit': 'kg'
            },
            {
                'name': 'Chicken Whole',
                'description': 'Fresh whole chicken, ready to cook',
                'category': 'butcher',
                'price': 350.00,
                'unit': 'piece'
            },
            {
                'name': 'Minced Meat',
                'description': 'Freshly minced beef',
                'category': 'butcher',
                'price': 480.00,
                'unit': 'kg'
            },
            {
                'name': 'Bread - White Loaf',
                'description': 'Fresh white bread loaf',
                'category': 'bakery',
                'price': 80.00,
                'unit': 'loaf'
            },
            {
                'name': 'Milk - Fresh',
                'description': 'Fresh milk, 500ml',
                'category': 'kiosk',
                'price': 60.00,
                'unit': 'packet'
            },
            {
                'name': 'Eggs',
                'description': 'Fresh chicken eggs',
                'category': 'kiosk',
                'price': 300.00,
                'unit': 'tray (30 eggs)'
            },
            {
                'name': 'Cooking Oil',
                'description': 'Vegetable cooking oil, 2L',
                'category': 'kiosk',
                'price': 280.00,
                'unit': 'bottle'
            },
            {
                'name': 'Sugar',
                'description': 'White sugar, 1kg',
                'category': 'kiosk',
                'price': 120.00,
                'unit': 'kg'
            }
        ]
        
        if len(vendors) > 1:
            vendor2 = vendors[1]
            for prod_data in butchery_products:
                product = Product.query.filter_by(
                    vendor_id=vendor2.id,
                    name=prod_data['name']
                ).first()
                if not product:
                    product = Product(
                        vendor_id=vendor2.id,
                        category_id=categories[prod_data['category']].id if prod_data['category'] in categories else None,
                        name=prod_data['name'],
                        description=prod_data['description'],
                        price=Decimal(str(prod_data['price'])),
                        unit=prod_data['unit'],
                        is_active=True
                    )
                    db.session.add(product)
                    print(f"  ✓ {product.name} - KSh {product.price}/{product.unit}")
            
            db.session.commit()
        
        print("\n✅ Sample data seeded successfully!")
        print("\n📋 Sample Accounts:")
        print("\n👥 Buyers:")
        print("  • john@example.com")
        print("  • jane@example.com")
        print("\n🏪 Vendors:")
        print("  • mary@vendor.com (Fresh Greens Market)")
        print("  • peter@vendor.com (Kamau Butchery & More)")
        print("\n👑 Admin:")
        print("  • (create via VENDORA_BOOTSTRAP_ADMIN_EMAIL / VENDORA_BOOTSTRAP_ADMIN_PASSWORD)")

if __name__ == '__main__':
    seed_data()

