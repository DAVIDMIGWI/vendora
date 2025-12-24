from flask import render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from datetime import datetime, date
from decimal import Decimal
import os
from models import db, Vendor, Product, Category, Order, OrderItem
from upload_utils import save_product_image, delete_product_image, allowed_file
from . import vendor_bp

def vendor_required(f):
    """Decorator to ensure user is a vendor with approved status"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_vendor():
            flash('Access denied', 'error')
            return redirect(url_for('auth.login'))
        if not current_user.vendor_profile or current_user.vendor_profile.status != 'APPROVED':
            flash('Your vendor account is not approved', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@vendor_bp.route('/dashboard')
@login_required
@vendor_required
def dashboard():
    """Vendor dashboard"""
    vendor = current_user.vendor_profile
    
    # Today's orders
    today = date.today()
    today_orders = Order.query.filter_by(vendor_id=vendor.id)\
        .filter(db.func.date(Order.created_at) == today)\
        .order_by(Order.created_at.desc()).all()
    
    # Pending orders (for prominent display)
    pending_orders_list = Order.query.filter_by(vendor_id=vendor.id, status='PENDING')\
        .order_by(Order.created_at.desc()).all()
    
    # Stats
    total_orders = Order.query.filter_by(vendor_id=vendor.id).count()
    pending_orders = Order.query.filter_by(vendor_id=vendor.id, status='PENDING').count()
    active_products = Product.query.filter_by(vendor_id=vendor.id, is_active=True).count()
    
    return render_template('vendor/dashboard.html',
                         vendor=vendor,
                         today_orders=today_orders,
                         pending_orders_list=pending_orders_list,
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         active_products=active_products)

@vendor_bp.route('/orders')
@login_required
@vendor_required
def orders():
    """View all orders"""
    vendor = current_user.vendor_profile
    
    status_filter = request.args.get('status', '')
    orders_query = Order.query.filter_by(vendor_id=vendor.id)
    
    if status_filter:
        orders_query = orders_query.filter_by(status=status_filter)
    
    orders = orders_query.order_by(Order.created_at.desc()).all()
    
    return render_template('vendor/orders.html', orders=orders, status_filter=status_filter)

@vendor_bp.route('/orders/<int:order_id>')
@login_required
@vendor_required
def order_detail(order_id):
    """View order details"""
    vendor = current_user.vendor_profile
    order = Order.query.get_or_404(order_id)
    
    if order.vendor_id != vendor.id:
        flash('Access denied', 'error')
        return redirect(url_for('vendor.orders'))
    
    return render_template('vendor/order_detail.html', order=order)

@vendor_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
@vendor_required
def update_order_status(order_id):
    """Update order status"""
    vendor = current_user.vendor_profile
    order = Order.query.get_or_404(order_id)
    
    if order.vendor_id != vendor.id:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        flash('Access denied', 'error')
        return redirect(url_for('vendor.orders'))
    
    data = request.get_json() if request.is_json else request.form
    new_status = data.get('status')
    
    valid_statuses = ['PENDING', 'ACCEPTED', 'ON_THE_WAY', 'DELIVERED', 'CANCELLED']
    if new_status not in valid_statuses:
        error = 'Invalid status'
        if request.is_json:
            return jsonify({'success': False, 'error': error}), 400
        flash(error, 'error')
        return redirect(url_for('vendor.order_detail', order_id=order_id))
    
    # Status transition validation
    if order.status == 'DELIVERED' and new_status != 'DELIVERED':
        error = 'Cannot change status of delivered order'
        if request.is_json:
            return jsonify({'success': False, 'error': error}), 400
        flash(error, 'error')
        return redirect(url_for('vendor.order_detail', order_id=order_id))
    
    if order.status == 'CANCELLED' and new_status != 'CANCELLED':
        error = 'Cannot change status of cancelled order'
        if request.is_json:
            return jsonify({'success': False, 'error': error}), 400
        flash(error, 'error')
        return redirect(url_for('vendor.order_detail', order_id=order_id))
    
    # If accepting order, set delivery fee (default to 0 if not provided)
    if new_status == 'ACCEPTED' and order.status == 'PENDING':
        delivery_fee = data.get('delivery_fee', '0')
        try:
            delivery_fee = Decimal(str(delivery_fee)) if delivery_fee else Decimal('0')
            if delivery_fee < 0:
                raise ValueError('Delivery fee cannot be negative')
            order.delivery_fee = delivery_fee
        except (ValueError, TypeError):
            error = 'Invalid delivery fee'
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 400
            flash(error, 'error')
            return redirect(url_for('vendor.order_detail', order_id=order_id))
    
    order.status = new_status
    order.updated_at = datetime.utcnow()
    
    # Recalculate total when accepting order or when delivery fee changes
    if new_status == 'ACCEPTED':
        order.calculate_total()
    
    db.session.commit()
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Order status updated',
            'order': order.to_dict()
        }), 200
    
    flash('Order status updated', 'success')
    return redirect(url_for('vendor.order_detail', order_id=order_id))

@vendor_bp.route('/api/orders/status', methods=['GET'])
@login_required
@vendor_required
def get_orders_status():
    """API endpoint to get order statuses for real-time updates"""
    vendor = current_user.vendor_profile
    if not vendor:
        return jsonify({'success': False, 'error': 'Vendor profile not found'}), 403
    
    # Get today's orders for dashboard, or all orders if requested
    today_only = request.args.get('today_only', 'false').lower() == 'true'
    
    if today_only:
        from datetime import date
        today = date.today()
        orders = Order.query.filter_by(vendor_id=vendor.id)\
            .filter(db.func.date(Order.created_at) == today)\
            .order_by(Order.created_at.desc()).all()
    else:
        orders = Order.query.filter_by(vendor_id=vendor.id)\
            .order_by(Order.created_at.desc()).all()
    
    # Return order statuses as JSON
    order_statuses = {}
    for order in orders:
        order_statuses[order.id] = {
            'status': order.status,
            'payment_status': order.payment_status,
            'updated_at': order.updated_at.isoformat() if order.updated_at else None,
            'total': str(order.total),
            'created_at': order.created_at.isoformat() if order.created_at else None
        }
    
    return jsonify({
        'success': True,
        'orders': order_statuses,
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@vendor_bp.route('/orders/<int:order_id>/items/<int:item_id>/remove', methods=['POST'])
@login_required
@vendor_required
def remove_order_item(order_id, item_id):
    """Remove item from order (mark as unavailable)"""
    vendor = current_user.vendor_profile
    order = Order.query.get_or_404(order_id)
    
    if order.vendor_id != vendor.id:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        flash('Access denied', 'error')
        return redirect(url_for('vendor.orders'))
    
    # Can only remove items from pending or accepted orders
    if order.status not in ['PENDING', 'ACCEPTED']:
        error = 'Cannot remove items from orders that are already in progress'
        if request.is_json:
            return jsonify({'success': False, 'error': error}), 400
        flash(error, 'error')
        return redirect(url_for('vendor.order_detail', order_id=order_id))
    
    order_item = OrderItem.query.filter_by(id=item_id, order_id=order_id).first_or_404()
    
    if order_item.is_removed:
        error = 'Item already removed'
        if request.is_json:
            return jsonify({'success': False, 'error': error}), 400
        flash(error, 'error')
        return redirect(url_for('vendor.order_detail', order_id=order_id))
    
    # Mark item as removed
    order_item.is_removed = True
    order_item.removed_at = datetime.utcnow()
    order.items_removed = True
    
    # Recalculate order totals
    order.calculate_total()
    order.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Item removed from order. Buyer has been notified.',
            'order': order.to_dict()
        }), 200
    
    flash('Item removed from order. Buyer has been notified.', 'success')
    return redirect(url_for('vendor.order_detail', order_id=order_id))

@vendor_bp.route('/orders/<int:order_id>/payment', methods=['POST'])
@login_required
@vendor_required
def update_payment_status(order_id):
    """Update payment status"""
    vendor = current_user.vendor_profile
    order = Order.query.get_or_404(order_id)
    
    if order.vendor_id != vendor.id:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        flash('Access denied', 'error')
        return redirect(url_for('vendor.orders'))
    
    data = request.get_json() if request.is_json else request.form
    payment_status = data.get('payment_status')
    
    valid_payment_statuses = ['PENDING', 'PAID', 'NOT_PAID']
    if payment_status not in valid_payment_statuses:
        error = 'Invalid payment status'
        if request.is_json:
            return jsonify({'success': False, 'error': error}), 400
        flash(error, 'error')
        return redirect(url_for('vendor.order_detail', order_id=order_id))
    
    order.payment_status = payment_status
    order.updated_at = datetime.utcnow()
    # If vendor confirms payment, keep the buyer claim timestamp. If vendor marks as not paid, clear it.
    if payment_status == 'NOT_PAID':
        order.buyer_payment_claimed_at = None  # Clear buyer's claim if vendor marks as not paid
    db.session.commit()
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Payment status updated',
            'order': order.to_dict()
        }), 200
    
    flash('Payment status updated', 'success')
    return redirect(url_for('vendor.order_detail', order_id=order_id))

@vendor_bp.route('/products')
@login_required
@vendor_required
def products():
    """View all products"""
    vendor = current_user.vendor_profile
    products = Product.query.filter_by(vendor_id=vendor.id)\
        .order_by(Product.created_at.desc()).all()
    
    return render_template('vendor/products.html', products=products)

@vendor_bp.route('/products/new', methods=['GET', 'POST'])
@login_required
@vendor_required
def new_product():
    """Create new product"""
    vendor = current_user.vendor_profile
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        name = data.get('name')
        description = data.get('description', '')
        category_id = data.get('category_id', type=int)
        price = data.get('price')
        unit = data.get('unit', 'piece')
        is_active = data.get('is_active', 'true') == 'true' if isinstance(data.get('is_active'), str) else data.get('is_active', True)
        
        # Handle image upload (required for new products)
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                if not allowed_file(file.filename):
                    error = 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP'
                    if request.is_json:
                        return jsonify({'success': False, 'error': error}), 400
                    flash(error, 'error')
                    return render_template('vendor/product_form.html', categories=Category.query.all())
                
                image_url = save_product_image(file)
                if not image_url:
                    error = 'Failed to upload image'
                    if request.is_json:
                        return jsonify({'success': False, 'error': error}), 400
                    flash(error, 'error')
                    return render_template('vendor/product_form.html', categories=Category.query.all())
        
        # Image is required for new products
        if not image_url:
            error = 'Product image is required. Please upload an image file.'
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 400
            flash(error, 'error')
            return render_template('vendor/product_form.html', categories=Category.query.all())
        
        if not all([name, price]):
            error = 'Name and price are required'
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 400
            flash(error, 'error')
            return render_template('vendor/product_form.html', categories=Category.query.all())
        
        try:
            price = Decimal(str(price))
        except:
            error = 'Invalid price'
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 400
            flash(error, 'error')
            return render_template('vendor/product_form.html', categories=Category.query.all())
        
        product = Product(
            vendor_id=vendor.id,
            category_id=category_id if category_id else None,
            name=name,
            description=description,
            image_url=image_url,
            price=price,
            unit=unit,
            is_active=is_active
        )
        
        db.session.add(product)
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Product created',
                'product': product.to_dict()
            }), 201
        
        flash('Product created', 'success')
        return redirect(url_for('vendor.products'))
    
    categories = Category.query.all()
    return render_template('vendor/product_form.html', categories=categories)

@vendor_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@vendor_required
def edit_product(product_id):
    """Edit product"""
    vendor = current_user.vendor_profile
    product = Product.query.get_or_404(product_id)
    
    if product.vendor_id != vendor.id:
        flash('Access denied', 'error')
        return redirect(url_for('vendor.products'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        name = data.get('name')
        description = data.get('description', '')
        category_id = data.get('category_id', type=int)
        price = data.get('price')
        unit = data.get('unit', 'piece')
        is_active = data.get('is_active', 'true') == 'true' if isinstance(data.get('is_active'), str) else data.get('is_active', True)
        
        # Handle image upload (optional for editing - keeps existing if no new file uploaded)
        image_url = product.image_url  # Keep existing image by default
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                if not allowed_file(file.filename):
                    error = 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP'
                    if request.is_json:
                        return jsonify({'success': False, 'error': error}), 400
                    flash(error, 'error')
                    return render_template('vendor/product_form.html', product=product, categories=Category.query.all())
                
                # Delete old image if it exists and was uploaded to our server
                if product.image_url and product.image_url.startswith('/static/uploads/products/'):
                    delete_product_image(product.image_url)
                
                image_url = save_product_image(file, product.id)
                if not image_url:
                    error = 'Failed to upload image'
                    if request.is_json:
                        return jsonify({'success': False, 'error': error}), 400
                    flash(error, 'error')
                    return render_template('vendor/product_form.html', product=product, categories=Category.query.all())
        
        if not all([name, price, image_url]):
            error = 'Name, price, and image are required'
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 400
            flash(error, 'error')
            return render_template('vendor/product_form.html', product=product, categories=Category.query.all())
        
        try:
            price = Decimal(str(price))
        except:
            error = 'Invalid price'
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 400
            flash(error, 'error')
            return render_template('vendor/product_form.html', product=product, categories=Category.query.all())
        
        product.name = name
        product.description = description
        product.image_url = image_url
        product.category_id = category_id if category_id else None
        product.price = price
        product.unit = unit
        product.is_active = is_active
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Product updated',
                'product': product.to_dict()
            }), 200
        
        flash('Product updated', 'success')
        return redirect(url_for('vendor.products'))
    
    categories = Category.query.all()
    return render_template('vendor/product_form.html', product=product, categories=categories)

@vendor_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
@vendor_required
def delete_product(product_id):
    """Delete product"""
    vendor = current_user.vendor_profile
    product = Product.query.get_or_404(product_id)
    
    if product.vendor_id != vendor.id:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        flash('Access denied', 'error')
        return redirect(url_for('vendor.products'))
    
    db.session.delete(product)
    db.session.commit()
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Product deleted'}), 200
    
    flash('Product deleted', 'success')
    return redirect(url_for('vendor.products'))

@vendor_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@vendor_required
def profile():
    """Vendor profile"""
    vendor = current_user.vendor_profile
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        vendor.shop_name = data.get('shop_name', vendor.shop_name)
        vendor.business_type = data.get('business_type', vendor.business_type)
        vendor.phone = data.get('phone', vendor.phone)
        vendor.location = data.get('location', vendor.location)
        # Detailed location fields
        vendor.street_address = data.get('street_address', vendor.street_address)
        vendor.building_name = data.get('building_name', vendor.building_name)
        vendor.landmark = data.get('landmark', vendor.landmark)
        vendor.area = data.get('area', vendor.area)
        vendor.city = data.get('city', vendor.city)
        vendor.delivery_note = data.get('delivery_note', vendor.delivery_note)
        vendor.payment_instructions = data.get('payment_instructions', vendor.payment_instructions)
        vendor.working_hours = data.get('working_hours', vendor.working_hours)
        is_online = data.get('is_online')
        if is_online is not None:
            vendor.is_online = is_online == 'true' if isinstance(is_online, str) else bool(is_online)
        
        # Update location coordinates only if explicitly provided (not empty)
        # This ensures we don't accidentally clear existing coordinates
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        if latitude and longitude and latitude != '' and longitude != '':
            try:
                from decimal import Decimal
                vendor.latitude = Decimal(str(latitude))
                vendor.longitude = Decimal(str(longitude))
            except (ValueError, TypeError):
                pass  # Invalid coordinates, skip
        # If coordinates are not provided, keep existing ones (don't clear)
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Profile updated',
                'vendor': vendor.to_dict()
            }), 200
        
        flash('Profile updated', 'success')
        return redirect(url_for('vendor.profile'))
    
    return render_template('vendor/profile.html', vendor=vendor)

