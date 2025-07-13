from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from ..config import settings
from ..models import UserInfo, TokenValidation

class JWTManager:
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    
    def create_access_token(self, user_info: UserInfo, scopes: list = None, requires_2fa: bool = False) -> str:
        """Create JWT access token"""
        if scopes is None:
            scopes = ["read"]
            
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": user_info.email,
            "name": user_info.name,
            "email": user_info.email,
            "domain": user_info.domain, 
            "provider": user_info.provider,
            "picture": user_info.picture,
            "scopes": scopes,
            "requires_2fa": requires_2fa,
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": "comma-auth",
            "aud": "comma-apps"
        }
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_email: str) -> str:
        """Create JWT refresh token"""
        expires_delta = timedelta(days=self.refresh_token_expire_days)
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": user_email,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": "comma-auth"
        }
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> TokenValidation:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                return TokenValidation(valid=False)
            
            # Extract user info
            user_info = UserInfo(
                email=payload.get("email"),
                name=payload.get("name"),
                picture=payload.get("picture"),
                domain=payload.get("domain"),
                provider=payload.get("provider")
            )
            
            return TokenValidation(
                valid=True,
                user_info=user_info,
                scopes=payload.get("scopes", []),
                expires_at=datetime.utcfromtimestamp(exp) if exp else None
            )
            
        except JWTError:
            return TokenValidation(valid=False)
    
    def verify_refresh_token(self, token: str) -> Optional[str]:
        """Verify refresh token and return user email"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if it's a refresh token
            if payload.get("type") != "refresh":
                return None
                
            # Check if token is expired
            exp = payload.get("exp")
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                return None
                
            return payload.get("sub")  # user email
            
        except JWTError:
            return None
    
    def create_2fa_token(self, user_info: UserInfo, scopes: list = None) -> str:
        """Create token with 2FA completed"""
        if scopes is None:
            scopes = ["read", "write"]  # Enhanced permissions after 2FA
            
        return self.create_access_token(user_info, scopes, requires_2fa=False)