from flask import render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from models import db, User, Vendor, Category, Product, Order
from datetime import datetime, timedelta
from sqlalchemy import func
import os
import time
from . import admin_bp

def admin_required(f):
    """Decorator to ensure user is admin"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Access denied', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # Calculate date ranges for trends
    now = datetime.utcnow()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    last_month_end = this_month_start - timedelta(seconds=1)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Total Users
    total_users = User.query.count()
    users_this_month = User.query.filter(User.created_at >= this_month_start).count()
    users_last_month = User.query.filter(
        User.created_at >= last_month_start,
        User.created_at < this_month_start
    ).count()
    users_growth = ((users_this_month - users_last_month) / users_last_month * 100) if users_last_month > 0 else 0
    
    # Active Vendors (approved and online)
    active_vendors = Vendor.query.filter_by(status='APPROVED', is_online=True).count()
    vendors_today = Vendor.query.filter(
        Vendor.status == 'APPROVED',
        Vendor.created_at >= today_start
    ).count()
    
    # Total Vendors
    total_vendors = Vendor.query.count()
    approved_vendors = Vendor.query.filter_by(status='APPROVED').count()
    pending_vendors = Vendor.query.filter_by(status='PENDING').count()
    
    # Total Orders
    total_orders = Order.query.count()
    orders_this_month = Order.query.filter(Order.created_at >= this_month_start).count()
    orders_last_month = Order.query.filter(
        Order.created_at >= last_month_start,
        Order.created_at < this_month_start
    ).count()
    orders_growth = ((orders_this_month - orders_last_month) / orders_last_month * 100) if orders_last_month > 0 else 0
    
    # Format total orders (e.g., 45.2k)
    if total_orders >= 1000:
        total_orders_formatted = f"{total_orders / 1000:.1f}k"
    else:
        total_orders_formatted = str(total_orders)
    
    # System Health Metrics (simulated for now)
    # In production, these would come from actual monitoring
    start_time = time.time()
    db.session.execute(db.text('SELECT 1'))
    db_latency_ms = int((time.time() - start_time) * 1000)
    
    # Simulate API uptime (99.9%)
    api_uptime = 99.9
    
    # Calculate storage usage (from uploads folder size)
    storage_used = 42  # Default
    try:
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        if upload_folder and os.path.exists(upload_folder):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(upload_folder):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
            # Assume 1GB total storage, calculate percentage
            storage_used = min(100, int((total_size / (1024 * 1024 * 1024)) * 100))
    except Exception:
        pass  # Use default if calculation fails
    
    # Recent Vendor Applications (pending vendors)
    recent_vendor_applications = Vendor.query.filter_by(status='PENDING')\
        .order_by(Vendor.created_at.desc()).limit(10).all()
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         users_growth=users_growth,
                         active_vendors=active_vendors,
                         vendors_today=vendors_today,
                         total_vendors=total_vendors,
                         approved_vendors=approved_vendors,
                         pending_vendors=pending_vendors,
                         total_orders=total_orders,
                         total_orders_formatted=total_orders_formatted,
                         orders_growth=orders_growth,
                         pending_orders=Order.query.filter_by(status='PENDING').count(),
                         total_products=Product.query.count(),
                         recent_orders=recent_orders,
                         recent_vendor_applications=recent_vendor_applications,
                         db_latency_ms=db_latency_ms,
                         api_uptime=api_uptime,
                         storage_used=storage_used)

@admin_bp.route('/vendors')
@login_required
@admin_required
def vendors():
    """Manage vendors"""
    status_filter = request.args.get('status', '')
    vendors_query = Vendor.query
    
    if status_filter:
        vendors_query = vendors_query.filter_by(status=status_filter)
    
    vendors = vendors_query.order_by(Vendor.created_at.desc()).all()
    
    return render_template('admin/vendors.html', vendors=vendors, status_filter=status_filter)

@admin_bp.route('/vendors/<int:vendor_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_vendor(vendor_id):
    """Approve vendor"""
    vendor = Vendor.query.get_or_404(vendor_id)
    vendor.status = 'APPROVED'
    db.session.commit()
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Vendor approved',
            'vendor': vendor.to_dict()
        }), 200
    
    flash('Vendor approved', 'success')
    return redirect(url_for('admin.vendors'))

@admin_bp.route('/vendors/<int:vendor_id>/block', methods=['POST'])
@login_required
@admin_required
def block_vendor(vendor_id):
    """Block vendor"""
    vendor = Vendor.query.get_or_404(vendor_id)
    vendor.status = 'BLOCKED'
    db.session.commit()
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Vendor blocked',
            'vendor': vendor.to_dict()
        }), 200
    
    flash('Vendor blocked', 'success')
    return redirect(url_for('admin.vendors'))

@admin_bp.route('/buyers')
@login_required
@admin_required
def buyers():
    """View all buyers"""
    buyers = User.query.filter_by(role='BUYER').order_by(User.created_at.desc()).all()
    return render_template('admin/buyers.html', buyers=buyers)

@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    """View all orders"""
    status_filter = request.args.get('status', '')
    orders_query = Order.query
    
    if status_filter:
        orders_query = orders_query.filter_by(status=status_filter)
    
    orders = orders_query.order_by(Order.created_at.desc()).all()
    
    return render_template('admin/orders.html', orders=orders, status_filter=status_filter)

@admin_bp.route('/orders/<int:order_id>')
@login_required
@admin_required
def order_detail(order_id):
    """View order details"""
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    """Manage categories"""
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_category():
    """Create new category"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        name = data.get('name')
        slug = data.get('slug', '').lower().replace(' ', '-')
        
        if not name:
            error = 'Category name is required'
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 400
            flash(error, 'error')
            return render_template('admin/category_form.html')
        
        if not slug:
            slug = name.lower().replace(' ', '-')
        
        # Check if slug exists
        if Category.query.filter_by(slug=slug).first():
            error = 'Category with this slug already exists'
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 400
            flash(error, 'error')
            return render_template('admin/category_form.html')
        
        category = Category(name=name, slug=slug)
        db.session.add(category)
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Category created',
                'category': category.to_dict()
            }), 201
        
        flash('Category created', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/category_form.html')

@admin_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(category_id):
    """Edit category"""
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        name = data.get('name')
        slug = data.get('slug', '').lower().replace(' ', '-')
        
        if not name:
            error = 'Category name is required'
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 400
            flash(error, 'error')
            return render_template('admin/category_form.html', category=category)
        
        if not slug:
            slug = name.lower().replace(' ', '-')
        
        # Check if slug exists (excluding current category)
        existing = Category.query.filter_by(slug=slug).first()
        if existing and existing.id != category.id:
            error = 'Category with this slug already exists'
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 400
            flash(error, 'error')
            return render_template('admin/category_form.html', category=category)
        
        category.name = name
        category.slug = slug
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Category updated',
                'category': category.to_dict()
            }), 200
        
        flash('Category updated', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/category_form.html', category=category)

@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    """Delete category"""
    category = Category.query.get_or_404(category_id)
    
    # Check if category has products
    if category.products.count() > 0:
        error = 'Cannot delete category with products'
        if request.is_json:
            return jsonify({'success': False, 'error': error}), 400
        flash(error, 'error')
        return redirect(url_for('admin.categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Category deleted'}), 200
    
    flash('Category deleted', 'success')
    return redirect(url_for('admin.categories'))

