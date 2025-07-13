# Comma Central Auth Service

A centralized authentication service providing "Sign in with comma" across all CMYK properties.

## Features

- Google Workspace OAuth integration
- Twilio Verify OTP (2FA)
- JWT token management
- Multi-provider support (Apple ID, Microsoft - future)
- Cross-domain authentication

## Properties Supported

- comma.cm (main site)
- docs.comma.cm
- app.comma.cm  
- storybook.comma.cm
- Future: nonprofit expansions

## Architecture

FastAPI service with:
- OAuth provider abstraction
- JWT access/refresh tokens
- Scoped permissions per application
- Domain-based user validation

## Quick Start

```bash
uv run uvicorn src.main:app --reload
```

## Environment Variables

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET` 
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `JWT_SECRET_KEY`
- `ALLOWED_DOMAINS`