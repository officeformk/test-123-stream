from fastapi import HTTPException
from pydantic import BaseModel
from datetime import datetime

class RegisterRequest(BaseModel):
    name: str
    email: str
    mobile: str
    reg_number: str

class OTPVerifyRequest(BaseModel):
    email: str
    otp: str

class ChatRequest(BaseModel):
    email: str
    query: str

class Auth:
    def __init__(self, db):
        self.db = db

    def verify_doctor(self, email: str) -> bool:
        doctor = self.db.get_doctor(email)
        if not doctor:
            return False
        return doctor[4] == 1  # Check is_verified status

    def register_doctor(self, email: str, name: str, mobile: str, reg_number: str) -> str:
        return self.db.register_doctor(email, name, mobile, reg_number)

    def verify_otp(self, email: str, otp: str) -> bool:
        return self.db.verify_otp(email, otp)

    def check_query_limit(self, email: str) -> tuple:
        doctor = self.db.get_doctor(email)
        if not doctor:
            return False, 0, 0
        
        is_verified = doctor[4]
        last_date = doctor[7]
        daily_count = doctor[8]
        total_count = doctor[9]

        today = datetime.utcnow().date().isoformat()
        if last_date != today:
            daily_count = 0

        limit = 50 if is_verified else 5
        can_query = daily_count < limit

        return can_query, daily_count, limit

    def validate_chat_access(self, email: str):
        doctor = self.db.get_doctor(email)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        is_verified = doctor[4]
        last_date = doctor[6]
        daily_count = doctor[7]
        total_count = doctor[8]

        today = datetime.utcnow().date().isoformat()
        if last_date != today:
            daily_count = 0

        limit = 50 if is_verified else 5
        if daily_count >= limit:
            raise HTTPException(status_code=403, detail=f"Query limit reached ({limit} per day).")

        return {
            "daily_count": daily_count,
            "total_count": total_count,
            "limit": limit
        }