"""
Django settings integration for Comma Central Auth
Add these settings to your Django project's settings.py
"""

# Comma Central Auth Configuration
COMMA_AUTH_ENABLED = True
COMMA_AUTH_URL = "https://auth.comma.cm"  # Production URL

# For development
# COMMA_AUTH_URL = "http://localhost:8000"

# Add to MIDDLEWARE (preferably after AuthenticationMiddleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'path.to.comma_auth.CommaAuthMiddleware',  # Add this line
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS settings for comma auth
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "https://comma.cm",
    "https://auth.comma.cm",
    "https://docs.comma.cm",
    "https://app.comma.cm",
    "https://storybook.comma.cm",
    "http://localhost:3000",
    "http://localhost:8000",
]

# Allow comma auth tokens in headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]