"""
Migration script to add image_url column to products table.
Run this if you have an existing database.
"""
import pymysql
from config import config

# Get database connection info
db_config = config['development']
db_uri = db_config.SQLALCHEMY_DATABASE_URI

# Parse connection string: mysql+pymysql://root@localhost/VENDORA
# Extract database name
db_name = db_uri.split('/')[-1]

print(f"Connecting to MySQL database: {db_name}")

try:
    # Connect to MySQL (without specifying database first)
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        charset='utf8mb4'
    )
    
    with connection.cursor() as cursor:
        # Select the database
        cursor.execute(f"USE {db_name}")
        
        # Add image_url column to products table
        try:
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN image_url VARCHAR(500) NOT NULL DEFAULT 'https://via.placeholder.com/400x400?text=No+Image'
            """)
            connection.commit()
            print("✓ Added image_url column to products table")
            
            # Update existing products with placeholder images based on category
            print("\nUpdating existing products with default images...")
            cursor.execute("""
                UPDATE products 
                SET image_url = CASE 
                    WHEN category_id IN (SELECT id FROM categories WHERE slug = 'mama-mboga') 
                    THEN 'https://images.unsplash.com/photo-1622206151226-18ca2c9ab4a1?w=400&h=400&fit=crop'
                    WHEN category_id IN (SELECT id FROM categories WHERE slug = 'fruits') 
                    THEN 'https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=400&h=400&fit=crop'
                    WHEN category_id IN (SELECT id FROM categories WHERE slug = 'butcher') 
                    THEN 'https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?w=400&h=400&fit=crop'
                    WHEN category_id IN (SELECT id FROM categories WHERE slug = 'bakery') 
                    THEN 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&h=400&fit=crop'
                    ELSE 'https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=400&h=400&fit=crop'
                END
                WHERE image_url = 'https://via.placeholder.com/400x400?text=No+Image'
            """)
            connection.commit()
            print("✓ Updated existing products with category-appropriate default images")
            
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print("✓ image_url column already exists in products table")
            else:
                print(f"⚠ Error adding column to products: {e}")
    
    connection.close()
    print("\n✅ Migration complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

