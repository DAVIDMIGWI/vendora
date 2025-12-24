from datetime import datetime
from decimal import Decimal
from . import db

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id', ondelete='CASCADE'), nullable=False, index=True)
    status = db.Column(db.String(20), default='PENDING', nullable=False)  # PENDING, ACCEPTED, ON_THE_WAY, DELIVERED, CANCELLED
    payment_status = db.Column(db.String(20), default='PENDING', nullable=False)  # PENDING, PAID, NOT_PAID
    buyer_payment_claimed_at = db.Column(db.DateTime, nullable=True)  # When buyer claims to have paid
    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    delivery_fee = db.Column(db.Numeric(10, 2), nullable=True, default=None)  # Set by vendor when accepting order
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    items_removed = db.Column(db.Boolean, default=False, nullable=False)  # True if any items were removed
    delivery_address = db.Column(db.Text, nullable=False)
    delivery_instructions = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Notification tracking fields
    sms_status = db.Column(db.String(20), nullable=True)  # 'queued', 'sent', 'failed'
    sms_message_id = db.Column(db.String(100), nullable=True)
    whatsapp_status = db.Column(db.String(20), nullable=True)  # 'queued', 'sent', 'failed'
    whatsapp_message_id = db.Column(db.String(100), nullable=True)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.id}>'
    
    def calculate_total(self):
        """Calculate order total from items (excluding removed items)"""
        # Handle both dynamic and regular relationships
        items_list = list(self.items) if hasattr(self.items, '__iter__') else self.items.all()
        self.subtotal = sum(item.unit_price_snapshot * item.quantity for item in items_list if not item.is_removed)
        delivery_fee = self.delivery_fee or Decimal('0.00')
        self.total = self.subtotal + delivery_fee
        return self.total
    
    def to_dict(self):
        return {
            'id': self.id,
            'buyer_id': self.buyer_id,
            'vendor_id': self.vendor_id,
            'status': self.status,
            'payment_status': self.payment_status,
            'buyer_payment_claimed_at': self.buyer_payment_claimed_at.isoformat() if self.buyer_payment_claimed_at else None,
            'subtotal': str(self.subtotal),
            'delivery_fee': str(self.delivery_fee) if self.delivery_fee else None,
            'total': str(self.total),
            'items_removed': self.items_removed,
            'delivery_address': self.delivery_address,
            'delivery_instructions': self.delivery_instructions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='SET NULL'), nullable=True)
    product_name_snapshot = db.Column(db.String(200), nullable=False)
    unit_price_snapshot = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    is_removed = db.Column(db.Boolean, default=False, nullable=False)  # True if vendor removed this item
    removed_at = db.Column(db.DateTime, nullable=True)  # When item was removed
    
    def __repr__(self):
        return f'<OrderItem {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name_snapshot': self.product_name_snapshot,
            'unit_price_snapshot': str(self.unit_price_snapshot),
            'quantity': self.quantity,
            'is_removed': self.is_removed,
            'removed_at': self.removed_at.isoformat() if self.removed_at else None
        }

