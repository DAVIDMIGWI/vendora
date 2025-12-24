"""Utility functions for handling file uploads"""
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_product_image(file, product_id=None):
    """
    Save uploaded product image and return the URL path
    
    Args:
        file: FileStorage object from request.files
        product_id: Optional product ID for naming (if editing)
    
    Returns:
        str: URL path to the saved image, or None if upload failed
    """
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        return None
    
    # Generate unique filename
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    
    # Create upload directory if it doesn't exist
    upload_folder = current_app.config['UPLOAD_FOLDER']
    products_folder = os.path.join(upload_folder, 'products')
    os.makedirs(products_folder, exist_ok=True)
    
    # Save file
    file_path = os.path.join(products_folder, unique_filename)
    file.save(file_path)
    
    # Return URL path (relative to static folder)
    return f"/static/uploads/products/{unique_filename}"

def delete_product_image(image_url):
    """Delete a product image file"""
    if not image_url or not image_url.startswith('/static/uploads/products/'):
        return False
    
    try:
        file_path = os.path.join(
            current_app.config.get('UPLOAD_FOLDER', 'static/uploads'),
            image_url.replace('/static/uploads/', '')
        )
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception:
        pass
    return False

