from flask import request, jsonify, session
from flask_login import login_required, current_user
from models import Vendor, Product
from ..buyer.routes import get_cart, save_cart, clear_cart
from . import api_bp

@api_bp.route('/cart', methods=['GET'])
@login_required
def api_get_cart():
    """Get cart items"""
    if not current_user.is_buyer():
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    cart = get_cart()
    cart_items = []
    total = 0.0
    
    for vendor_id, items in cart.items():
        vendor = Vendor.query.get(int(vendor_id))
        if not vendor or vendor.status != 'APPROVED':
            continue
        
        vendor_items = []
        vendor_total = 0.0
        
        for item in items:
            product = Product.query.get(item['product_id'])
            if not product or not product.is_active:
                continue
            
            quantity = int(item['quantity'])
            item_total = float(product.price) * quantity
            vendor_total += item_total
            
            vendor_items.append({
                'product': product.to_dict(),
                'quantity': quantity,
                'total': item_total
            })
        
        if vendor_items:
            cart_items.append({
                'vendor': vendor.to_dict(),
                'items': vendor_items,
                'subtotal': vendor_total
            })
            total += vendor_total
    
    return jsonify({
        'success': True,
        'cart': cart_items,
        'total': total
    }), 200

@api_bp.route('/cart/add', methods=['POST'])
@login_required
def api_add_to_cart():
    """Add product to cart"""
    from ..buyer.routes import add_to_cart
    return add_to_cart()

@api_bp.route('/cart/update', methods=['POST'])
@login_required
def api_update_cart():
    """Update cart item"""
    from ..buyer.routes import update_cart
    return update_cart()

@api_bp.route('/cart/remove', methods=['POST'])
@login_required
def api_remove_from_cart():
    """Remove item from cart"""
    from ..buyer.routes import remove_from_cart
    return remove_from_cart()

@api_bp.route('/cart/clear', methods=['POST'])
@login_required
def api_clear_cart():
    """Clear cart"""
    if not current_user.is_buyer():
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    clear_cart()
    return jsonify({'success': True, 'message': 'Cart cleared'}), 200

