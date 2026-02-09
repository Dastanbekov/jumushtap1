# JumushTap Backend

Enterprise-grade Django REST API for hourly shift marketplace.

## 🏗️ Architecture

- **Backend:** Django 5.0 + Django REST Framework
- **Database:** PostgreSQL
- **Cache & Queue:** Redis + Celery
- **Storage:** S3-compatible (AWS S3 / MinIO)
- **Authentication:** JWT with SMS OTP
- **Payments:** Stripe / Local PSP
- **Push Notifications:** Firebase Cloud Messaging

## 📁 Project Structure

```
backend/
├── apps/               # Django applications
│   ├── users/         # Authentication & profiles
│   ├── jobs/          # Shift management (coming soon)
│   ├── payments/      # Payment processing (coming soon)
│   ├── ratings/       # Rating system (coming soon)
│   └── notifications/ # Push notifications (coming soon)
├── core/              # Project core
│   ├── settings/      # Multi-environment settings
│   ├── middleware/    # Custom middleware
│   ├── utils/         # Utilities
│   └── permissions.py # Global permissions
├── requirements/      # Dependencies
└── logs/             # Application logs
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+

### 2. Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/development.txt

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb jumushtap_dev

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Run Development Server

```bash
# Start Redis (in separate terminal)
redis-server

# Start Celery worker (in separate terminal)
celery -A core worker -l info

# Run Django server
python manage.py runserver
```

## 📝 Environment Variables

See `.env.example` for all configuration options.

Key variables:
- `DJANGO_ENV`: `development` or `production`
- `DB_*`: PostgreSQL connection settings
- `REDIS_URL`: Redis connection
- `SECRET_KEY`: Django secret key (change in production!)

## 🔒 Security Features

✅ JWT authentication with token rotation  
✅ SMS OTP verification  
✅ Role-based access control (RBAC)  
✅ Object-level permissions  
✅ Rate limiting (Redis-based)  
✅ Audit logging  
✅ Correlation ID tracking  
✅ STRIDE threat mitigation  

## 📖 API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/api/schema/swagger-ui/
- ReDoc: http://localhost:8000/api/schema/redoc/

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=apps --cov-report=html

# Run specific test file
pytest apps/users/tests/test_models.py
```

## 🛠️ Development Tools

```bash
# Code formatting
black apps/

# Import sorting
isort apps/

# Linting
flake8 apps/

# Security scan
bandit -r apps/
```

## 📊 Monitoring

### Logs
Logs are written to `logs/django.log` and console.

### Health Check
```bash
curl http://localhost:8000/api/health/
```

## 🚢 Production Deployment

See `requirements/production.txt` for production dependencies.

```bash
# Install production requirements
pip install -r requirements/production.txt

# Set environment
export DJANGO_ENV=production

# Collect static files
python manage.py collectstatic --noinput

# Run with gunicorn
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

## 📋 Current Status (Phase 1: Infrastructure Complete)

✅ Multi-environment settings (dev/prod)  
✅ Middleware (rate limit, audit log, correlation ID)  
✅ Global permissions (RBAC)  
✅ Geolocation utilities  
✅ Custom exception handler  

🚧 Coming Next (Phase 2-7):
- SMS OTP authentication
- Job/Shift management
- Payment system (escrow)
- Rating system
- Push notifications
- Admin panel enhancements

## 📞 Support

For technical issues, check:
- Implementation Plan: `../brain/.../implementation_plan.md`
- Security Requirements: `../documentation/security_req.md`

## 📄 License

Proprietary - JumushTap Platform
