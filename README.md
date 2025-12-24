# Vendora - Mobile-First E-Commerce Platform

A comprehensive e-commerce platform built with Flask, MySQL, and mobile-first design principles. Designed for future mobile app integration with a complete API layer.

## Features

- **Three User Roles**: Admin, Vendor, Buyer
- **Mobile-First Design**: Optimized for smartphones with TailwindCSS
- **API-Ready**: Complete REST API for future mobile app integration
- **Vendor Management**: Vendors can manage products, orders, and profile
- **Buyer Experience**: Browse vendors, add to cart, place orders
- **Admin Dashboard**: Manage vendors, orders, categories, and buyers

## Tech Stack

- **Backend**: Python Flask
- **Database**: MySQL with SQLAlchemy ORM
- **Authentication**: Flask-Login
- **Frontend**: HTML + Jinja2 Templates + TailwindCSS CDN
- **Theme**: Green (#22C55E) primary color

## Installation

1. **Clone the repository**

```bash
cd "Vendora"
```

2. **Create a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure Database**

Update `config.py` with your MySQL credentials:

```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://username:password@localhost/vendora'
```

Or set environment variable:

```bash
export DATABASE_URL='mysql+pymysql://username:password@localhost/vendora'
```

5. **Create MySQL Database**

```sql
CREATE DATABASE vendora;
```

6. **Run the application**

```bash
python app.py
```

The application will:

- Create all database tables automatically
- Create a default admin user: `admin@vendora.com` / `admin123` (CHANGE THIS IN PRODUCTION!)

## Default Admin Credentials

- **Email**: admin@vendora.com
- **Password**: admin123

⚠️ **IMPORTANT**: Change these credentials in production!

## Project Structure

```
vendora/
├── app.py                 # Main application file
├── config.py              # Configuration
├── requirements.txt       # Python dependencies
├── models/               # Database models
│   ├── user.py
│   ├── vendor.py
│   ├── category.py
│   ├── product.py
│   └── order.py
├── blueprints/           # Flask blueprints
│   ├── auth/            # Authentication
│   ├── buyer/           # Buyer routes
│   ├── vendor/          # Vendor routes
│   ├── admin/           # Admin routes
│   └── api/             # API endpoints (for mobile app)
├── templates/           # Jinja2 templates
│   ├── base.html
│   ├── auth/
│   ├── buyer/
│   ├── vendor/
│   └── admin/
└── static/              # Static files (CSS, JS, images)
```

## API Endpoints

All API endpoints are prefixed with `/api`:

### Authentication

- `POST /api/auth/login` - Login
- `POST /api/auth/register/buyer` - Register as buyer
- `POST /api/auth/register/vendor` - Register as vendor
- `GET /api/auth/me` - Get current user

### Vendors & Products

- `GET /api/vendors` - List all approved vendors
- `GET /api/vendors/<id>` - Get vendor details
- `GET /api/vendors/<id>/products` - Get vendor products
- `GET /api/categories` - List all categories

### Cart & Orders

- `GET /api/cart` - Get cart items
- `POST /api/cart/add` - Add to cart
- `POST /api/cart/update` - Update cart item
- `POST /api/cart/remove` - Remove from cart
- `GET /api/orders` - Get user orders
- `POST /api/orders` - Create order

### Vendor API

- `GET /api/vendor/orders` - Get vendor orders
- `POST /api/vendor/orders/<id>/status` - Update order status

### Admin API

- `GET /api/admin/vendors` - List all vendors
- `POST /api/admin/vendors/<id>/approve` - Approve vendor
- `POST /api/admin/vendors/<id>/block` - Block vendor
- `GET /api/admin/orders` - List all orders
- `GET /api/admin/categories` - List categories
- `POST /api/admin/categories` - Create category

## User Roles

### Admin

- Manage vendors (approve/block)
- View all orders
- Manage categories
- View all buyers

### Vendor

- Manage products (CRUD)
- View and update order status
- Update profile and shop information
- Toggle online/offline status

### Buyer

- Browse vendors and products
- Add products to cart
- Place orders
- View order history

## Mobile-First Design

- Single-column layout on mobile
- Large tap targets for easy interaction
- Bottom navigation bars for easy access
- Card-based layouts instead of tables
- Responsive design with TailwindCSS

## Future Mobile App Integration

The platform is designed with API-first architecture. All major actions have both:

1. Web HTML routes (Jinja templates)
2. JSON API endpoints

This allows easy integration with:

- Flutter mobile apps
- React Native apps
- Native iOS/Android apps
- Third-party integrations

## Development

To run in development mode:

```bash
export FLASK_ENV=development
python app.py
```

## Production Deployment

1. Set `FLASK_ENV=production` or use `ProductionConfig`
2. Change `SECRET_KEY` in config
3. Update database credentials
4. Change default admin password
5. Use a production WSGI server (e.g., Gunicorn)

## License

This project is built for Vendora e-commerce platform.
# vendora
