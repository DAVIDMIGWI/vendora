from flask import request, jsonify
from flask_login import login_required, current_user
from models import Product
from . import api_bp

@api_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get product details"""
    product = Product.query.get_or_404(product_id)
    
    if not product.is_active:
        return jsonify({'success': False, 'error': 'Product not available'}), 404
    
    return jsonify({
        'success': True,
        'product': product.to_dict()
    }), 200

