from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from backend.rag.rag_utils import get_rag_response
from backend.database import Database
from backend.auth import Auth, RegisterRequest, OTPVerifyRequest, ChatRequest

app = FastAPI()
db = Database()
auth = Auth(db)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/register")
def register(request: RegisterRequest):
    otp = auth.register_doctor(request)
    print(f"[DEBUG] OTP for {request.email}: {otp}")
    return {"message": "Doctor registered. OTP sent (printed in logs)."}

@app.post("/verify-otp")
def verify_otp(request: OTPVerifyRequest):
    auth.verify_otp(request)
    return {"message": "OTP verified. You are now verified."}

@app.post("/chat")
def chat(request: ChatRequest):
    access_info = auth.validate_chat_access(request.email)
    response = get_rag_response(request.query)
    
    db.update_query_count(
        request.email, 
        access_info["daily_count"] + 1, 
        access_info["total_count"] + 1, 
        datetime.utcnow().date().isoformat()
    )
    
    return {
        "response": response, 
        "remaining": access_info["limit"] - (access_info["daily_count"] + 1)
    }
