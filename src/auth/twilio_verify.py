from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from typing import Optional, Dict
from ..config import settings

class TwilioVerifyProvider:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.verify_service_sid = settings.TWILIO_VERIFY_SERVICE_SID
        
    async def send_verification_code(self, phone_number: str) -> Dict[str, str]:
        """Send OTP verification code via SMS"""
        try:
            verification = self.client.verify \
                .v2 \
                .services(self.verify_service_sid) \
                .verifications \
                .create(to=phone_number, channel='sms')
            
            return {
                "status": "sent",
                "sid": verification.sid,
                "to": verification.to,
                "channel": verification.channel
            }
        except TwilioException as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def verify_code(self, phone_number: str, code: str) -> Dict[str, str]:
        """Verify the OTP code"""
        try:
            verification_check = self.client.verify \
                .v2 \
                .services(self.verify_service_sid) \
                .verification_checks \
                .create(to=phone_number, code=code)
            
            return {
                "status": verification_check.status,  # "approved" or "pending"
                "sid": verification_check.sid,
                "valid": verification_check.status == "approved"
            }
        except TwilioException as e:
            return {
                "status": "error", 
                "message": str(e),
                "valid": False
            }
    
    async def get_verification_status(self, phone_number: str) -> Optional[Dict]:
        """Get current verification status for a phone number"""
        try:
            verifications = self.client.verify \
                .v2 \
                .services(self.verify_service_sid) \
                .verifications \
                .list(to=phone_number, limit=1)
            
            if verifications:
                verification = verifications[0]
                return {
                    "status": verification.status,
                    "to": verification.to,
                    "channel": verification.channel,
                    "date_created": verification.date_created
                }
            return None
        except TwilioException as e:
            return {
                "status": "error",
                "message": str(e)
            }