from flask import render_template, request, jsonify, session, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
from decimal import Decimal
from models import db, Vendor, Product, Category, Order, OrderItem
from utils import get_vendors_within_radius, calculate_distance
from . import buyer_bp
import logging

# Session key for cart
CART_SESSION_KEY = 'cart'

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

@buyer_bp.route('/vendors')
@login_required
def vendors_list():
    """Vendor listing page with category and distance filters"""
    if not current_user.can_be_buyer():
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
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

@buyer_bp.route('/home')
@login_required
def home():
    """Buyer home page with products and vendors"""
    # Check if user can be a buyer (all users can be buyers)
    if not current_user.can_be_buyer():
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
    # Set active role to buyer if not set
    from flask import session
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

@buyer_bp.route('/vendor/<int:vendor_id>')
@login_required
def vendor_view(vendor_id):
    """View vendor and their products"""
    if not current_user.can_be_buyer():
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
    vendor = Vendor.query.get_or_404(vendor_id)
    
    if vendor.status != 'APPROVED':
        flash('Vendor not available', 'error')
        return redirect(url_for('buyer.home'))
    
    # Calculate distance if both have coordinates
    distance = None
    if current_user.latitude and current_user.longitude and vendor.latitude and vendor.longitude:
        distance = calculate_distance(
            current_user.latitude, current_user.longitude,
            vendor.latitude, vendor.longitude
        )
    
    # Get active products
    products = Product.query.filter_by(vendor_id=vendor_id, is_active=True).all()
    
    # Filter by category if provided
    category_id = request.args.get('category', type=int)
    if category_id:
        products = [p for p in products if p.category_id == category_id]
    
    categories = Category.query.all()
    
    return render_template('buyer/vendor_view.html', 
                         vendor=vendor, 
                         products=products,
                         categories=categories,
                         category_id=category_id,
                         distance=distance)

@buyer_bp.route('/cart')
@login_required
def cart():
    """View cart"""
    if not current_user.can_be_buyer():
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
    cart = get_cart()
    cart_items = []
    total = Decimal('0.00')
    
    for vendor_id, items in cart.items():
        vendor = Vendor.query.get(vendor_id)
        if not vendor or vendor.status != 'APPROVED':
            continue
        
        vendor_total = Decimal('0.00')
        vendor_items = []
        
        for item in items:
            product = Product.query.get(item['product_id'])
            if not product or not product.is_active:
                continue
            
            quantity = int(item['quantity'])
            item_total = Decimal(str(product.price)) * quantity
            vendor_total += item_total
            
            vendor_items.append({
                'product': product,
                'quantity': quantity,
                'total': item_total
            })
        
        if vendor_items:
            cart_items.append({
                'vendor': vendor,
                'cart_items': vendor_items,  # Changed from 'items' to avoid conflict
                'subtotal': vendor_total
            })
            total += vendor_total
    
    # Calculate total cart count
    cart_count = sum(len(cart_item['cart_items']) for cart_item in cart_items)
    
    return render_template('buyer/cart.html', cart_items=cart_items, total=total, cart_count=cart_count)

@buyer_bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    """Add product to cart"""
    if not current_user.can_be_buyer():
        if request.is_json:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
    data = request.get_json() if request.is_json else request.form
    product_id = int(data.get('product_id'))
    quantity = int(data.get('quantity', 1))
    
    product = Product.query.get_or_404(product_id)
    
    if not product.is_active:
        error = 'Product is not available'
        if request.is_json:
            return jsonify({'success': False, 'error': error}), 400
        flash(error, 'error')
        return redirect(url_for('buyer.vendor_view', vendor_id=product.vendor_id))
    
    if product.vendor.status != 'APPROVED':
        error = 'Vendor is not available'
        if request.is_json:
            return jsonify({'success': False, 'error': error}), 400
        flash(error, 'error')
        return redirect(url_for('buyer.vendor_view', vendor_id=product.vendor_id))
    
    cart = get_cart()
    vendor_id = str(product.vendor_id)
    
    if vendor_id not in cart:
        cart[vendor_id] = []
    
    # Check if product already in cart
    existing_item = next((item for item in cart[vendor_id] if item['product_id'] == product_id), None)
    
    if existing_item:
        existing_item['quantity'] += quantity
    else:
        cart[vendor_id].append({
            'product_id': product_id,
            'quantity': quantity
        })
    
    save_cart(cart)
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Product added to cart',
            'cart_count': sum(len(items) for items in cart.values())
        }), 200
    
    flash('Product added to cart', 'success')
    return redirect(url_for('buyer.vendor_view', vendor_id=product.vendor_id))

@buyer_bp.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    """Update cart item quantity"""
    if not current_user.can_be_buyer():
        if request.is_json:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
    data = request.get_json() if request.is_json else request.form
    vendor_id = str(data.get('vendor_id'))
    product_id = int(data.get('product_id'))
    quantity = int(data.get('quantity', 1))
    
    cart = get_cart()
    
    if vendor_id not in cart:
        error = 'Item not found in cart'
        if request.is_json:
            return jsonify({'success': False, 'error': error}), 404
        flash(error, 'error')
        return redirect(url_for('buyer.cart'))
    
    item = next((item for item in cart[vendor_id] if item['product_id'] == product_id), None)
    
    if not item:
        error = 'Item not found in cart'
        if request.is_json:
            return jsonify({'success': False, 'error': error}), 404
        flash(error, 'error')
        return redirect(url_for('buyer.cart'))
    
    if quantity <= 0:
        cart[vendor_id].remove(item)
        if not cart[vendor_id]:
            del cart[vendor_id]
    else:
        item['quantity'] = quantity
    
    save_cart(cart)
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Cart updated'}), 200
    
    flash('Cart updated', 'success')
    return redirect(url_for('buyer.cart'))

@buyer_bp.route('/cart/remove', methods=['POST'])
@login_required
def remove_from_cart():
    """Remove item from cart"""
    if not current_user.can_be_buyer():
        if request.is_json:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
    data = request.get_json() if request.is_json else request.form
    vendor_id = str(data.get('vendor_id'))
    product_id = int(data.get('product_id'))
    
    cart = get_cart()
    
    if vendor_id in cart:
        cart[vendor_id] = [item for item in cart[vendor_id] if item['product_id'] != product_id]
        if not cart[vendor_id]:
            del cart[vendor_id]
    
    save_cart(cart)
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Item removed from cart'}), 200
    
    flash('Item removed from cart', 'success')
    return redirect(url_for('buyer.cart'))

@buyer_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout and place order"""
    if not current_user.can_be_buyer():
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
    cart = get_cart()
    
    if not cart:
        flash('Your cart is empty', 'error')
        return redirect(url_for('buyer.cart'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        use_primary = data.get('use_primary_address') == '1'
        delivery_address = data.get('delivery_address', '').strip()
        delivery_instructions = data.get('delivery_instructions', '')
        delivery_latitude = data.get('delivery_latitude')
        delivery_longitude = data.get('delivery_longitude')
        
        # Validate delivery location coordinates
        if delivery_latitude and delivery_longitude:
            try:
                delivery_lat = Decimal(str(delivery_latitude))
                delivery_lon = Decimal(str(delivery_longitude))
            except (ValueError, TypeError):
                delivery_lat = None
                delivery_lon = None
        else:
            delivery_lat = None
            delivery_lon = None
        
        # Validate distance from all vendors in cart
        if delivery_lat and delivery_lon:
            invalid_vendors = []
            for vendor_id, items in cart.items():
                vendor = Vendor.query.get(int(vendor_id))
                if not vendor or vendor.status != 'APPROVED':
                    continue
                if vendor.latitude and vendor.longitude:
                    distance = calculate_distance(
                        float(delivery_lat), float(delivery_lon),
                        float(vendor.latitude), float(vendor.longitude)
                    )
                    if distance > 1.0:  # More than 1 km
                        invalid_vendors.append({
                            'name': vendor.shop_name,
                            'distance': round(distance, 2)
                        })
            
            if invalid_vendors:
                vendor_list = ', '.join([v['name'] + f' ({v["distance"]} km)' for v in invalid_vendors])
                error = f"Delivery location is too far from: {vendor_list}. Please select a location within 1 km from all vendors."
                if request.is_json:
                    return jsonify({'success': False, 'error': error}), 400
                flash(error, 'error')
                # Rebuild cart_items for error display
                cart_items = []
                total = Decimal('0.00')
                for vendor_id, items in cart.items():
                    vendor = Vendor.query.get(int(vendor_id))
                    if not vendor or vendor.status != 'APPROVED':
                        continue
                    vendor_total = Decimal('0.00')
                    vendor_items = []
                    for item in items:
                        product = Product.query.get(item['product_id'])
                        if not product or not product.is_active:
                            continue
                        quantity = int(item['quantity'])
                        item_total = Decimal(str(product.price)) * quantity
                        vendor_total += item_total
                        vendor_items.append({
                            'product': product,
                            'quantity': quantity,
                            'total': item_total
                        })
                    if vendor_items:
                        cart_items.append({
                            'vendor': vendor,
                            'cart_items': vendor_items,
                            'subtotal': vendor_total
                        })
                        total += vendor_total
                return render_template('buyer/checkout.html', 
                                     cart_items=cart_items, 
                                     total=total,
                                     primary_address=current_user.primary_address or '')
        else:
            # No coordinates provided - warn but allow (for backward compatibility)
            if not delivery_lat or not delivery_lon:
                flash('Please select a delivery location on the map to ensure it\'s within delivery range.', 'warning')
        
        # Use primary address if selected, otherwise use provided address
        if use_primary and current_user.primary_address:
            delivery_address = current_user.primary_address
        elif not delivery_address:
            error = 'Delivery address is required'
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 400
            flash(error, 'error')
            # Rebuild cart_items for error display
            cart_items = []
            total = Decimal('0.00')
            for vendor_id, items in cart.items():
                vendor = Vendor.query.get(int(vendor_id))
                if not vendor or vendor.status != 'APPROVED':
                    continue
                vendor_total = Decimal('0.00')
                vendor_items = []
                for item in items:
                    product = Product.query.get(item['product_id'])
                    if not product or not product.is_active:
                        continue
                    quantity = int(item['quantity'])
                    item_total = Decimal(str(product.price)) * quantity
                    vendor_total += item_total
                    vendor_items.append({
                        'product': product,
                        'quantity': quantity,
                        'total': item_total
                    })
                if vendor_items:
                    cart_items.append({
                        'vendor': vendor,
                        'cart_items': vendor_items,
                        'subtotal': vendor_total
                    })
                    total += vendor_total
            return render_template('buyer/checkout.html', 
                                 cart_items=cart_items, 
                                 total=total,
                                 primary_address=current_user.primary_address or '')
        
        # Create orders for each vendor
        orders_created = []
        
        for vendor_id, items in cart.items():
            vendor = Vendor.query.get(int(vendor_id))
            if not vendor or vendor.status != 'APPROVED':
                continue
            
            order = Order(
                buyer_id=current_user.id,
                vendor_id=vendor.id,
                delivery_address=delivery_address,
                delivery_instructions=delivery_instructions,
                delivery_fee=None,  # Will be set by vendor when accepting order
                status='PENDING',
                payment_status='PENDING',  # Default payment status
                items_removed=False
            )
            
            subtotal = Decimal('0.00')
            
            for item in items:
                product = Product.query.get(item['product_id'])
                if not product or not product.is_active:
                    continue
                
                quantity = int(item['quantity'])
                unit_price = Decimal(str(product.price))
                item_total = unit_price * quantity
                subtotal += item_total
                
                order_item = OrderItem(
                    product_id=product.id,
                    product_name_snapshot=product.name,
                    unit_price_snapshot=unit_price,
                    quantity=quantity,
                    is_removed=False
                )
                order.items.append(order_item)
            
            order.subtotal = subtotal
            order.total = subtotal  # Total will be updated when vendor sets delivery fee
            db.session.add(order)
            orders_created.append(order)
        
        if not orders_created:
            error = 'No valid items in cart'
            if request.is_json:
                return jsonify({'success': False, 'error': error}), 400
            flash(error, 'error')
            return redirect(url_for('buyer.cart'))
        
        db.session.commit()
        
        # #region agent log
        import json
        with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({
                'location': 'blueprints/buyer/routes.py:checkout:after_commit',
                'message': 'Orders committed, about to send notifications',
                'data': {'orders_count': len(orders_created), 'order_ids': [o.id for o in orders_created]},
                'timestamp': __import__('time').time() * 1000
            }) + '\n')
        # #endregion
        
        # Send notifications to vendors using Africa's Talking
        for order in orders_created:
            try:
                # #region agent log
                import json as json_module
                with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
                    f.write(json_module.dumps({
                        'location': 'blueprints/buyer/routes.py:checkout:before_notification',
                        'message': 'About to notify vendor for order',
                        'data': {'order_id': order.id, 'vendor_id': order.vendor_id},
                        'timestamp': __import__('time').time() * 1000
                    }) + '\n')
                # #endregion
                
                # Import notification service
                try:
                    from notification_service import NotificationService
                    notification_service = NotificationService()
                    result = notification_service.notify_vendor(order.id)
                except ImportError as ie:
                    logging.error(f'Failed to import notification_service: {str(ie)}')
                    # #region agent log
                    with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
                        f.write(json_module.dumps({
                            'location': 'blueprints/buyer/routes.py:checkout:import_error',
                            'message': 'Failed to import notification_service',
                            'data': {'order_id': order.id, 'error': str(ie)},
                            'timestamp': __import__('time').time() * 1000
                        }) + '\n')
                    # #endregion
                    result = False
                
                # #region agent log
                with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
                    f.write(json_module.dumps({
                        'location': 'blueprints/buyer/routes.py:checkout:after_notification',
                        'message': 'Notification attempt completed',
                        'data': {'order_id': order.id, 'result': result},
                        'timestamp': __import__('time').time() * 1000
                    }) + '\n')
                # #endregion
            except Exception as e:
                # Don't fail the order if notification fails
                logging.error(f'Failed to send notification for order {order.id}: {str(e)}', exc_info=True)
                # #region agent log
                import json as json_module
                import traceback
                with open('/Users/davidmigwi/VSCODE/Vendora/.cursor/debug.log', 'a') as f:
                    f.write(json_module.dumps({
                        'location': 'blueprints/buyer/routes.py:checkout:notification_exception',
                        'message': 'Exception during notification send',
                        'data': {'order_id': order.id, 'error': str(e), 'traceback': traceback.format_exc()},
                        'timestamp': __import__('time').time() * 1000
                    }) + '\n')
                # #endregion
        
        clear_cart()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Order placed successfully',
                'orders': [order.to_dict() for order in orders_created]
            }), 201
        
        flash('Order placed successfully', 'success')
        return redirect(url_for('buyer.orders'))
    
    # GET request - show checkout form
    cart_items = []
    total = Decimal('0.00')
    
    for vendor_id, items in cart.items():
        vendor = Vendor.query.get(int(vendor_id))
        if not vendor or vendor.status != 'APPROVED':
            continue
        
        vendor_total = Decimal('0.00')
        vendor_items = []
        
        for item in items:
            product = Product.query.get(item['product_id'])
            if not product or not product.is_active:
                continue
            
            quantity = int(item['quantity'])
            item_total = Decimal(str(product.price)) * quantity
            vendor_total += item_total
            
            vendor_items.append({
                'product': product,
                'quantity': quantity,
                'total': item_total
            })
        
        if vendor_items:
            cart_items.append({
                'vendor': vendor,
                'cart_items': vendor_items,  # Changed from 'items' to avoid conflict
                'subtotal': vendor_total
            })
            total += vendor_total
    
    # Get primary address for pre-filling
    primary_address = current_user.primary_address or ''
    
    return render_template('buyer/checkout.html', 
                         cart_items=cart_items, 
                         total=total,
                         primary_address=primary_address)

@buyer_bp.route('/orders')
@login_required
def orders():
    """View buyer orders"""
    # Check if user can be a buyer (all users can be buyers)
    if not current_user.can_be_buyer():
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
    # Set active role to buyer if not set
    from flask import session
    if session.get('active_role') != 'buyer':
        session['active_role'] = 'buyer'
    
    # Filter by status if provided
    status_filter = request.args.get('status', '')
    orders_query = Order.query.filter_by(buyer_id=current_user.id)
    
    if status_filter:
        orders_query = orders_query.filter_by(status=status_filter)
    
    orders = orders_query.order_by(Order.created_at.desc()).all()
    
    return render_template('buyer/orders.html', orders=orders, status_filter=status_filter)

@buyer_bp.route('/api/orders/status', methods=['GET'])
@login_required
def get_orders_status():
    """API endpoint to get order statuses for real-time updates"""
    if not current_user.can_be_buyer():
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    # Get all orders for the buyer
    orders = Order.query.filter_by(buyer_id=current_user.id).all()
    
    # Return order statuses as JSON
    order_statuses = {}
    for order in orders:
        order_statuses[order.id] = {
            'status': order.status,
            'payment_status': order.payment_status,
            'updated_at': order.updated_at.isoformat() if order.updated_at else None,
            'total': str(order.total)
        }
    
    return jsonify({
        'success': True,
        'orders': order_statuses,
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@buyer_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """View order details"""
    if not current_user.can_be_buyer():
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
    order = Order.query.get_or_404(order_id)
    
    if order.buyer_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('buyer.orders'))
    
    return render_template('buyer/order_detail.html', order=order)

@buyer_bp.route('/orders/<int:order_id>/mark-paid', methods=['POST'])
@login_required
def mark_order_paid(order_id):
    """Buyer claims to have paid - notifies vendor"""
    if not current_user.can_be_buyer():
        if request.is_json:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
    order = Order.query.get_or_404(order_id)
    
    if order.buyer_id != current_user.id:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        flash('Access denied', 'error')
        return redirect(url_for('buyer.orders'))
    
    # Mark that buyer claims to have paid (don't change payment_status - vendor will confirm)
    order.buyer_payment_claimed_at = datetime.utcnow()
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Payment claim sent to vendor. Vendor will confirm payment status.',
            'order': order.to_dict()
        }), 200
    
    flash('Payment claim sent to vendor! The vendor will confirm the payment status.', 'success')
    return redirect(url_for('buyer.order_detail', order_id=order_id))

@buyer_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Buyer profile - manage primary address and location"""
    if not current_user.can_be_buyer():
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        current_user.name = data.get('name', current_user.name)
        current_user.phone = data.get('phone', current_user.phone)
        
        # Get primary address directly from textarea
        primary_address = data.get('primary_address', '').strip()
        if primary_address:
            current_user.primary_address = primary_address
            # Keep estate and street for backward compatibility, but use full address
            # Try to extract estate if format is "street, estate"
            parts = primary_address.split(',')
            if len(parts) >= 2:
                current_user.primary_street = parts[0].strip()
                current_user.primary_estate = parts[-1].strip()
            else:
                current_user.primary_street = primary_address
                current_user.primary_estate = ''
        else:
            current_user.primary_address = None
            current_user.primary_street = None
            current_user.primary_estate = None
        
        # Update location coordinates only if explicitly provided (not empty)
        # This ensures we don't accidentally clear existing coordinates
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        if latitude and longitude and latitude != '' and longitude != '':
            try:
                current_user.latitude = Decimal(str(latitude))
                current_user.longitude = Decimal(str(longitude))
            except (ValueError, TypeError):
                pass  # Invalid coordinates, skip
        # If coordinates are not provided, keep existing ones (don't clear)
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Profile updated',
                'user': {
                    'id': current_user.id,
                    'name': current_user.name,
                    'phone': current_user.phone,
                    'primary_address': current_user.primary_address,
                    'latitude': float(current_user.latitude) if current_user.latitude else None,
                    'longitude': float(current_user.longitude) if current_user.longitude else None
                }
            }), 200
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('buyer.profile'))
    
    return render_template('buyer/profile.html')

@buyer_bp.route('/update-location', methods=['POST'])
@login_required
def update_location():
    """Update user location coordinates"""
    if not current_user.can_be_buyer():
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if not latitude or not longitude:
        return jsonify({'success': False, 'error': 'Latitude and longitude are required'}), 400
    
    try:
        current_user.latitude = Decimal(str(latitude))
        current_user.longitude = Decimal(str(longitude))
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Location updated',
            'latitude': float(current_user.latitude),
            'longitude': float(current_user.longitude)
        }), 200
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'error': 'Invalid coordinates'}), 400

