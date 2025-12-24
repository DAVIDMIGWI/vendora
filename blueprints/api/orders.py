from flask import request, jsonify
from flask_login import login_required, current_user
from models import db, Order
from . import api_bp

@api_bp.route('/orders', methods=['GET'])
@login_required
def get_orders():
    """Get user orders"""
    if current_user.is_buyer():
        orders = Order.query.filter_by(buyer_id=current_user.id)\
            .order_by(Order.created_at.desc()).all()
    elif current_user.is_vendor() and current_user.vendor_profile:
        orders = Order.query.filter_by(vendor_id=current_user.vendor_profile.id)\
            .order_by(Order.created_at.desc()).all()
    else:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    return jsonify({
        'success': True,
        'orders': [order.to_dict() for order in orders]
    }), 200

@api_bp.route('/orders/<int:order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    """Get order details"""
    order = Order.query.get_or_404(order_id)
    
    # Check access
    if current_user.is_buyer() and order.buyer_id != current_user.id:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    if current_user.is_vendor() and current_user.vendor_profile:
        if order.vendor_id != current_user.vendor_profile.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    if not (current_user.is_buyer() or current_user.is_vendor() or current_user.is_admin()):
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    return jsonify({
        'success': True,
        'order': order.to_dict()
    }), 200

@api_bp.route('/orders', methods=['POST'])
@login_required
def create_order():
    """Create order from cart"""
    from ..buyer.routes import checkout
    return checkout()

@api_bp.route('/vendor/orders', methods=['GET'])
@login_required
def get_vendor_orders():
    """Get vendor orders"""
    if not current_user.is_vendor() or not current_user.vendor_profile:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    vendor = current_user.vendor_profile
    status_filter = request.args.get('status', '')
    
    orders_query = Order.query.filter_by(vendor_id=vendor.id)
    if status_filter:
        orders_query = orders_query.filter_by(status=status_filter)
    
    orders = orders_query.order_by(Order.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'orders': [order.to_dict() for order in orders]
    }), 200

@api_bp.route('/vendor/orders/<int:order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
    """Update order status"""
    from ..vendor.routes import update_order_status as vendor_update_order_status
    return vendor_update_order_status(order_id)

@api_bp.route('/vendor/orders/<int:order_id>/payment', methods=['POST'])
@login_required
def update_payment_status(order_id):
    """Update payment status"""
    from ..vendor.routes import update_payment_status as vendor_update_payment_status
    return vendor_update_payment_status(order_id)

@api_bp.route('/orders/<int:order_id>/mark-paid', methods=['POST'])
@login_required
def mark_order_paid(order_id):
    """Buyer marks order as paid"""
    from ..buyer.routes import mark_order_paid as buyer_mark_order_paid
    return buyer_mark_order_paid(order_id)

