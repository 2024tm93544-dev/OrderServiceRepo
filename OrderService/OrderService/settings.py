from pathlib import Path
import os
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Prometheus (local safe directory) ---
PROMETHEUS_MULTIPROC_DIR = os.getenv("PROMETHEUS_MULTIPROC_DIR", str(BASE_DIR / "prometheus_data"))
os.makedirs(PROMETHEUS_MULTIPROC_DIR, exist_ok=True)

# --- Security ---
SECRET_KEY = os.getenv('SECRET_KEY', 'a@w-vlr#hv&y68_n7f$a4$&+p&^cay-=pw0r^%xjs(w*0@_(5x)')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8001',
    'http://127.0.0.1:8001'
]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000'
]

# --- Installed Apps ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'drf_yasg',
    'django_prometheus',
    'django_extensions',

    # Local app
    'ordersapp',
]

# --- Middleware ---
MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'OrderService.urls'

# --- Templates ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "ordersapp" / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'OrderService.wsgi.application'


# --- Database: PostgreSQL ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'order_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'root'),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}


# --- Authentication ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Localization ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- Static Files ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "ordersapp" / "static"]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Service URLs (Mocked for Local Run) ---
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://127.0.0.1:8000/v1/users")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://127.0.0.1:8001/v1/orders")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://127.0.0.1:8002/v1/inventory")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://127.0.0.1:8003/v1/payments")
SHIPPING_SERVICE_URL = os.getenv("SHIPPING_SERVICE_URL", "http://127.0.0.1:8004/v1/shipping")

USE_MOCK_USER = os.getenv("USE_MOCK_USER", "True").lower() == "true"
USE_MOCK_INVENTORY = os.getenv("USE_MOCK_INVENTORY", "True").lower() == "true"
USE_MOCK_PAYMENT = os.getenv("USE_MOCK_PAYMENT", "True").lower() == "true"
USE_MOCK_SHIPPING = os.getenv("USE_MOCK_SHIPPING", "True").lower() == "true"
