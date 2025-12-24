from flask import request, jsonify
from flask_login import login_required, current_user
from models import Vendor, Product, Category
from . import api_bp

@api_bp.route('/vendors', methods=['GET'])
def get_vendors():
    """Get all approved vendors"""
    vendors = Vendor.query.filter_by(status='APPROVED', is_online=True).all()
    
    search = request.args.get('search', '')
    if search:
        vendors = [v for v in vendors if search.lower() in v.shop_name.lower()]
    
    return jsonify({
        'success': True,
        'vendors': [v.to_dict() for v in vendors]
    }), 200

@api_bp.route('/vendors/<int:vendor_id>', methods=['GET'])
def get_vendor(vendor_id):
    """Get vendor details"""
    vendor = Vendor.query.get_or_404(vendor_id)
    
    if vendor.status != 'APPROVED':
        return jsonify({'success': False, 'error': 'Vendor not available'}), 404
    
    return jsonify({
        'success': True,
        'vendor': vendor.to_dict()
    }), 200

@api_bp.route('/vendors/<int:vendor_id>/products', methods=['GET'])
def get_vendor_products(vendor_id):
    """Get vendor products"""
    vendor = Vendor.query.get_or_404(vendor_id)
    
    if vendor.status != 'APPROVED':
        return jsonify({'success': False, 'error': 'Vendor not available'}), 404
    
    products = Product.query.filter_by(vendor_id=vendor_id, is_active=True).all()
    
    category_id = request.args.get('category_id', type=int)
    if category_id:
        products = [p for p in products if p.category_id == category_id]
    
    return jsonify({
        'success': True,
        'products': [p.to_dict() for p in products]
    }), 200

@api_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories"""
    categories = Category.query.all()
    return jsonify({
        'success': True,
        'categories': [c.to_dict() for c in categories]
    }), 200

