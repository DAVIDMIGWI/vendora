from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import db, User, Vendor
from . import auth_bp

@auth_bp.route('/register/buyer', methods=['GET', 'POST'])
def register_buyer():
    # If user is already logged in, redirect them to their dashboard
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        elif current_user.can_be_vendor() and session.get('active_role') == 'vendor':
            return redirect(url_for('vendor.dashboard'))
        else:
            return redirect(url_for('buyer.home'))
    
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

@auth_bp.route('/register/vendor', methods=['GET', 'POST'])
def register_vendor():
    # If user is already logged in and has vendor profile, redirect to vendor dashboard
    if current_user.is_authenticated:
        if current_user.vendor_profile:
            return redirect(url_for('vendor.dashboard'))
        elif current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
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

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect them to their dashboard
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        elif current_user.can_be_vendor() and session.get('active_role') == 'vendor':
            return redirect(url_for('vendor.dashboard'))
        else:
            return redirect(url_for('buyer.home'))
    
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
            return redirect(url_for('auth.select_role'))
        
        # Redirect based on role (single role users)
        if user.is_admin():
            return redirect(url_for('admin.dashboard'))
        elif user.is_vendor():
            return redirect(url_for('vendor.dashboard'))
        else:
            return redirect(url_for('buyer.home'))
    
    return render_template('auth/login.html')

@auth_bp.route('/select-role', methods=['GET', 'POST'])
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
                return redirect(url_for('auth.register_vendor'))
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
                    return redirect(url_for('auth.register_vendor'))
    
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

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  # Clear session including active_role
    flash('You have been logged out', 'info')
    return render_template('landing.html')

