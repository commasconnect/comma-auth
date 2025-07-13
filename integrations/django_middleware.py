"""
Django middleware for Comma Central Auth integration
Copy this to each CMYK Django project
"""

import httpx
import json
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from typing import Optional

class CommaAuthMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        self.comma_auth_url = getattr(settings, 'COMMA_AUTH_URL', 'http://localhost:8000')
        self.comma_auth_enabled = getattr(settings, 'COMMA_AUTH_ENABLED', True)
        super().__init__(get_response)
    
    def process_request(self, request):
        if not self.comma_auth_enabled:
            return None
            
        # Skip auth for certain paths
        skip_paths = [
            '/admin/login/',
            '/auth/login/',
            '/health/',
            '/static/',
            '/media/',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Check for comma auth token
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
            
        token = auth_header.split(' ')[1]
        user_info = self._verify_token(token)
        
        if user_info:
            # Create or get Django user
            django_user = self._get_or_create_user(user_info)
            if django_user:
                request.user = django_user
                request.comma_auth_info = user_info
                
        return None
    
    def _verify_token(self, token: str) -> Optional[dict]:
        """Verify token with comma auth service"""
        try:
            headers = {'Authorization': f'Bearer {token}'}
            response = httpx.post(
                f'{self.comma_auth_url}/auth/verify',
                headers=headers,
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('valid'):
                    return data.get('user_info')
        except Exception:
            pass
        
        return None
    
    def _get_or_create_user(self, user_info: dict) -> Optional[User]:
        """Get or create Django user from comma auth info"""
        try:
            email = user_info.get('email')
            if not email:
                return None
                
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': user_info.get('name', '').split(' ')[0],
                    'last_name': ' '.join(user_info.get('name', '').split(' ')[1:]),
                    'is_active': True,
                }
            )
            
            # Update user info if needed
            if not created:
                name_parts = user_info.get('name', '').split(' ')
                user.first_name = name_parts[0] if name_parts else ''
                user.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                user.save()
            
            return user
            
        except Exception:
            return None


class CommaAuthRequiredMixin:
    """Mixin for views that require comma auth"""
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request, 'comma_auth_info'):
            return JsonResponse({
                'error': 'Authentication required',
                'auth_url': f"{settings.COMMA_AUTH_URL}/auth/google"
            }, status=401)
        
        return super().dispatch(request, *args, **kwargs)


class Comma2FARequiredMixin:
    """Mixin for views that require 2FA"""
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request, 'comma_auth_info'):
            return JsonResponse({
                'error': 'Authentication required',
                'auth_url': f"{settings.COMMA_AUTH_URL}/auth/google"
            }, status=401)
        
        # Check if 2FA is required but not completed
        auth_info = getattr(request, 'comma_auth_info', {})
        if auth_info.get('requires_2fa', False):
            return JsonResponse({
                'error': '2FA required',
                'otp_url': f"{settings.COMMA_AUTH_URL}/auth/otp/send"
            }, status=403)
        
        return super().dispatch(request, *args, **kwargs)