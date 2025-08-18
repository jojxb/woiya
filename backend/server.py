from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
import jwt
import bcrypt
import uuid
from enum import Enum
import asyncio

# Database connection
client = AsyncIOMotorClient(os.getenv("MONGO_URL", "mongodb://localhost:27017"))
db = client.woiya_marketplace

# Security
security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET", "woiya-secret-key-2024")

app = FastAPI(title="WOIYA Marketplace API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enums
class UserRole(str, Enum):
    PENCARI_JASA = "pencari_jasa"  # Service Seeker
    PENYEDIA_JASA = "penyedia_jasa"  # Service Provider

class JobCategory(str, Enum):
    COURIER = "courier_logistik"
    HOME_REPAIR = "perbaikan_rumah"
    DAILY_ASSISTANT = "asisten_harian"
    PET_CARE = "perawatan_hewan"
    EDUCATION = "edukasi_belajar"
    EVENTS = "acara_kreatif"

class JobStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentMethod(str, Enum):
    GOPAY = "gopay"
    OVO = "ovo"
    VIRTUAL_ACCOUNT = "virtual_account"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    HELD_IN_ESCROW = "held_in_escrow"
    RELEASED = "released"
    REFUNDED = "refunded"

# Pydantic Models
class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str
    phone: str
    role: UserRole
    location: Dict[str, float] = {"lat": -6.2088, "lng": 106.8456}  # Default Jakarta

class UserLogin(BaseModel):
    email: str
    password: str

class JobCreate(BaseModel):
    title: str
    description: str
    category: JobCategory
    budget_min: int
    budget_max: int
    location: Dict[str, float]
    address: str
    deadline: datetime
    requirements: List[str] = []

class BidCreate(BaseModel):
    job_id: str
    amount: int
    message: str
    completion_time: str  # e.g., "2 days"

class PaymentCreate(BaseModel):
    job_id: str
    bid_id: str
    payment_method: PaymentMethod
    amount: int

class MessageCreate(BaseModel):
    recipient_id: str
    content: str
    job_id: Optional[str] = None

class RatingCreate(BaseModel):
    target_user_id: str
    job_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str

# Helper Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Mock Payment Handlers
class MockPaymentHandler:
    @staticmethod
    async def create_payment(payment_method: PaymentMethod, amount: int, order_id: str) -> Dict[str, Any]:
        await asyncio.sleep(1)  # Simulate API call
        return {
            "success": True,
            "payment_id": f"pay_{uuid.uuid4().hex[:12]}",
            "gateway_url": f"https://mock-{payment_method.value}.com/pay/{order_id}",
            "status": "created",
            "method": payment_method.value,
            "amount": amount
        }
    
    @staticmethod
    async def check_payment_status(payment_id: str) -> Dict[str, Any]:
        await asyncio.sleep(0.5)
        return {
            "success": True,
            "status": "paid",
            "payment_id": payment_id
        }
    
    @staticmethod
    async def process_refund(payment_id: str, amount: int) -> Dict[str, Any]:
        await asyncio.sleep(1)
        return {
            "success": True,
            "refund_id": f"ref_{uuid.uuid4().hex[:12]}",
            "status": "refunded",
            "amount": amount
        }

# API Endpoints
@app.post("/api/auth/register")
async def register_user(user_data: UserRegister):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user_data.password)
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "password": hashed_password,
        "full_name": user_data.full_name,
        "phone": user_data.phone,
        "role": user_data.role,
        "location": user_data.location,
        "rating": 0.0,
        "total_ratings": 0,
        "wallet_balance": 0,
        "created_at": datetime.utcnow(),
        "is_verified": False
    }
    
    await db.users.insert_one(user_doc)
    
    # Create JWT token
    token = create_jwt_token(user_id, user_data.role)
    
    return {
        "message": "User registered successfully",
        "token": token,
        "user": {
            "id": user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "role": user_data.role
        }
    }

@app.post("/api/auth/login")
async def login_user(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email}, {"_id": 0})
    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(user["id"], user["role"])
    
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "wallet_balance": user.get("wallet_balance", 0)
        }
    }

@app.get("/api/user/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "phone": current_user["phone"],
        "role": current_user["role"],
        "location": current_user["location"],
        "rating": current_user.get("rating", 0.0),
        "total_ratings": current_user.get("total_ratings", 0),
        "wallet_balance": current_user.get("wallet_balance", 0),
        "created_at": current_user["created_at"]
    }

@app.post("/api/jobs")
async def create_job(job_data: JobCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != UserRole.PENCARI_JASA:
        raise HTTPException(status_code=403, detail="Only service seekers can create jobs")
    
    job_id = str(uuid.uuid4())
    job_doc = {
        "id": job_id,
        "title": job_data.title,
        "description": job_data.description,
        "category": job_data.category,
        "budget_min": job_data.budget_min,
        "budget_max": job_data.budget_max,
        "location": job_data.location,
        "address": job_data.address,
        "deadline": job_data.deadline,
        "requirements": job_data.requirements,
        "status": JobStatus.OPEN,
        "creator_id": current_user["id"],
        "creator_name": current_user["full_name"],
        "created_at": datetime.utcnow(),
        "bids_count": 0,
        "selected_bid_id": None
    }
    
    await db.jobs.insert_one(job_doc)
    
    # Return the job without MongoDB's _id field - explicitly exclude it
    job_response = {k: v for k, v in job_doc.items() if k != "_id"}
    
    return {"message": "Job created successfully", "job_id": job_id, "job": job_response}

@app.get("/api/jobs")
async def get_jobs(
    category: Optional[JobCategory] = None,
    status: Optional[JobStatus] = None,
    limit: int = 20,
    skip: int = 0,
    current_user: dict = Depends(get_current_user)
):
    filter_query = {}
    if category:
        filter_query["category"] = category
    if status:
        filter_query["status"] = status
    
    # Service providers see all open jobs, service seekers see their own jobs
    if current_user["role"] == UserRole.PENCARI_JASA:
        filter_query["creator_id"] = current_user["id"]
    else:
        filter_query["status"] = JobStatus.OPEN
    
    cursor = db.jobs.find(filter_query, {"_id": 0}).skip(skip).limit(limit).sort("created_at", -1)
    jobs = await cursor.to_list(length=None)
    
    # Add bid count for each job
    for job in jobs:
        job["bids_count"] = await db.bids.count_documents({"job_id": job["id"]})
    
    return {"jobs": jobs}

@app.get("/api/jobs/{job_id}")
async def get_job_details(job_id: str, current_user: dict = Depends(get_current_user)):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get bids for this job
    bids_cursor = db.bids.find({"job_id": job_id}, {"_id": 0}).sort("created_at", -1)
    bids = await bids_cursor.to_list(length=None)
    
    # Add bidder information
    for bid in bids:
        bidder = await db.users.find_one({"id": bid["bidder_id"]}, {"_id": 0})
        if bidder:
            bid["bidder_name"] = bidder["full_name"]
            bid["bidder_rating"] = bidder.get("rating", 0.0)
    
    job["bids"] = bids
    return {"job": job}

@app.post("/api/jobs/{job_id}/bids")
async def create_bid(job_id: str, bid_data: BidCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != UserRole.PENYEDIA_JASA:
        raise HTTPException(status_code=403, detail="Only service providers can place bids")
    
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != JobStatus.OPEN:
        raise HTTPException(status_code=400, detail="Job is not open for bidding")
    
    # Check if user already bid
    existing_bid = await db.bids.find_one({"job_id": job_id, "bidder_id": current_user["id"]}, {"_id": 0})
    if existing_bid:
        raise HTTPException(status_code=400, detail="You have already placed a bid on this job")
    
    bid_id = str(uuid.uuid4())
    bid_doc = {
        "id": bid_id,
        "job_id": job_id,
        "bidder_id": current_user["id"],
        "bidder_name": current_user["full_name"],
        "amount": bid_data.amount,
        "message": bid_data.message,
        "completion_time": bid_data.completion_time,
        "created_at": datetime.utcnow(),
        "is_selected": False
    }
    
    await db.bids.insert_one(bid_doc)
    
    # Update job bid count
    await db.jobs.update_one({"id": job_id}, {"$inc": {"bids_count": 1}})
    
    return {"message": "Bid placed successfully", "bid_id": bid_id}

@app.post("/api/jobs/{job_id}/select-bid/{bid_id}")
async def select_bid(job_id: str, bid_id: str, current_user: dict = Depends(get_current_user)):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["creator_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only job creator can select bids")
    
    bid = await db.bids.find_one({"id": bid_id, "job_id": job_id}, {"_id": 0})
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    # Update job and bid status
    await db.jobs.update_one({"id": job_id}, {
        "$set": {
            "selected_bid_id": bid_id,
            "status": JobStatus.IN_PROGRESS,
            "selected_at": datetime.utcnow()
        }
    })
    
    await db.bids.update_one({"id": bid_id}, {"$set": {"is_selected": True}})
    
    return {"message": "Bid selected successfully"}

@app.post("/api/payments/create")
async def create_payment(payment_data: PaymentCreate, current_user: dict = Depends(get_current_user)):
    job = await db.jobs.find_one({"id": payment_data.job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    bid = await db.bids.find_one({"id": payment_data.bid_id}, {"_id": 0})
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    
    if job["creator_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only job creator can make payments")
    
    # Create payment with mock handler
    payment_result = await MockPaymentHandler.create_payment(
        payment_data.payment_method,
        payment_data.amount,
        f"job_{payment_data.job_id}"
    )
    
    if payment_result["success"]:
        payment_id = str(uuid.uuid4())
        payment_doc = {
            "id": payment_id,
            "job_id": payment_data.job_id,
            "bid_id": payment_data.bid_id,
            "payer_id": current_user["id"],
            "receiver_id": bid["bidder_id"],
            "amount": payment_data.amount,
            "payment_method": payment_data.payment_method,
            "status": PaymentStatus.PENDING,
            "gateway_payment_id": payment_result["payment_id"],
            "gateway_url": payment_result["gateway_url"],
            "created_at": datetime.utcnow(),
            "escrow_hold_until": datetime.utcnow() + timedelta(days=7)
        }
        
        await db.payments.insert_one(payment_doc)
        
        return {
            "message": "Payment created successfully",
            "payment_id": payment_id,
            "gateway_url": payment_result["gateway_url"],
            "payment_method": payment_data.payment_method.value
        }
    else:
        raise HTTPException(status_code=400, detail="Payment creation failed")

@app.post("/api/payments/{payment_id}/confirm")
async def confirm_payment(payment_id: str, background_tasks: BackgroundTasks):
    payment = await db.payments.find_one({"id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Mock payment confirmation
    status_result = await MockPaymentHandler.check_payment_status(payment["gateway_payment_id"])
    
    if status_result["success"] and status_result["status"] == "paid":
        await db.payments.update_one(
            {"id": payment_id},
            {"$set": {"status": PaymentStatus.HELD_IN_ESCROW, "paid_at": datetime.utcnow()}}
        )
        
        return {"message": "Payment confirmed and held in escrow"}
    else:
        raise HTTPException(status_code=400, detail="Payment not confirmed")

@app.post("/api/payments/{payment_id}/release")
async def release_payment(payment_id: str, current_user: dict = Depends(get_current_user)):
    payment = await db.payments.find_one({"id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment["payer_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only payer can release payments")
    
    if payment["status"] != PaymentStatus.HELD_IN_ESCROW:
        raise HTTPException(status_code=400, detail="Payment not in escrow")
    
    # Release payment and update wallet
    await db.payments.update_one(
        {"id": payment_id},
        {"$set": {"status": PaymentStatus.RELEASED, "released_at": datetime.utcnow()}}
    )
    
    await db.users.update_one(
        {"id": payment["receiver_id"]},
        {"$inc": {"wallet_balance": payment["amount"]}}
    )
    
    # Mark job as completed
    await db.jobs.update_one(
        {"id": payment["job_id"]},
        {"$set": {"status": JobStatus.COMPLETED, "completed_at": datetime.utcnow()}}
    )
    
    return {"message": "Payment released successfully"}

@app.post("/api/messages")
async def send_message(message_data: MessageCreate, current_user: dict = Depends(get_current_user)):
    message_id = str(uuid.uuid4())
    message_doc = {
        "id": message_id,
        "sender_id": current_user["id"],
        "sender_name": current_user["full_name"],
        "recipient_id": message_data.recipient_id,
        "content": message_data.content,
        "job_id": message_data.job_id,
        "created_at": datetime.utcnow(),
        "is_read": False
    }
    
    await db.messages.insert_one(message_doc)
    return {"message": "Message sent successfully", "message_id": message_id}

@app.get("/api/messages/{user_id}")
async def get_conversation(user_id: str, current_user: dict = Depends(get_current_user)):
    cursor = db.messages.find({
        "$or": [
            {"sender_id": current_user["id"], "recipient_id": user_id},
            {"sender_id": user_id, "recipient_id": current_user["id"]}
        ]
    }, {"_id": 0}).sort("created_at", 1)
    
    messages = await cursor.to_list(length=None)
    return {"messages": messages}

@app.post("/api/ratings")
async def create_rating(rating_data: RatingCreate, current_user: dict = Depends(get_current_user)):
    # Check if job exists and user is involved
    job = await db.jobs.find_one({"id": rating_data.job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if rating already exists
    existing_rating = await db.ratings.find_one({
        "rater_id": current_user["id"],
        "job_id": rating_data.job_id,
        "target_user_id": rating_data.target_user_id
    }, {"_id": 0})
    if existing_rating:
        raise HTTPException(status_code=400, detail="Rating already exists")
    
    rating_id = str(uuid.uuid4())
    rating_doc = {
        "id": rating_id,
        "rater_id": current_user["id"],
        "target_user_id": rating_data.target_user_id,
        "job_id": rating_data.job_id,
        "rating": rating_data.rating,
        "comment": rating_data.comment,
        "created_at": datetime.utcnow()
    }
    
    await db.ratings.insert_one(rating_doc)
    
    # Update user's average rating
    ratings_cursor = db.ratings.find({"target_user_id": rating_data.target_user_id}, {"_id": 0})
    all_ratings = await ratings_cursor.to_list(length=None)
    
    avg_rating = sum(r["rating"] for r in all_ratings) / len(all_ratings)
    
    await db.users.update_one(
        {"id": rating_data.target_user_id},
        {"$set": {"rating": round(avg_rating, 1), "total_ratings": len(all_ratings)}}
    )
    
    return {"message": "Rating submitted successfully"}

@app.get("/api/wallet")
async def get_wallet_info(current_user: dict = Depends(get_current_user)):
    # Get payment history
    payments_cursor = db.payments.find({
        "$or": [{"payer_id": current_user["id"]}, {"receiver_id": current_user["id"]}]
    }, {"_id": 0}).sort("created_at", -1).limit(20)
    
    payments = await payments_cursor.to_list(length=None)
    
    return {
        "balance": current_user.get("wallet_balance", 0),
        "recent_transactions": payments
    }

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    if current_user["role"] == UserRole.PENCARI_JASA:
        # Service Seeker stats
        total_jobs = await db.jobs.count_documents({"creator_id": current_user["id"]})
        active_jobs = await db.jobs.count_documents({"creator_id": current_user["id"], "status": JobStatus.OPEN})
        completed_jobs = await db.jobs.count_documents({"creator_id": current_user["id"], "status": JobStatus.COMPLETED})
        
        return {
            "role": "pencari_jasa",
            "total_jobs": total_jobs,
            "active_jobs": active_jobs,
            "completed_jobs": completed_jobs,
            "wallet_balance": current_user.get("wallet_balance", 0)
        }
    else:
        # Service Provider stats
        total_bids = await db.bids.count_documents({"bidder_id": current_user["id"]})
        selected_bids = await db.bids.count_documents({"bidder_id": current_user["id"], "is_selected": True})
        
        # Get earnings from completed jobs
        completed_payments = db.payments.find({
            "receiver_id": current_user["id"],
            "status": PaymentStatus.RELEASED
        }, {"_id": 0})
        payments = await completed_payments.to_list(length=None)
        total_earnings = sum(p["amount"] for p in payments)
        
        return {
            "role": "penyedia_jasa",
            "total_bids": total_bids,
            "selected_bids": selected_bids,
            "total_earnings": total_earnings,
            "wallet_balance": current_user.get("wallet_balance", 0),
            "rating": current_user.get("rating", 0.0)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)