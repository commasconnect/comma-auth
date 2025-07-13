from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import uuid
from typing import Dict
from .config import settings
from .models import TokenResponse, OTPRequest, OTPVerification, TokenValidation, AuthState
from .auth.google import GoogleAuthProvider
from .auth.twilio_verify import TwilioVerifyProvider  
from .auth.jwt_manager import JWTManager

app = FastAPI(
    title="Comma Central Auth Service",
    description="Centralized authentication for all CMYK properties",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize providers
google_auth = GoogleAuthProvider()
twilio_verify = TwilioVerifyProvider()
jwt_manager = JWTManager()
security = HTTPBearer()

# In-memory state storage (use Redis in production)
auth_states: Dict[str, AuthState] = {}

@app.get("/")
async def root():
    return {"message": "Comma Central Auth Service", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "comma-auth"}

# Google OAuth Flow
@app.get("/auth/google")
async def google_login(redirect_url: str = None):
    """Initiate Google OAuth flow"""
    state = str(uuid.uuid4())
    auth_states[state] = AuthState(
        provider="google",
        redirect_url=redirect_url,
        scopes=["read"]
    )
    
    authorization_url = google_auth.get_authorization_url(state)
    return {"authorization_url": authorization_url, "state": state}

@app.get("/auth/google/callback")
async def google_callback(code: str, state: str):
    """Handle Google OAuth callback"""
    if state not in auth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    auth_state = auth_states.pop(state)
    
    try:
        # Exchange code for token
        token_data = await google_auth.exchange_code_for_token(code, state)
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        # Get user info
        user_info = await google_auth.get_user_info(access_token)
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info or invalid domain")
        
        # Create JWT tokens
        jwt_access_token = jwt_manager.create_access_token(
            user_info, 
            scopes=auth_state.scopes,
            requires_2fa=True  # Require 2FA for sensitive operations
        )
        refresh_token = jwt_manager.create_refresh_token(user_info.email)
        
        response_data = TokenResponse(
            access_token=jwt_access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            requires_2fa=True
        )
        
        # Redirect to original URL if provided
        if auth_state.redirect_url:
            return RedirectResponse(
                url=f"{auth_state.redirect_url}?token={jwt_access_token}&requires_2fa=true"
            )
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

# 2FA/OTP Endpoints
@app.post("/auth/otp/send")
async def send_otp(
    otp_request: OTPRequest, 
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Send OTP verification code"""
    # Verify user has valid token
    token_validation = jwt_manager.verify_token(credentials.credentials)
    if not token_validation.valid:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await twilio_verify.send_verification_code(otp_request.phone_number)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return {"status": "sent", "message": "Verification code sent"}

@app.post("/auth/otp/verify")
async def verify_otp(
    otp_verification: OTPVerification,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verify OTP code and upgrade token"""
    # Verify user has valid token
    token_validation = jwt_manager.verify_token(credentials.credentials)
    if not token_validation.valid:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await twilio_verify.verify_code(
        otp_verification.phone_number, 
        otp_verification.code
    )
    
    if not result.get("valid"):
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    # Create enhanced token with 2FA completed
    enhanced_token = jwt_manager.create_2fa_token(
        token_validation.user_info,
        scopes=["read", "write", "admin"]  # Full permissions after 2FA
    )
    
    return TokenResponse(
        access_token=enhanced_token,
        refresh_token=jwt_manager.create_refresh_token(token_validation.user_info.email),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        requires_2fa=False
    )

# Token Management
@app.post("/auth/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    user_email = jwt_manager.verify_refresh_token(refresh_token)
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    # Note: In production, you'd fetch user info from database
    # For now, we'll need the user to re-authenticate
    raise HTTPException(
        status_code=401, 
        detail="Please re-authenticate to refresh token"
    )

@app.post("/auth/verify", response_model=TokenValidation)
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify token validity (for other services)"""
    return jwt_manager.verify_token(credentials.credentials)

@app.post("/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout user (invalidate token)"""
    # In production, you'd maintain a token blacklist
    return {"message": "Logged out successfully"}

# Future endpoints for Apple ID and Microsoft
@app.get("/auth/apple")
async def apple_login():
    """Apple Sign-In (coming soon)"""
    raise HTTPException(status_code=501, detail="Apple Sign-In coming soon")

@app.get("/auth/microsoft") 
async def microsoft_login():
    """Microsoft OAuth (coming soon)"""
    raise HTTPException(status_code=501, detail="Microsoft OAuth coming soon")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)