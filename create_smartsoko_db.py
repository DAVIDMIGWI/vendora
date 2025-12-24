"""Script to create VENDORA MySQL database using config.py credentials"""
import pymysql
import sys
from config import DevelopmentConfig

DB_NAME = 'VENDORA'

def create_database():
    """Create VENDORA database in MySQL"""
    # Parse database URI from config
    db_uri = DevelopmentConfig.SQLALCHEMY_DATABASE_URI
    
    if not db_uri.startswith('mysql+pymysql://'):
        print("❌ Error: Database URI is not MySQL!")
        print(f"   Current URI: {db_uri}")
        print("   Please update config.py to use MySQL")
        return False
    
    # Parse: mysql+pymysql://user:password@host/database
    uri_parts = db_uri.replace('mysql+pymysql://', '').split('@')
    if len(uri_parts) != 2:
        print("❌ Error: Could not parse database URI")
        return False
    
    user_pass = uri_parts[0].split(':')
    host_db = uri_parts[1].split('/')
    
    if len(host_db) != 2:
        print("❌ Error: Could not parse database credentials")
        return False
    
    # Handle case where password might not be present
    if len(user_pass) == 2:
        username = user_pass[0]
        password = user_pass[1]
    else:
        username = user_pass[0]
        password = ''
    host = host_db[0]
    
    print("=" * 50)
    print("Creating MySQL Database: VENDORA")
    print("=" * 50)
    print(f"Host: {host}")
    print(f"User: {username}")
    print(f"Database: {DB_NAME}")
    print()
    
    try:
        print("🔧 Connecting to MySQL server...")
        # Connect to MySQL server (without database)
        connection = pymysql.connect(
            host=host,
            user=username,
            password=password if password else None,
            charset='utf8mb4'
        )
        
        print("✓ Connected to MySQL server")
        
        with connection.cursor() as cursor:
            # Check if database exists
            cursor.execute("SHOW DATABASES LIKE %s", (DB_NAME,))
            exists = cursor.fetchone()
            
            if exists:
                print(f"⚠️  Database '{DB_NAME}' already exists")
                print(f"✓ Database '{DB_NAME}' is ready to use")
                connection.close()
                return True
            
            # Create database
            print(f"📦 Creating database '{DB_NAME}'...")
            cursor.execute(f"CREATE DATABASE `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            connection.commit()
            
            # Verify
            cursor.execute("SHOW DATABASES LIKE %s", (DB_NAME,))
            result = cursor.fetchone()
            
            if result:
                print(f"✅ Database '{DB_NAME}' created successfully!")
            else:
                print(f"❌ Failed to create database")
                return False
        
        connection.close()
        return True
        
    except pymysql.err.OperationalError as e:
        if e.args[0] == 2003:
            print(f"\n❌ Error: Cannot connect to MySQL server on '{host}'")
            print("   Please ensure MySQL server is running:")
            print("   • macOS (Homebrew): brew services start mysql")
            print("   • macOS (MySQL): sudo /usr/local/mysql/support-files/mysql.server start")
            print("   • Linux: sudo systemctl start mysql")
        elif e.args[0] == 1045:
            print(f"\n❌ Error: Access denied for user '{username}'")
            print("   Please update the password in config.py:")
            print(f"   SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:YOUR_PASSWORD@localhost/{DB_NAME}'")
            print("\n   Or set environment variable:")
            print(f"   export DATABASE_URL='mysql+pymysql://root:YOUR_PASSWORD@localhost/{DB_NAME}'")
        else:
            print(f"\n❌ MySQL Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == '__main__':
    if create_database():
        print("\n🎉 Database setup complete!")
        print("\nNext steps:")
        print("  1. Run: python3 seed_data.py  # Add sample data")
        print("  2. Run: python3 app.py         # Start the server")
    else:
        print("\n❌ Database setup failed.")
        print("\n💡 Make sure:")
        print("   1. MySQL server is running")
        print("   2. Password in config.py is correct")
        sys.exit(1)
