import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://vendora_user:Vendora2024@localhost/vendora'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # File upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Google Maps API configuration
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY') or 'AIzaSyBRMnM2f1xdamvC2ylOnWJQPfeejubsfBo'
    
    # Africa's Talking API configuration
    AT_USERNAME = os.environ.get('AT_USERNAME') or ''
    AT_API_KEY = os.environ.get('AT_API_KEY') or ''
    AT_ENV = os.environ.get('AT_ENV', 'sandbox')  # 'sandbox' or 'live'
    # Sender ID for SMS - only set if you have an approved Sender ID
    # Leave empty/None to use default (recommended for testing)
    AT_SMS_FROM = os.environ.get('AT_SMS_FROM') or None
    AT_WHATSAPP_TEMPLATE_NAME = os.environ.get('AT_WHATSAPP_TEMPLATE_NAME', 'order_notification')
    AT_WHATSAPP_URL = os.environ.get('AT_WHATSAPP_URL') or ''  # WhatsApp API endpoint URL

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://vendora_user:Vendora2024@localhost/vendora'

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://vendora_user:Vendora2024@localhost/vendora'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

