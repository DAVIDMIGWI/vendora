#!/usr/bin/python3
import sys
import os

# Add the project directory to the path
sys.path.insert(0, '/var/www/vendora')

# Set environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ['DATABASE_URL'] = 'mysql+pymysql://vendora_user:Vendora2024@localhost/vendora'

from app import create_app
application = create_app('production')

if __name__ == "__main__":
    application.run()

