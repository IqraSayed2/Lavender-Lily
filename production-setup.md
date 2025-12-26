# Complete Production Setup Guide for LavenderLily

This guide provides step-by-step instructions to deploy your LavenderLily UAE e-commerce site to production. Follow these steps carefully to ensure a secure, scalable setup.

## Prerequisites
- A VPS or cloud server (e.g., AWS EC2, DigitalOcean Droplet, Heroku)
- Domain name (e.g., lavenderlily.ae)
- SSL certificate (free from Let's Encrypt)
- Production database (MySQL/PostgreSQL)

## 1. Server Setup
### Install Required Software
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install MySQL (or PostgreSQL)
sudo apt install mysql-server -y
sudo mysql_secure_installation

# Install nginx
sudo apt install nginx -y

# Install certbot for SSL
sudo apt install certbot python3-certbot-nginx -y
```

### Configure Firewall
```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

## 2. Application Deployment
### Clone and Setup Project
```bash
# Clone repository
git clone https://github.com/yourusername/lavenderlily.git
cd lavenderlily

# Create virtual environment
python3 -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn
```

### Database Configuration
```bash
# Create database
sudo mysql -u root -p
CREATE DATABASE lavenderlily;
CREATE USER 'lavenderuser'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON lavenderlily.* TO 'lavenderuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Update `lavenderlily/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'lavenderlily',
        'USER': 'lavenderuser',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
SECRET_KEY = 'your-production-secret-key'
```

### Run Migrations and Collect Static Files
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## 3. Gunicorn Setup
### Create Gunicorn Service
Create `/etc/systemd/system/gunicorn.service`:
```ini
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/lavenderlily
ExecStart=/home/ubuntu/lavenderlily/env/bin/gunicorn --access-logfile - --workers 3 --bind unix:/home/ubuntu/lavenderlily/lavenderlily.sock lavenderlily.wsgi:application

[Install]
WantedBy=multi-user.target
```

### Start Gunicorn
```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

## 4. Nginx Configuration
### Configure Nginx
Create `/etc/nginx/sites-available/lavenderlily`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        alias /home/ubuntu/lavenderlily/static/;
    }
    location /media/ {
        alias /home/ubuntu/lavenderlily/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/lavenderlily/lavenderlily.sock;
    }
}
```

### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/lavenderlily /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## 5. SSL Certificate
### Get SSL with Certbot
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Configure SSL Settings
Update `lavenderlily/settings.py`:
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

## 6. Payment Gateway Configuration
### Razorpay Production Setup
1. Get production API keys from Razorpay Dashboard
2. Enable Apple Pay and Google Pay
3. Configure webhooks if needed
4. Set currency to AED

Update `settings.py`:
```python
RAZORPAY_KEY_ID = 'your_live_razorpay_key_id'
RAZORPAY_KEY_SECRET = 'your_live_razorpay_key_secret'
```

### Ziina Production Setup
1. Get production credentials from Ziina Dashboard
2. Configure webhook URL: https://yourdomain.com/orders/ziina-webhook/
3. Enable required payment methods

Update `settings.py`:
```python
ZIINA_MERCHANT_ID = 'your_ziina_merchant_id'
ZIINA_API_KEY = 'your_ziina_api_key'
ZIINA_API_SECRET = 'your_ziina_api_secret'
```

## 7. Email Configuration
Update `settings.py` for production email:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@gmail.com'
EMAIL_HOST_PASSWORD = 'your_app_password'
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'
```

## 8. Security Hardening
### Update Permissions
```bash
sudo chown -R ubuntu:www-data /home/ubuntu/lavenderlily
sudo chmod -R 755 /home/ubuntu/lavenderlily
sudo chmod -R 777 /home/ubuntu/lavenderlily/media
```

### Environment Variables
Use `python-decouple` for sensitive data:
```python
from decouple import config

SECRET_KEY = config('SECRET_KEY')
RAZORPAY_KEY_ID = config('RAZORPAY_KEY_ID')
# etc.
```

Create `.env` file (add to .gitignore):
```
SECRET_KEY=your-secret-key
RAZORPAY_KEY_ID=your-key-id
# etc.
```

## 9. Monitoring and Logging
### Set up Log Rotation
```bash
sudo nano /etc/logrotate.d/lavenderlily
```

Add:
```
/home/ubuntu/lavenderlily/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
}
```

### Error Monitoring
Consider adding Sentry for error tracking.

## 10. Backup Strategy
### Database Backup
```bash
# Create backup script
sudo nano /home/ubuntu/backup.sh
```

Add:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u lavenderuser -p'your_password' lavenderlily > /home/ubuntu/backups/lavenderlily_$DATE.sql
```

### Schedule Backups
```bash
sudo crontab -e
# Add: 0 2 * * * /home/ubuntu/backup.sh
```

## 11. Performance Optimization
### Static File Optimization
- Use CloudFront or similar CDN for static files
- Enable gzip compression in nginx

### Database Optimization
- Add database indexes as needed
- Consider read replicas for high traffic

### Caching
Add Redis for session and cache storage.

## 12. Testing and Launch
### Pre-Launch Checklist
- [ ] All payment methods tested with small amounts
- [ ] SSL certificate valid
- [ ] Domain DNS configured
- [ ] Admin panel accessible
- [ ] Email notifications working
- [ ] Mobile responsive design verified
- [ ] Error pages configured

### Soft Launch
1. Launch with limited inventory
2. Monitor payment success rates
3. Set up customer support
4. Monitor server logs

### Full Launch
1. Update DNS to production server
2. Announce launch on social media
3. Monitor analytics and performance

## Troubleshooting
### Common Issues
- **502 Bad Gateway**: Check Gunicorn service status
- **Static files not loading**: Verify nginx configuration and permissions
- **Database connection errors**: Check database credentials and firewall
- **SSL issues**: Ensure certificate is valid and nginx config is correct

### Logs to Check
```bash
sudo journalctl -u gunicorn
sudo tail -f /var/log/nginx/error.log
```

## Cost Estimation
- **Server**: $20-100/month (depending on traffic)
- **Domain**: $10-50/year
- **SSL**: Free (Let's Encrypt)
- **Database**: Included with server or $10-50/month
- **CDN**: $10-50/month (optional)

## Support
For deployment issues:
- Check Django documentation
- Nginx documentation
- Server provider support
- Payment gateway support (Razorpay/Ziina)

Remember to regularly update your server, dependencies, and monitor performance!