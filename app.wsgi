#!/usr/bin/python3
import sys
import os

# Add the project directory to the path
sys.path.insert(0, '/var/www/vendora')

# Set environment variables
os.environ['FLASK_ENV'] = 'production'
# IMPORTANT: Configure DATABASE_URL in your server environment (Apache/Nginx/Systemd/etc).
# Do not hardcode credentials in source control.

from app import create_app
application = create_app('production')

if __name__ == "__main__":
    application.run()

