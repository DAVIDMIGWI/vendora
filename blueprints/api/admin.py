from flask import request, jsonify
from flask_login import login_required, current_user
from models import db, User, Vendor, Category, Order
from . import api_bp

def admin_required_api(f):
    """Decorator for admin API endpoints"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/admin/vendors', methods=['GET'])
@login_required
@admin_required_api
def api_get_vendors():
    """Get all vendors (admin)"""
    status_filter = request.args.get('status', '')
    vendors_query = Vendor.query
    
    if status_filter:
        vendors_query = vendors_query.filter_by(status=status_filter)
    
    vendors = vendors_query.order_by(Vendor.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'vendors': [v.to_dict() for v in vendors]
    }), 200

@api_bp.route('/admin/vendors/<int:vendor_id>/approve', methods=['POST'])
@login_required
@admin_required_api
def api_approve_vendor(vendor_id):
    """Approve vendor (admin)"""
    from ..admin.routes import approve_vendor
    return approve_vendor(vendor_id)

@api_bp.route('/admin/vendors/<int:vendor_id>/block', methods=['POST'])
@login_required
@admin_required_api
def api_block_vendor(vendor_id):
    """Block vendor (admin)"""
    from ..admin.routes import block_vendor
    return block_vendor(vendor_id)

@api_bp.route('/admin/orders', methods=['GET'])
@login_required
@admin_required_api
def api_get_orders():
    """Get all orders (admin)"""
    status_filter = request.args.get('status', '')
    orders_query = Order.query
    
    if status_filter:
        orders_query = orders_query.filter_by(status=status_filter)
    
    orders = orders_query.order_by(Order.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'orders': [order.to_dict() for order in orders]
    }), 200

@api_bp.route('/admin/categories', methods=['GET'])
@login_required
@admin_required_api
def api_get_categories():
    """Get all categories (admin)"""
    categories = Category.query.order_by(Category.name).all()
    return jsonify({
        'success': True,
        'categories': [c.to_dict() for c in categories]
    }), 200

@api_bp.route('/admin/categories', methods=['POST'])
@login_required
@admin_required_api
def api_create_category():
    """Create category (admin)"""
    from ..admin.routes import new_category
    return new_category()

@api_bp.route('/admin/categories/<int:category_id>', methods=['PUT'])
@login_required
@admin_required_api
def api_update_category(category_id):
    """Update category (admin)"""
    from ..admin.routes import edit_category
    return edit_category(category_id)

@api_bp.route('/admin/categories/<int:category_id>', methods=['DELETE'])
@login_required
@admin_required_api
def api_delete_category(category_id):
    """Delete category (admin)"""
    from ..admin.routes import delete_category
    return delete_category(category_id)

