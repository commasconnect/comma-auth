import httpx
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from typing import Dict, Optional
from ..config import settings
from ..models import UserInfo

class GoogleAuthProvider:
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        
    def get_authorization_url(self, state: str) -> str:
        """Generate Google OAuth authorization URL"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uris": [self.redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=[
                'openid',
                'email', 
                'profile',
                'https://www.googleapis.com/auth/admin.directory.user.readonly'  # For workspace domain validation
            ]
        )
        flow.redirect_uri = self.redirect_uri
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            hd=','.join(settings.ALLOWED_DOMAINS)  # Restrict to allowed domains
        )
        
        return authorization_url
    
    async def exchange_code_for_token(self, code: str, state: str) -> Dict:
        """Exchange authorization code for access token"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uris": [self.redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=[
                'openid',
                'email',
                'profile', 
                'https://www.googleapis.com/auth/admin.directory.user.readonly'
            ]
        )
        flow.redirect_uri = self.redirect_uri
        
        flow.fetch_token(code=code)
        return flow.credentials._asdict()
    
    async def get_user_info(self, access_token: str) -> Optional[UserInfo]:
        """Get user information from Google"""
        async with httpx.AsyncClient() as client:
            # Get user info from Google API
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                return None
                
            user_data = response.json()
            
            # Extract domain from email
            email = user_data.get("email", "")
            domain = email.split("@")[1] if "@" in email else ""
            
            # Validate domain is in allowed list
            if domain not in settings.ALLOWED_DOMAINS:
                return None
                
            return UserInfo(
                email=email,
                name=user_data.get("name", ""),
                picture=user_data.get("picture"),
                domain=domain,
                provider="google"
            )
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify Google ID token"""
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token, Request(), self.client_id
            )
            
            # Verify domain restriction
            domain = idinfo.get("hd")
            if domain not in settings.ALLOWED_DOMAINS:
                return None
                
            return idinfo
        except ValueError:
            return None