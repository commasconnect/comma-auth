from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserInfo(BaseModel):
    email: EmailStr
    name: str
    picture: Optional[str] = None
    domain: str
    provider: str  # "google", "apple", "microsoft"

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    requires_2fa: bool = False

class OTPRequest(BaseModel):
    phone_number: str
    
class OTPVerification(BaseModel):
    phone_number: str
    code: str

class TokenValidation(BaseModel):
    valid: bool
    user_info: Optional[UserInfo] = None
    scopes: List[str] = []
    expires_at: Optional[datetime] = None

class AuthState(BaseModel):
    provider: str
    redirect_url: Optional[str] = None
    scopes: List[str] = []