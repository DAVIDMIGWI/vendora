from datetime import datetime
from . import db

class Vendor(db.Model):
    __tablename__ = 'vendors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    shop_name = db.Column(db.String(200), nullable=False)
    business_type = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)  # Legacy field, use phone_number for E.164
    phone_number = db.Column(db.String(20), nullable=True)  # E.164 format (e.g., +254712345678) for SMS
    whatsapp_number = db.Column(db.String(20), nullable=True)  # E.164 format for WhatsApp
    whatsapp_opt_in = db.Column(db.Boolean, default=False, nullable=False)  # WhatsApp opt-in status
    location = db.Column(db.String(255), nullable=True)  # General location/area
    # Detailed location information
    street_address = db.Column(db.String(255), nullable=True)  # Street name and number
    building_name = db.Column(db.String(200), nullable=True)  # Building/complex name
    landmark = db.Column(db.String(200), nullable=True)  # Nearby landmark
    area = db.Column(db.String(100), nullable=True)  # Area/estate name
    city = db.Column(db.String(100), nullable=True)  # City name
    # Location coordinates for distance calculation
    latitude = db.Column(db.Numeric(10, 8), nullable=True)
    longitude = db.Column(db.Numeric(11, 8), nullable=True)
    status = db.Column(db.String(20), default='PENDING', nullable=False)  # PENDING, APPROVED, BLOCKED
    delivery_note = db.Column(db.Text, nullable=True)
    payment_instructions = db.Column(db.Text, nullable=True)  # Payment instructions for buyers
    working_hours = db.Column(db.String(100), nullable=True)
    is_online = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='vendor', lazy='dynamic', cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='vendor', lazy='dynamic', foreign_keys='Order.vendor_id')
    
    def __repr__(self):
        return f'<Vendor {self.shop_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'shop_name': self.shop_name,
            'business_type': self.business_type,
            'phone': self.phone,
            'location': self.location,
            'status': self.status,
            'delivery_note': self.delivery_note,
            'payment_instructions': self.payment_instructions,
            'working_hours': self.working_hours,
            'is_online': self.is_online,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

