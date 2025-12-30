# Complete Production Setup Guide for LavenderLily

This guide provides step-by-step instructions to deploy your LavenderLily UAE e-commerce site to production using Google Cloud Run. This is the best, safest, and most professional way to make your site accessible to real customers.

## Prerequisites
- Google Cloud Platform account
- Domain name (e.g., lavenderlily.ae)
- Production database (Cloud SQL)

## Architecture Overview

```
Customer Browser
     ↓
https://lavenderlily.ae
     ↓
Google Cloud Run (Django)
     ↓
Cloud SQL (MySQL/PostgreSQL)
```

## What YOU actually need to do (clear steps)

### 1️⃣ Put Django in production mode

Update `lavenderlily/settings.py`:

```python
# Add to requirements.txt
gunicorn==21.2.0
python-decouple==3.8

# In settings.py
from decouple import config

DEBUG = False
ALLOWED_HOSTS = ['lavenderlily.ae', '.run.app']

# Use environment variables for secrets
SECRET_KEY = config('SECRET_KEY')

# Database (Cloud SQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # or postgresql
        'NAME': config('DB_NAME'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
    }
}
```

### 2️⃣ Dockerize the project

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "lavenderlily.wsgi:application"]
```

Create `.dockerignore`:
```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis
*.egg-info
dist
build
.env
.venv
venv/
ENV/
env/
.idea/
.vscode/
*.swp
*.swo
*~
.DS_Store
staticfiles/
media/
node_modules/
.gitignore
README.md
production-setup.md
```

### 3️⃣ Deploy to Google Cloud Run

1. Create Google Cloud project
2. Enable Cloud Run API
3. Enable Cloud SQL API (if using Cloud SQL)
4. Install Google Cloud CLI

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/lavenderlily
gcloud run deploy lavenderlily \
  --image gcr.io/YOUR_PROJECT_ID/lavenderlily \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars SECRET_KEY="your-secret-key",DEBUG="False",ALLOWED_HOSTS=".run.app" \
  --port 8080
```

Result: `https://lavenderlily-xyz.a.run.app`

### 4️⃣ Attach your custom domain

1. Buy domain (GoDaddy / Namecheap / Google Domains)
2. In Cloud Run console, go to your service
3. Add custom domain
4. Update DNS records as instructed
5. Google auto-adds SSL

Now: `https://lavenderlily.ae`

### 5️⃣ Connect database (Cloud SQL)

Create Cloud SQL instance:
```bash
gcloud sql instances create lavenderlily-db --tier db-f1-micro --region us-central1
gcloud sql databases create lavenderlily --instance lavenderlily-db
```

Update environment variables in Cloud Run with database credentials.

For MySQL:
```bash
gcloud run services update lavenderlily \
  --set-env-vars DB_HOST="/cloudsql/YOUR_PROJECT_ID:us-central1:lavenderlily-db",DB_NAME="lavenderlily",DB_USER="root",DB_PASSWORD="your-password"
```

### 6️⃣ Payment System

The application uses a **simulated payment system** for testing and development purposes. In production, you can:

- Keep the fake payment for demo purposes
- Integrate real payment gateways like Stripe, PayPal, or local UAE gateways (Ziina, Tap & Go)
- The payment flow simulates successful transactions

For real payments, add environment variables for your chosen gateway:
```
STRIPE_PUBLIC_KEY=your_stripe_publishable_key
STRIPE_SECRET_KEY=your_stripe_secret_key
# Or other payment provider keys
```

## What you do NOT need to worry about

❌ Nginx
❌ Gunicorn service files
❌ Certbot
❌ Server updates
❌ Firewall rules

Google handles all of that.

## Cost (honest numbers)

* Cloud Run: ₹0–₹500/month (small traffic)
* Cloud SQL: ₹500–₹1,000/month
* Domain: yearly cost
* SSL: free

## Security Settings

Add to `settings.py`:
```python
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## Pre-Launch Checklist

- [ ] Django in production mode (DEBUG=False)
- [ ] ALLOWED_HOSTS configured
- [ ] Secrets in environment variables
- [ ] Docker container built and tested
- [ ] Cloud Run deployment successful
- [ ] Custom domain attached with SSL
- [ ] Cloud SQL database connected
- [ ] Payment system configured (currently simulated)
- [ ] Static files collected
- [ ] Admin user created
- [ ] Test orders with simulated payments
- [ ] Email notifications working

## Testing and Launch

1. Deploy to Cloud Run with test environment variables
2. Test all functionality including simulated payments
3. Test order flow from cart to completion
4. Launch!

## Troubleshooting

### Common Issues
- **Container build fails**: Check Dockerfile and requirements.txt
- **Database connection fails**: Verify Cloud SQL connection and credentials
- **Static files not loading**: Ensure collectstatic ran in container
- **Payment simulation fails**: Check JavaScript console for errors

### Logs
```bash
gcloud logs read --filter "resource.type=cloud_run_revision AND resource.labels.service_name=lavenderlily"
```

## Support

- Google Cloud Run documentation
- Django deployment docs
- General payment gateway documentation (when implementing real payments)

Your site will be live for the world 🌍 and behave like a real online store!