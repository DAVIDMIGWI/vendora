"""Script to create MySQL database VENDORA if it doesn't exist"""
import pymysql
import sys

# Database configuration
DB_NAME = 'VENDORA'
DB_USER = 'root'
DB_PASSWORD = 'password'  # Update this with your MySQL password
DB_HOST = 'localhost'

def create_database():
    """Create VENDORA database in MySQL"""
    try:
        print(f"🔧 Connecting to MySQL server...")
        # Connect to MySQL server (without database)
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4'
        )
        
        print(f"✓ Connected to MySQL server")
        
        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            print(f"📦 Creating database '{DB_NAME}'...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            connection.commit()
            
            # Verify database was created
            cursor.execute("SHOW DATABASES LIKE %s", (DB_NAME,))
            result = cursor.fetchone()
            
            if result:
                print(f"✅ Database '{DB_NAME}' created successfully!")
            else:
                print(f"❌ Failed to create database '{DB_NAME}'")
                return False
        
        connection.close()
        return True
        
    except pymysql.err.OperationalError as e:
        if e.args[0] == 2003:
            print(f"❌ Error: Cannot connect to MySQL server on '{DB_HOST}'")
            print("   Please ensure MySQL server is running:")
            print("   • macOS (Homebrew): brew services start mysql")
            print("   • macOS (MySQL): sudo /usr/local/mysql/support-files/mysql.server start")
        elif e.args[0] == 1045:
            print(f"❌ Error: Access denied for user '{DB_USER}'")
            print("   Please update DB_PASSWORD in setup_db.py with your MySQL root password")
        else:
            print(f"❌ MySQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("MySQL Database Setup for Vendora")
    print("=" * 50)
    print()
    
    if create_database():
        print()
        print("🎉 Setup complete! You can now run:")
        print("   python3 seed_data.py  # Add sample data")
        print("   python3 app.py         # Start the server")
    else:
        print()
        print("💡 Tip: Update DB_PASSWORD in setup_db.py if your MySQL password is different")
        sys.exit(1)

