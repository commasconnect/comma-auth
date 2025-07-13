"""
Microsoft OAuth provider (future implementation)
"""

import httpx
from typing import Dict, Optional
from ..config import settings
from ..models import UserInfo

class MicrosoftAuthProvider:
    def __init__(self):
        self.client_id = settings.MICROSOFT_CLIENT_ID
        self.client_secret = settings.MICROSOFT_CLIENT_SECRET
        self.tenant = "common"  # Allow work/school and personal accounts
        
    def get_authorization_url(self, state: str) -> str:
        """Generate Microsoft OAuth authorization URL"""
        base_url = f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/authorize"
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': settings.GOOGLE_REDIRECT_URI.replace('google', 'microsoft'),
            'scope': 'openid email profile User.Read',
            'state': state,
            'response_mode': 'query'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    async def exchange_code_for_token(self, code: str, state: str) -> Dict:
        """Exchange authorization code for access token"""
        token_url = f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/token"
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': settings.GOOGLE_REDIRECT_URI.replace('google', 'microsoft'),
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Token exchange failed: {response.text}")
    
    async def get_user_info(self, access_token: str) -> Optional[UserInfo]:
        """Get user information from Microsoft Graph API"""
        try:
            async with httpx.AsyncClient() as client:
                # Get user profile from Microsoft Graph
                response = await client.get(
                    "https://graph.microsoft.com/v1.0/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code != 200:
                    return None
                    
                user_data = response.json()
                
                email = user_data.get('mail') or user_data.get('userPrincipalName', '')
                domain = email.split('@')[1] if '@' in email else ''
                
                # Validate domain is in allowed list
                if domain not in settings.ALLOWED_DOMAINS:
                    return None
                    
                return UserInfo(
                    email=email,
                    name=user_data.get('displayName', ''),
                    picture=None,  # Could get from Graph API if needed
                    domain=domain,
                    provider="microsoft"
                )
                
        except Exception:
            return None