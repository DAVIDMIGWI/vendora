from flask import request, jsonify
from flask_login import login_user, current_user
from models import db, User, Vendor
from . import api_bp

@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """API endpoint for login - redirects to auth.login which handles JSON"""
    from ..auth.routes import login as auth_login
    return auth_login()

@api_bp.route('/auth/register/buyer', methods=['POST'])
def api_register_buyer():
    """API endpoint for buyer registration"""
    from ..auth.routes import register_buyer
    return register_buyer()

@api_bp.route('/auth/register/vendor', methods=['POST'])
def api_register_vendor():
    """API endpoint for vendor registration"""
    from ..auth.routes import register_vendor
    return register_vendor()

@api_bp.route('/auth/me', methods=['GET'])
def api_get_current_user():
    """Get current authenticated user"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    user_data = {
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email,
        'phone': current_user.phone,
        'role': current_user.role
    }
    
    if current_user.is_vendor() and current_user.vendor_profile:
        user_data['vendor'] = current_user.vendor_profile.to_dict()
    
    return jsonify({'success': True, 'user': user_data}), 200

