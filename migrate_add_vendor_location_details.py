"""
Migration script to add detailed location fields to vendors table
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
        
        # Add location detail columns to vendors table
        try:
            cursor.execute("""
                ALTER TABLE vendors
                ADD COLUMN street_address VARCHAR(255) NULL AFTER location,
                ADD COLUMN building_name VARCHAR(200) NULL AFTER street_address,
                ADD COLUMN landmark VARCHAR(200) NULL AFTER building_name,
                ADD COLUMN area VARCHAR(100) NULL AFTER landmark,
                ADD COLUMN city VARCHAR(100) NULL AFTER area
            """)
            connection.commit()
            print("✓ Added location detail columns to vendors table")
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print("✓ Location detail columns already exist in vendors table")
            else:
                print(f"⚠ Error adding columns to vendors: {e}")
    
    connection.close()
    print("\n✅ Migration complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

