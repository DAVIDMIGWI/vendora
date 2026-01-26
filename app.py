import os
import logging
from flask import Flask, redirect, url_for, render_template, request, jsonify, session, flash, send_from_directory, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, date, timedelta
from decimal import Decimal
from functools import wraps
from sqlalchemy import func
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from config import config
from models import db, User, Vendor, Product, Category, Order, OrderItem
from utils import get_vendors_within_radius, calculate_distance, send_email_smtp
from upload_utils import save_product_image, delete_product_image, allowed_file

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Password reset token settings
RESET_PASSWORD_TOKEN_SALT = 'vendora-reset-password'
RESET_PASSWORD_TOKEN_MAX_AGE_SECONDS = 600  # 10 minutes

# Session key for cart
CART_SESSION_KEY = 'cart'

# Helper functions for cart
def get_cart():
    """Get cart from session"""
    return session.get(CART_SESSION_KEY, {})

def save_cart(cart):
    """Save cart to session"""
    session[CART_SESSION_KEY] = cart

def clear_cart():
    """Clear cart from session"""
    session.pop(CART_SESSION_KEY, None)

def get_cart_count():
    """Get total number of items in cart"""
    cart = get_cart()
    count = 0
    for vendor_id, items in cart.items():
        count += len(items)
    return count

# Decorators
def vendor_required(f):
    """Decorator to ensure user is a vendor - allows PENDING vendors to access dashboard"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Access denied', 'error')
            return redirect(url_for('login'))
        
        # Check if user has vendor profile
        if not current_user.vendor_profile:
            flash('You need to register as a vendor first', 'error')
            return redirect(url_for('register_vendor'))
        
        # Block BLOCKED vendors
        if current_user.vendor_profile.status == 'BLOCKED':
            flash('Your vendor account has been blocked', 'error')
            return redirect(url_for('login'))
        
        # Allow APPROVED and PENDING vendors (dashboard will show appropriate messages)
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to ensure user is admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Access denied', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required_api(f):
    """Decorator for admin API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return User.query.get(int(user_id))

def create_app(config_name='default'):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Ensure upload folder exists
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder:
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(os.path.join(upload_folder, 'products'), exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Temporarily re-register blueprints until all routes are consolidated
    from blueprints.buyer import buyer_bp
    from blueprints.vendor import vendor_bp
    from blueprints.admin import admin_bp
    from blueprints.api import api_bp
    
    app.register_blueprint(buyer_bp)
    app.register_blueprint(vendor_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    
    # Context processor for cart count and config (available in all templates)
    @app.context_processor
    def inject_globals():
        """Make cart count and config available in all templates"""
        cart_count = 0
        if current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated and current_user.can_be_buyer():
            cart_count = get_cart_count()
        return {
            'cart_count': cart_count,
            'config': app.config
        }
    
    # Favicon route
    @app.route('/favicon.ico')
    def favicon():
        """Serve favicon"""
        from flask import send_from_directory
        return send_from_directory(app.static_folder, 'favicon.svg', mimetype='image/svg+xml')
    
    # ============================================================================
    # AUTHENTICATION ROUTES
    # ============================================================================
    
    @app.route('/register/buyer', methods=['GET', 'POST'])
    def register_buyer():
        """Register as buyer"""
        # If user is already logged in, redirect them to their dashboard
        if current_user.is_authenticated:
            if current_user.is_admin():
                return redirect(url_for('admin_dashboard'))
            elif current_user.can_be_vendor() and session.get('active_role') == 'vendor':
                return redirect(url_for('vendor_dashboard'))
            else:
                return redirect(url_for('buyer_home'))
        
        if request.method == 'POST':
            data = request.get_json() if request.is_json else None
            
            name = data.get('name') if data else request.form.get('name')
            email = data.get('email') if data else request.form.get('email')
            phone = data.get('phone') if data else request.form.get('phone')
            password = data.get('password') if data else request.form.get('password')
            
            if not all([name, email, password]):
                error = 'Name, email, and password are required'
                if data:
                    return jsonify({'success': False, 'error': error}), 400
                flash(error, 'error')
                return render_template('auth/register_buyer.html')
            
            if User.query.filter_by(email=email).first():
                error = 'Email already registered'
                if data:
                    return jsonify({'success': False, 'error': error}), 400
                flash(error, 'error')
                return render_template('auth/register_buyer.html')
            
            user = User(name=name, email=email, phone=phone, role='BUYER')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            login_user(user, remember=True)
            session['active_role'] = 'buyer'  # Set default role for new buyer
            
            if data:
                return jsonify({
                    'success': True,
                    'message': 'Registration successful',
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'email': user.email,
                        'role': user.role
                    }
                }), 201
            
        # Redirect to buyer dashboard/home
        return redirect(url_for('buyer.home'))
        
        return render_template('auth/register_buyer.html')
    
    @app.route('/register/vendor', methods=['GET', 'POST'])
    def register_vendor():
        """Register as vendor"""
        # If user is already logged in and has vendor profile, redirect to vendor dashboard
        if current_user.is_authenticated:
            if current_user.vendor_profile:
                return redirect(url_for('vendor_dashboard'))
            elif current_user.is_admin():
                return redirect(url_for('admin_dashboard'))
            # Allow logged-in buyers to register as vendors, so continue
        
        if request.method == 'POST':
            data = request.get_json() if request.is_json else None
            
            name = data.get('name') if data else request.form.get('name')
            email = data.get('email') if data else request.form.get('email')
            phone = data.get('phone') if data else request.form.get('phone')
            password = data.get('password') if data else request.form.get('password')
            shop_name = data.get('shop_name') if data else request.form.get('shop_name')
            business_type = data.get('business_type') if data else request.form.get('business_type')
            location = data.get('location') if data else request.form.get('location')
            
            if not all([name, email, password, shop_name]):
                error = 'Name, email, password, and shop name are required'
                if data:
                    return jsonify({'success': False, 'error': error}), 400
                flash(error, 'error')
                return render_template('auth/register_vendor.html')
            
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            
            if existing_user:
                # User exists - check if they already have a vendor profile
                if existing_user.vendor_profile:
                    error = 'You already have a vendor account. Please log in instead.'
                    if data:
                        return jsonify({'success': False, 'error': error}), 400
                    flash(error, 'error')
                    return render_template('auth/register_vendor.html')
                
                # User exists but no vendor profile - verify password and add vendor profile
                if not existing_user.check_password(password):
                    error = 'Invalid password. If you want to add vendor features to your account, please use your existing password.'
                    if data:
                        return jsonify({'success': False, 'error': error}), 401
                    flash(error, 'error')
                    return render_template('auth/register_vendor.html')
                
                # Add vendor profile to existing user
                user = existing_user
                # Update user info if provided
                if name:
                    user.name = name
                if phone:
                    user.phone = phone
                # Change role to VENDOR (they can still be buyer via role selection)
                user.role = 'VENDOR'
                
                vendor = Vendor(
                    user_id=user.id,
                    shop_name=shop_name,
                    business_type=business_type,
                    phone=phone,
                    location=location,
                    status='PENDING'
                )
                db.session.add(vendor)
                db.session.commit()
                
                login_user(user, remember=True)
                # Set active role - if existing user, they might have both roles now
                if user.has_multiple_roles():
                    session['active_role'] = 'vendor'  # Default to vendor for vendor registration
                else:
                    session['active_role'] = 'vendor'
            else:
                # New user - create account
                user = User(name=name, email=email, phone=phone, role='VENDOR')
                user.set_password(password)
                db.session.add(user)
                db.session.flush()
                
                vendor = Vendor(
                    user_id=user.id,
                    shop_name=shop_name,
                    business_type=business_type,
                    phone=phone,
                    location=location,
                    status='PENDING'
                )
                db.session.add(vendor)
                db.session.commit()
                
                login_user(user, remember=True)
                session['active_role'] = 'vendor'  # Set default role for new vendor
            
            if data:
                return jsonify({
                    'success': True,
                    'message': 'Registration successful. Awaiting admin approval.',
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'email': user.email,
                        'role': user.role
                    },
                    'vendor': vendor.to_dict()
                }), 201
            
            flash('Registration successful. Awaiting admin approval.', 'info')
            # Redirect to vendor dashboard (even if pending, they can see the dashboard)
            return redirect(url_for('vendor.dashboard'))
        
        return render_template('auth/register_vendor.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login - always show login page (allows switching accounts)"""
        if request.method == 'POST':
            data = request.get_json() if request.is_json else None
            
            email = data.get('email') if data else request.form.get('email')
            password = data.get('password') if data else request.form.get('password')
            remember = data.get('remember', True) if data else request.form.get('remember', False)
            
            if not email or not password:
                error = 'Email and password are required'
                if data:
                    return jsonify({'success': False, 'error': error}), 400
                flash(error, 'error')
                return render_template('auth/login.html')
            
            user = User.query.filter_by(email=email).first()
            
            if not user or not user.check_password(password):
                error = 'Invalid email or password'
                if data:
                    return jsonify({'success': False, 'error': error}), 401
                flash(error, 'error')
                return render_template('auth/login.html')
            
            # Check vendor status
            if user.is_vendor() and user.vendor_profile:
                if user.vendor_profile.status == 'BLOCKED':
                    error = 'Your vendor account has been blocked'
                    if data:
                        return jsonify({'success': False, 'error': error}), 403
                    flash(error, 'error')
                    return render_template('auth/login.html')
                if user.vendor_profile.status == 'PENDING':
                    error = 'Your vendor account is pending approval'
                    if data:
                        return jsonify({'success': False, 'error': error}), 403
                    flash(error, 'info')
                    return render_template('auth/login.html')
            
            login_user(user, remember=bool(remember))
            
            # Set default active role in session
            if user.is_admin():
                session['active_role'] = 'admin'
            elif user.can_be_vendor():
                session['active_role'] = 'vendor'
            else:
                session['active_role'] = 'buyer'
            
            if data:
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'email': user.email,
                        'role': user.role
                    }
                }), 200
            
            # Check if user has multiple roles (can be both buyer and vendor)
            if user.has_multiple_roles():
                # Redirect to role selection page
                return redirect(url_for('select_role'))
            
            # Redirect based on role (single role users)
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            elif user.is_vendor():
                return redirect(url_for('vendor.dashboard'))
            else:
                return redirect(url_for('buyer.home'))
        
        return render_template('auth/login.html')
    
    @app.route('/select-role', methods=['GET', 'POST'])
    @login_required
    def select_role():
        """Role selection page for users who can be both buyer and vendor"""
        if request.method == 'POST':
            selected_role = request.form.get('role')
            
            if not selected_role:
                flash('Please select a role', 'error')
                return render_template('auth/select_role.html')
            
            # Validate role selection
            if selected_role == 'buyer' and not current_user.can_be_buyer():
                flash('You cannot access buyer features', 'error')
                return render_template('auth/select_role.html')
            
            if selected_role == 'vendor' and not current_user.can_be_vendor():
                flash('You cannot access vendor features. Your vendor account may be pending approval.', 'error')
                return render_template('auth/select_role.html')
            
            # Store selected role in session
            session['active_role'] = selected_role
            
            # Redirect based on selected role
            if selected_role == 'vendor':
                # Check if vendor account is approved before redirecting
                if current_user.vendor_profile and current_user.vendor_profile.status == 'APPROVED':
                    return redirect(url_for('vendor.dashboard'))
                elif current_user.vendor_profile and current_user.vendor_profile.status == 'PENDING':
                    # Allow access to dashboard even if pending (they can see pending message)
                    session['active_role'] = 'vendor'
                    return redirect(url_for('vendor.dashboard'))
                else:
                    flash('You need to register as a vendor first', 'error')
                    return redirect(url_for('register_vendor'))
            else:
                return redirect(url_for('buyer.home'))
        
        # GET request - check for role parameter (from navbar switcher)
        role_param = request.args.get('role')
        if role_param in ['buyer', 'vendor']:
            # Validate role selection
            if role_param == 'buyer':
                # All users can be buyers
                if current_user.can_be_buyer():
                    session['active_role'] = 'buyer'
                    return redirect(url_for('buyer.home'))
                else:
                    flash('Unable to switch to buyer mode', 'error')
                    return redirect(url_for('buyer.home'))
            elif role_param == 'vendor':
                # Check if user has vendor profile
                if current_user.vendor_profile:
                    session['active_role'] = 'vendor'
                    # Allow access even if pending - dashboard will show appropriate message
                    return redirect(url_for('vendor.dashboard'))
                else:
                    flash('You need to register as a vendor first', 'info')
                    # Don't redirect to register, just go back to current page or buyer home
                    if session.get('active_role') == 'buyer':
                        return redirect(url_for('buyer.home'))
                    else:
                        return redirect(url_for('register_vendor'))
        
        # Check if user actually has multiple roles
        if not current_user.has_multiple_roles():
            # If only one role, redirect directly
            if current_user.can_be_vendor():
                session['active_role'] = 'vendor'
                return redirect(url_for('vendor.dashboard'))
            else:
                session['active_role'] = 'buyer'
                return redirect(url_for('buyer.home'))
        
        return render_template('auth/select_role.html')

    def _get_reset_serializer():
        return URLSafeTimedSerializer(app.config['SECRET_KEY'])

    def _make_reset_token(user: User) -> str:
        # Include password hash so tokens are invalidated after a password change.
        return _get_reset_serializer().dumps(
            {'uid': user.id, 'email': user.email, 'pwh': user.password_hash},
            salt=RESET_PASSWORD_TOKEN_SALT
        )

    def _verify_reset_token(token: str):
        try:
            data = _get_reset_serializer().loads(
                token,
                salt=RESET_PASSWORD_TOKEN_SALT,
                max_age=RESET_PASSWORD_TOKEN_MAX_AGE_SECONDS
            )
        except (BadSignature, SignatureExpired):
            return None

        user = User.query.get(int(data.get('uid'))) if data.get('uid') else None
        if not user:
            return None
        if user.email != data.get('email'):
            return None
        if user.password_hash != data.get('pwh'):
            return None
        return user

    def _external_url(endpoint: str, **values) -> str:
        # Prefer forwarded proto (Apache proxy) so reset links use https in production.
        scheme = request.headers.get('X-Forwarded-Proto') or ('https' if request.is_secure else 'http')
        return url_for(endpoint, _external=True, _scheme=scheme, **values)

    @app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        """Request a password reset link (always responds generically)."""
        if request.method == 'POST':
            email = (request.form.get('email') or '').strip().lower()

            # Always show success to avoid account enumeration.
            generic_msg = 'If an account exists for that email, we sent a password reset link (valid for 10 minutes).'

            if email:
                user = User.query.filter_by(email=email).first()
                if user:
                    token = _make_reset_token(user)
                    reset_link = _external_url('reset_password', token=token)
                    subject = 'Reset your Vendora password (valid for 10 minutes)'
                    text = (
                        "You requested a password reset for your Vendora account.\n\n"
                        f"Reset your password using this link (valid for 10 minutes):\n{reset_link}\n\n"
                        "If you did not request this, you can ignore this email."
                    )
                    try:
                        send_email_smtp(
                            to_email=user.email,
                            subject=subject,
                            text_body=text
                        )
                    except Exception:
                        current_app.logger.exception('Failed to send password reset email')

            flash(generic_msg, 'info')
            return redirect(url_for('login'))

        return render_template('auth/forgot_password.html')

    @app.route('/reset-password/<token>', methods=['GET', 'POST'])
    def reset_password(token):
        """Reset password using a signed token (expires in 10 minutes)."""
        user = _verify_reset_token(token)
        if not user:
            flash('This password reset link is invalid or has expired. Please request a new one.', 'error')
            return redirect(url_for('forgot_password'))

        if request.method == 'POST':
            password = request.form.get('password') or ''
            confirm = request.form.get('confirm_password') or ''

            if len(password) < 8:
                flash('Password must be at least 8 characters.', 'error')
                return render_template('auth/reset_password.html', token=token)
            if password != confirm:
                flash('Passwords do not match.', 'error')
                return render_template('auth/reset_password.html', token=token)

            user.set_password(password)
            db.session.commit()
            flash('Your password has been reset. Please log in.', 'success')
            return redirect(url_for('login'))

        return render_template('auth/reset_password.html', token=token)
    
    @app.route('/logout')
    def logout():
        """Logout - completely kill session and render landing page"""
        # IMPORTANT: Clear session first, then call logout_user().
        # Flask-Login uses the session to tell the response handler to clear the "remember me" cookie.
        session.clear()
        logout_user()
        flash('You have been logged out successfully', 'info')
        return redirect(url_for('landing'))
    
    # ============================================================================
    # ROOT ROUTE - Landing page
    # ============================================================================
    
    @app.route('/')
    def landing():
        """Landing page for non-authenticated users"""
        if current_user.is_authenticated:
            if current_user.is_admin():
                return redirect(url_for('admin.dashboard'))
            elif current_user.is_vendor():
                return redirect(url_for('vendor.dashboard'))
            else:
                return redirect(url_for('buyer.home'))
        return render_template('landing.html')
    
    # ============================================================================
    # BUYER ROUTES
    # ============================================================================
    
    @app.route('/buyer/vendors')
    @login_required
    def buyer_vendors_list():
        """Vendor listing page with category and distance filters"""
        if not current_user.can_be_buyer():
            flash('Access denied', 'error')
            return redirect(url_for('login'))
        
        # Get filter parameters
        category_id = request.args.get('category', type=int)
        distance_input = request.args.get('distance', type=float, default=1.0)
        # Allow only 0.2 (200m), 0.5 (500m), or 1.0 (1km) - default to 1.0
        max_distance = 1.0 if distance_input not in [0.2, 0.5, 1.0] else distance_input
        search = request.args.get('search', '').strip()
        
        # Get all categories
        categories = Category.query.all()
        
        # Get all approved and online vendors
        all_vendors = Vendor.query.filter_by(status='APPROVED', is_online=True).all()
        
        # Filter by category if provided
        if category_id:
            # Get vendors that have products in this category
            vendor_ids = db.session.query(Product.vendor_id).filter_by(
                category_id=category_id, is_active=True
            ).distinct().all()
            vendor_ids = [v[0] for v in vendor_ids]
            all_vendors = [v for v in all_vendors if v.id in vendor_ids]
        
        # Filter by search term if provided
        if search:
            search_lower = search.lower()
            all_vendors = [
                v for v in all_vendors
                if (search_lower in v.shop_name.lower() or
                    (v.business_type and search_lower in v.business_type.lower()) or
                    (v.location and search_lower in v.location.lower()))
            ]
        
        # Filter vendors by location (1km radius max)
        vendors_with_distance = get_vendors_within_radius(
            all_vendors, 
            current_user.latitude, 
            current_user.longitude,
            max_radius_km=max_distance
        )
        
        return render_template('buyer/vendors_list.html',
                             vendors=vendors_with_distance,
                             categories=categories,
                             category_id=category_id,
                             max_distance=max_distance,
                             search=search)
    
    @app.route('/buyer/home')
    @login_required
    def buyer_home():
        """Buyer home page with products and vendors"""
        # Check if user can be a buyer (all users can be buyers)
        if not current_user.can_be_buyer():
            flash('Access denied', 'error')
            return redirect(url_for('login'))
        
        # Set active role to buyer if not set
        if session.get('active_role') != 'buyer':
            session['active_role'] = 'buyer'
        
        # Get all categories
        categories = Category.query.all()
        
        # Search query
        search = request.args.get('search', '').strip()
        category_id = request.args.get('category', type=int)
        search_type = request.args.get('type', 'vendors')  # 'products' or 'vendors'
        distance_input = request.args.get('distance', type=float, default=1.0)
        # Allow only 0.2 (200m), 0.5 (500m), or 1.0 (1km) - default to 1.0
        max_distance = 1.0 if distance_input not in [0.2, 0.5, 1.0] else distance_input
        
        # Get all approved and online vendors
        all_vendors = Vendor.query.filter_by(status='APPROVED', is_online=True).all()
        
        # Filter vendors by location (1km radius max)
        vendors_with_distance = get_vendors_within_radius(
            all_vendors, 
            current_user.latitude, 
            current_user.longitude,
            max_radius_km=max_distance
        )
        
        products = []
        vendors = []
        
        if search:
            search_lower = search.lower()
            
            if search_type == 'products' or search_type == 'all':
                # Search products by name and description
                products_query = Product.query.filter_by(is_active=True)\
                    .join(Vendor).filter(Vendor.status == 'APPROVED', Vendor.is_online == True)
                
                if category_id:
                    products_query = products_query.filter(Product.category_id == category_id)
                
                all_products = products_query.all()
                
                # Filter products by search term
                for product in all_products:
                    if (search_lower in product.name.lower() or 
                        (product.description and search_lower in product.description.lower())):
                        products.append(product)
            
            if search_type == 'vendors' or search_type == 'all':
                # Search vendors by shop name and business type
                for vendor, distance in vendors_with_distance:
                    if (search_lower in vendor.shop_name.lower() or
                        (vendor.business_type and search_lower in vendor.business_type.lower()) or
                        (vendor.location and search_lower in vendor.location.lower())):
                        vendors.append((vendor, distance))
        else:
            # No search - show nearby vendors and optionally filter products by category
            vendors = vendors_with_distance
            
            if category_id:
                # Show products from selected category
                products_query = Product.query.filter_by(is_active=True, category_id=category_id)\
                    .join(Vendor).filter(Vendor.status == 'APPROVED', Vendor.is_online == True)
                products = products_query.all()
        
        return render_template('buyer/home.html', 
                             vendors=vendors,
                             products=products,
                             categories=categories,
                             search=search,
                             category_id=category_id,
                             search_type=search_type,
                             max_distance=max_distance,
                             user_lat=current_user.latitude,
                             user_lon=current_user.longitude,
                             has_location=bool(current_user.latitude and current_user.longitude))
    
    # About Us page
    @app.route('/about')
    def about():
        """About Us page"""
        return render_template('about.html')
    
    # Help page
    @app.route('/help')
    def help():
        """Help & Support page"""
        return render_template('help.html')
    
    # How It Works page
    @app.route('/how-it-works')
    def how_it_works():
        """How It Works page"""
        return render_template('how_it_works.html')
    
    # Terms of Service page
    @app.route('/terms')
    def terms():
        """Terms of Service page"""
        return render_template('terms.html')
    
    # Privacy Policy page
    @app.route('/privacy')
    def privacy():
        """Privacy Policy page"""
        return render_template('privacy.html')
    
    # Note: Additional buyer, vendor, admin, and API routes need to be added here
    # Due to the large number of routes (71 total), they will be added in subsequent operations
    # For now, the critical auth routes and basic buyer routes are in place
    
    # Create database tables
    with app.app_context():
        db.create_all()

        # Optional: bootstrap (or reset) an admin user via env vars.
        # This avoids hardcoding credentials in source control.
        bootstrap_email = os.environ.get('VENDORA_BOOTSTRAP_ADMIN_EMAIL')
        bootstrap_password = os.environ.get('VENDORA_BOOTSTRAP_ADMIN_PASSWORD')
        bootstrap_name = os.environ.get('VENDORA_BOOTSTRAP_ADMIN_NAME', 'Admin')
        bootstrap_reset = os.environ.get('VENDORA_BOOTSTRAP_ADMIN_RESET', '').lower() in ('1', 'true', 'yes')

        if bootstrap_email and bootstrap_password:
            admin = User.query.filter_by(email=bootstrap_email).first()
            if admin is None:
                admin = User(name=bootstrap_name, email=bootstrap_email, role='ADMIN')
                db.session.add(admin)
            elif bootstrap_reset:
                admin.role = 'ADMIN'
                if bootstrap_name and not admin.name:
                    admin.name = bootstrap_name
            else:
                admin = None  # Do not modify existing admin unless reset flag is set

            if admin is not None:
                admin.set_password(bootstrap_password)
                db.session.commit()
                try:
                    app.logger.warning("Bootstrapped admin user for %s (password not logged)", bootstrap_email)
                except Exception:
                    pass
    
    return app

if __name__ == '__main__':
    app = create_app('development')
    port = int(os.environ.get('PORT', 5000))
    print(f'\n🚀 Vendora is running!')
    print(f'📍 Server: http://localhost:{port}')
    print('👤 Admin: set VENDORA_BOOTSTRAP_ADMIN_EMAIL and VENDORA_BOOTSTRAP_ADMIN_PASSWORD to create/reset an admin')
    print(f'💾 Database: MySQL (VENDORA)')
    print(f'🐛 Debug Mode: ON')
    print(f'🔄 Auto-reload: ENABLED\n')
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=True)

