# Comma Auth Integration Guide

## Quick Setup for CMYK Projects

### Django Integration

1. **Copy the middleware**:
   ```bash
   cp integrations/django_middleware.py your_project/apps/core/middleware/comma_auth.py
   ```

2. **Update settings.py**:
   ```python
   # Add to MIDDLEWARE
   MIDDLEWARE = [
       'django.contrib.auth.middleware.AuthenticationMiddleware',
       'apps.core.middleware.comma_auth.CommaAuthMiddleware',  # Add this
       # ... other middleware
   ]
   
   # Comma Auth Configuration
   COMMA_AUTH_ENABLED = True
   COMMA_AUTH_URL = "https://auth.comma.cm"  # Production
   # COMMA_AUTH_URL = "http://localhost:8000"  # Development
   
   # CORS for auth
   CORS_ALLOWED_ORIGINS = [
       "https://auth.comma.cm",
       "https://comma.cm",
       # ... other origins
   ]
   ```

3. **Use in views**:
   ```python
   from apps.core.middleware.comma_auth import CommaAuthRequiredMixin, Comma2FARequiredMixin
   
   class ProtectedView(CommaAuthRequiredMixin, View):
       def get(self, request):
           # Access user info
           user_info = request.comma_auth_info
           return JsonResponse(user_info)
   
   class SensitiveView(Comma2FARequiredMixin, View):
       def get(self, request):
           # Requires 2FA completion
           return JsonResponse({"data": "sensitive"})
   ```

### Vue/Nuxt Integration

1. **Copy the composable**:
   ```bash
   cp integrations/vue_composable.ts your_project/src/composables/useCommaAuth.ts
   ```

2. **Use in components**:
   ```vue
   <template>
     <div>
       <div v-if="isAuthenticated">
         Welcome {{ userInfo?.name }}!
       </div>
       <div v-else-if="isPartiallyAuthenticated">
         <button @click="show2FA = true">Complete 2FA</button>
       </div>
       <div v-else>
         <button @click="initiateLogin()">Sign in with comma</button>
       </div>
     </div>
   </template>
   
   <script setup>
   import { useCommaAuth } from '@/composables/useCommaAuth'
   
   const { 
     isAuthenticated, 
     isPartiallyAuthenticated,
     userInfo, 
     initiateLogin,
     sendOTP,
     verifyOTP 
   } = useCommaAuth()
   </script>
   ```

## API Usage

### Authentication Flow

1. **Initiate login**: `GET /auth/google`
2. **Handle callback**: User redirected with token
3. **Verify token**: `POST /auth/verify` 
4. **Send OTP** (if needed): `POST /auth/otp/send`
5. **Verify OTP**: `POST /auth/otp/verify`

### Token Headers

All authenticated requests should include:
```
Authorization: Bearer <access_token>
```

## Environment Variables

Required for comma-auth service:

```bash
JWT_SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_VERIFY_SERVICE_SID=your-verify-service-sid
ALLOWED_DOMAINS=comma.cm,derozic.com
```

## Deployment

1. Deploy comma-auth service to meta instance
2. Configure DNS: `auth.comma.cm -> meta instance`
3. Update all CMYK apps to use production URL
4. Test cross-domain authentication

## Security Notes

- All tokens are JWT with expiration
- 2FA required for sensitive operations
- Domain validation restricts Google OAuth
- CORS properly configured for cross-domain auth