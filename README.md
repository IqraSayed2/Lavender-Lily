# LavenderLily - UAE E-commerce Platform

A modern, responsive e-commerce website built with Django for selling clothing products in the UAE market. Features a simulated payment system for testing and development.

## Features

- 🛒 **Product Catalog**: Browse and search products by categories
- 🛍️ **Shopping Cart**: Add/remove items, quantity management
- 💳 **Simulated Payment**: Fake payment processing for testing (always succeeds)
- 📧 **Email Notifications**: Order confirmations and updates
- 👨‍💼 **Admin Panel**: Complete order and product management
- 📱 **Mobile Responsive**: Optimized for all devices
- 🔒 **Secure**: HTTPS ready, secure payment processing

## Prerequisites

- Python 3.8 or higher
- MySQL or PostgreSQL database
- Git

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/lavenderlily.git
   cd lavenderlily
   ```

2. **Create virtual environment:**

   ```bash
   python -m venv env
   # On Windows:
   env\Scripts\activate
   # On macOS/Linux:
   source env/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup:**

   - Create a MySQL/PostgreSQL database
   - Update database settings in `lavenderlily/settings.py`:
     ```python
     DATABASES = {
         'default': {
             'ENGINE': 'django.db.backends.mysql',  # or postgresql
             'NAME': 'your_db_name',
             'USER': 'your_db_user',
             'PASSWORD': 'your_db_password',
             'HOST': 'localhost',
             'PORT': '3306',  # or 5432 for PostgreSQL
         }
     }
     ```

5. **Run migrations:**

   ```bash
   python manage.py migrate
   ```

6. **Create superuser (for admin access):**

   ```bash
   python manage.py createsuperuser
   ```

7. **Collect static files:**
   ```bash
   python manage.py collectstatic
   ```

## Configuration

### Email Configuration

For email notifications, configure SMTP in `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@gmail.com'
EMAIL_HOST_PASSWORD = 'your_app_password'
```

## Running the Application

1. **Start the development server:**

   ```bash
   python manage.py runserver
   ```

2. **Access the application:**
   - Website: http://127.0.0.1:8000
   - Admin panel: http://127.0.0.1:8000/admin

## Usage

### For Customers:

- Browse products on the homepage
- Add items to cart
- Proceed to checkout
- Complete payment (simulated - always succeeds)
- Receive order confirmation

### For Admins:

- Login to admin panel
- Manage products, categories, orders
- View payment statuses
- Send notifications

## Project Structure

```
lavenderlily/
├── cart/              # Shopping cart functionality
├── core/              # Core app (home, about, contact)
├── orders/            # Order management
├── store/             # Product catalog
├── lavenderlily/      # Project settings
├── templates/         # HTML templates
├── static/            # CSS, JS, images
├── media/             # User uploaded files
└── manage.py
```

## Deployment

For production deployment, follow these steps:

1. Set `DEBUG = False` in settings.py
2. Configure production database
3. Set up static file serving (nginx/Apache)
4. Use Gunicorn or uWSGI as WSGI server
5. Set up reverse proxy with nginx
6. Obtain SSL certificate
7. Configure environment variables for secrets
8. **Note**: Payment system is currently simulated for testing

See the [Production Setup Guide](production-setup.md) for detailed instructions.

## Testing

Run tests with:

```bash
python manage.py test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Acknowledgments

- Django framework
- Bootstrap for responsive design
