from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import db, User, Vendor
from . import auth_bp

@auth_bp.route('/register/buyer', methods=['GET', 'POST'])
def register_buyer():
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
        
        return redirect(url_for('buyer.home'))
    
    return render_template('auth/register_buyer.html')

@auth_bp.route('/register/vendor', methods=['GET', 'POST'])
def register_vendor():
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
        
        if User.query.filter_by(email=email).first():
            error = 'Email already registered'
            if data:
                return jsonify({'success': False, 'error': error}), 400
            flash(error, 'error')
            return render_template('auth/register_vendor.html')
        
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
        return redirect(url_for('vendor.dashboard'))
    
    return render_template('auth/register_vendor.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
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
        
        # Redirect based on role
        if user.is_admin():
            return redirect(url_for('admin.dashboard'))
        elif user.is_vendor():
            return redirect(url_for('vendor.dashboard'))
        else:
            return redirect(url_for('buyer.home'))
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

