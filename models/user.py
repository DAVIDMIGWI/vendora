from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='BUYER')  # ADMIN, VENDOR, BUYER
    # Address fields for buyers
    primary_address = db.Column(db.Text, nullable=True)
    primary_estate = db.Column(db.String(100), nullable=True)
    primary_street = db.Column(db.String(255), nullable=True)
    # Location coordinates for distance calculation
    latitude = db.Column(db.Numeric(10, 8), nullable=True)
    longitude = db.Column(db.Numeric(11, 8), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    vendor_profile = db.relationship('Vendor', backref='user', uselist=False, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='buyer', lazy='dynamic', foreign_keys='Order.buyer_id')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'ADMIN'
    
    def is_vendor(self):
        return self.role == 'VENDOR'
    
    def is_buyer(self):
        return self.role == 'BUYER'
    
    def __repr__(self):
        return f'<User {self.email}>'

