"""
Migration script to add notification tracking fields to orders and vendors tables.
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
        
        # Add notification fields to vendors table
        try:
            cursor.execute("""
                ALTER TABLE vendors 
                ADD COLUMN phone_number VARCHAR(20) NULL AFTER phone,
                ADD COLUMN whatsapp_number VARCHAR(20) NULL AFTER phone_number,
                ADD COLUMN whatsapp_opt_in BOOLEAN DEFAULT FALSE NOT NULL AFTER whatsapp_number
            """)
            connection.commit()
            print("✓ Added notification fields to vendors table")
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print("✓ Notification fields already exist in vendors table")
            else:
                print(f"⚠ Error adding columns to vendors: {e}")
        
        # Add notification tracking fields to orders table
        try:
            cursor.execute("""
                ALTER TABLE orders 
                ADD COLUMN sms_status VARCHAR(20) NULL AFTER updated_at,
                ADD COLUMN sms_message_id VARCHAR(100) NULL AFTER sms_status,
                ADD COLUMN whatsapp_status VARCHAR(20) NULL AFTER sms_message_id,
                ADD COLUMN whatsapp_message_id VARCHAR(100) NULL AFTER whatsapp_status
            """)
            connection.commit()
            print("✓ Added notification tracking fields to orders table")
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print("✓ Notification tracking fields already exist in orders table")
            else:
                print(f"⚠ Error adding columns to orders: {e}")
        
        # Migrate existing phone numbers to phone_number (E.164 format)
        try:
            cursor.execute("""
                UPDATE vendors 
                SET phone_number = CONCAT('+254', SUBSTRING(phone, 2))
                WHERE phone IS NOT NULL 
                AND phone LIKE '0%' 
                AND phone_number IS NULL
            """)
            connection.commit()
            updated = cursor.rowcount
            if updated > 0:
                print(f"✓ Migrated {updated} phone numbers to E.164 format")
        except Exception as e:
            print(f"⚠ Error migrating phone numbers: {e}")
    
    connection.close()
    print("\n✅ Migration complete!")
    
except Exception as e:
    print(f"\n❌ Migration failed: {e}")

