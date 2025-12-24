"""
Migration script to add latitude and longitude columns to users and vendors tables.
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
        
        # Add latitude and longitude to users table
        try:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN latitude NUMERIC(10, 8) NULL,
                ADD COLUMN longitude NUMERIC(11, 8) NULL
            """)
            connection.commit()
            print("✓ Added latitude/longitude to users table")
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print("✓ Latitude/longitude columns already exist in users table")
            else:
                print(f"⚠ Error adding columns to users: {e}")
        
        # Add latitude and longitude to vendors table
        try:
            cursor.execute("""
                ALTER TABLE vendors 
                ADD COLUMN latitude NUMERIC(10, 8) NULL,
                ADD COLUMN longitude NUMERIC(11, 8) NULL
            """)
            connection.commit()
            print("✓ Added latitude/longitude to vendors table")
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print("✓ Latitude/longitude columns already exist in vendors table")
            else:
                print(f"⚠ Error adding columns to vendors: {e}")
    
    connection.close()
    print("\n✅ Migration complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

