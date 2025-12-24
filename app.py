import os
from flask import Flask, redirect, url_for, render_template
from flask_login import LoginManager
from config import config
from models import db
from models.user import User

# Import blueprints
from blueprints.auth import auth_bp
from blueprints.buyer import buyer_bp
from blueprints.vendor import vendor_bp
from blueprints.admin import admin_bp
from blueprints.api import api_bp

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

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
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(buyer_bp)
    app.register_blueprint(vendor_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    
    # Context processor for cart count and config (available in all templates)
    @app.context_processor
    def inject_globals():
        """Make cart count and config available in all templates"""
        from flask_login import current_user
        cart_count = 0
        if current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated and current_user.is_buyer():
            from blueprints.buyer.routes import get_cart_count
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
    
    # Root route - Landing page
    @app.route('/')
    def landing():
        """Landing page for non-authenticated users"""
        from flask_login import current_user
        if current_user.is_authenticated:
            if current_user.is_admin():
                return redirect(url_for('admin.dashboard'))
            elif current_user.is_vendor():
                return redirect(url_for('vendor.dashboard'))
            else:
                return redirect(url_for('buyer.home'))
        return render_template('landing.html')
    
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
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create default admin user if it doesn't exist
        admin = User.query.filter_by(email='admin@vendora.com').first()
        if not admin:
            admin = User(
                name='Admin',
                email='admin@vendora.com',
                role='ADMIN'
            )
            admin.set_password('admin123')  # Change this in production!
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: admin@vendora.com / admin123")
    
    return app

if __name__ == '__main__':
    app = create_app('development')
    port = int(os.environ.get('PORT', 5001))
    print(f'\n🚀 Vendora is running!')
    print(f'📍 Server: http://localhost:{port}')
    print(f'👤 Admin: admin@vendora.com / admin123')
    print(f'💾 Database: MySQL (VENDORA)')
    print(f'🐛 Debug Mode: ON')
    print(f'🔄 Auto-reload: ENABLED\n')
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=True)

