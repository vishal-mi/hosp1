from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union
import uuid
from datetime import datetime, timedelta
import hashlib
import jwt
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Secret (in production, use a proper secret)
JWT_SECRET = "hospital-booking-secret-key"
JWT_ALGORITHM = "HS256"

# Create the main app without a prefix
app = FastAPI(title="Hospital Booking System")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Pydantic Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    phone: str
    password_hash: str
    user_type: str  # "patient", "doctor", "admin"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: str
    name: str
    phone: str
    password: str
    user_type: str = "patient"

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    phone: str
    user_type: str

class Doctor(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    specializations: List[str]
    experience_years: int
    qualifications: str
    consultation_fee: float
    available_days: List[str]  # ["Monday", "Tuesday", etc.]
    available_hours: Dict[str, List[str]]  # {"Monday": ["09:00", "10:00", ...]}
    is_available: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DoctorCreate(BaseModel):
    user_id: str
    specializations: List[str]
    experience_years: int
    qualifications: str
    consultation_fee: float
    available_days: List[str]
    available_hours: Dict[str, List[str]]

class DoctorResponse(BaseModel):
    id: str
    name: str
    specializations: List[str]
    experience_years: int
    qualifications: str
    consultation_fee: float
    available_days: List[str]
    available_hours: Dict[str, List[str]]
    is_available: bool

class SymptomAnalysis(BaseModel):
    symptoms: str
    patient_id: str

class DoctorRecommendation(BaseModel):
    doctor: DoctorResponse
    match_reason: str
    urgency_level: str

class SymptomAnalysisResponse(BaseModel):
    analysis: str
    recommended_specialties: List[str]
    recommended_doctors: List[DoctorRecommendation]
    urgency_level: str
    additional_notes: str

class Appointment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    doctor_id: str
    appointment_date: datetime
    symptoms: str
    status: str = "scheduled"  # "scheduled", "completed", "cancelled", "rescheduled"
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AppointmentCreate(BaseModel):
    doctor_id: str
    appointment_date: datetime
    symptoms: str

class AppointmentResponse(BaseModel):
    id: str
    patient_name: str
    doctor_name: str
    appointment_date: datetime
    symptoms: str
    status: str
    notes: Optional[str]

class AppointmentUpdate(BaseModel):
    appointment_date: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None

# Utility Functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# AI-Powered Symptom Analysis
async def analyze_symptoms_with_ai(symptoms: str, patient_id: str) -> SymptomAnalysisResponse:
    try:
        # Initialize AI chat
        chat = LlmChat(
            api_key=os.environ['OPENAI_API_KEY'],
            session_id=f"symptom_analysis_{patient_id}_{datetime.now().timestamp()}",
            system_message="""You are an AI medical assistant helping with symptom analysis for hospital appointment scheduling. 
            Your role is to:
            1. Analyze patient symptoms
            2. Suggest appropriate medical specialties
            3. Assess urgency level (Low, Medium, High, Emergency)
            4. Provide helpful guidance
            
            IMPORTANT: Always include medical disclaimers and encourage patients to seek professional medical advice.
            
            Respond in JSON format with:
            {
                "analysis": "detailed analysis of symptoms",
                "recommended_specialties": ["list", "of", "specialties"],
                "urgency_level": "Low/Medium/High/Emergency",
                "additional_notes": "helpful advice and disclaimers"
            }"""
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(
            text=f"Patient symptoms: {symptoms}\n\nPlease analyze these symptoms and provide recommendations."
        )
        
        ai_response = await chat.send_message(user_message)
        
        # Parse AI response (assuming it returns JSON)
        import json
        try:
            ai_data = json.loads(ai_response)
        except:
            # Fallback if AI doesn't return proper JSON
            ai_data = {
                "analysis": ai_response,
                "recommended_specialties": ["General Medicine"],
                "urgency_level": "Medium",
                "additional_notes": "Please consult with a healthcare professional for proper diagnosis."
            }
        
        # Get matching doctors based on specialties
        recommended_doctors = []
        for specialty in ai_data.get("recommended_specialties", []):
            doctors_cursor = db.doctors.find({"specializations": {"$in": [specialty]}, "is_available": True})
            specialty_doctors = await doctors_cursor.to_list(length=3)  # Limit to 3 per specialty
            
            for doctor_data in specialty_doctors:
                user_data = await db.users.find_one({"id": doctor_data["user_id"]})
                if user_data:
                    doctor_response = DoctorResponse(
                        id=doctor_data["id"],
                        name=user_data["name"],
                        specializations=doctor_data["specializations"],
                        experience_years=doctor_data["experience_years"],
                        qualifications=doctor_data["qualifications"],
                        consultation_fee=doctor_data["consultation_fee"],
                        available_days=doctor_data["available_days"],
                        available_hours=doctor_data["available_hours"],
                        is_available=doctor_data["is_available"]
                    )
                    
                    recommendation = DoctorRecommendation(
                        doctor=doctor_response,
                        match_reason=f"Specialized in {specialty}",
                        urgency_level=ai_data.get("urgency_level", "Medium")
                    )
                    recommended_doctors.append(recommendation)
        
        return SymptomAnalysisResponse(
            analysis=ai_data.get("analysis", "Symptom analysis completed"),
            recommended_specialties=ai_data.get("recommended_specialties", []),
            recommended_doctors=recommended_doctors,
            urgency_level=ai_data.get("urgency_level", "Medium"),
            additional_notes=ai_data.get("additional_notes", "Please consult with a healthcare professional.")
        )
        
    except Exception as e:
        logging.error(f"AI analysis error: {str(e)}")
        # Fallback to basic matching
        basic_specialties = ["General Medicine", "Internal Medicine"]
        doctors_cursor = db.doctors.find({"specializations": {"$in": basic_specialties}, "is_available": True})
        basic_doctors = await doctors_cursor.to_list(length=5)
        
        recommended_doctors = []
        for doctor_data in basic_doctors:
            user_data = await db.users.find_one({"id": doctor_data["user_id"]})
            if user_data:
                doctor_response = DoctorResponse(
                    id=doctor_data["id"],
                    name=user_data["name"],
                    specializations=doctor_data["specializations"],
                    experience_years=doctor_data["experience_years"],
                    qualifications=doctor_data["qualifications"],
                    consultation_fee=doctor_data["consultation_fee"],
                    available_days=doctor_data["available_days"],
                    available_hours=doctor_data["available_hours"],
                    is_available=doctor_data["is_available"]
                )
                
                recommendation = DoctorRecommendation(
                    doctor=doctor_response,
                    match_reason="General consultation",
                    urgency_level="Medium"
                )
                recommended_doctors.append(recommendation)
        
        return SymptomAnalysisResponse(
            analysis="Basic symptom analysis - AI service temporarily unavailable",
            recommended_specialties=basic_specialties,
            recommended_doctors=recommended_doctors,
            urgency_level="Medium",
            additional_notes="Please consult with a healthcare professional for proper diagnosis."
        )

# API Routes

# Authentication Routes
@api_router.post("/register", response_model=dict)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_dict = user_data.dict()
    user_dict["password_hash"] = hash_password(user_data.password)
    del user_dict["password"]
    
    user = User(**user_dict)
    await db.users.insert_one(user.dict())
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**user.dict())
    }

@api_router.post("/login", response_model=dict)
async def login(login_data: UserLogin):
    user_data = await db.users.find_one({"email": login_data.email})
    if not user_data or not verify_password(login_data.password, user_data["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = User(**user_data)
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**user.dict())
    }

# Symptom Analysis Routes
@api_router.post("/analyze-symptoms", response_model=SymptomAnalysisResponse)
async def analyze_symptoms(
    symptom_data: SymptomAnalysis,
    current_user: User = Depends(get_current_user)
):
    if current_user.user_type not in ["patient", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return await analyze_symptoms_with_ai(symptom_data.symptoms, current_user.id)

# Doctor Management Routes
@api_router.post("/doctors", response_model=dict)
async def create_doctor(
    doctor_data: DoctorCreate,
    current_user: User = Depends(get_current_user)
):
    if current_user.user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    doctor = Doctor(**doctor_data.dict())
    await db.doctors.insert_one(doctor.dict())
    
    return {"message": "Doctor created successfully", "doctor_id": doctor.id}

@api_router.get("/doctors", response_model=List[DoctorResponse])
async def get_doctors():
    doctors_cursor = db.doctors.find({"is_available": True})
    doctors = await doctors_cursor.to_list(length=100)
    
    doctor_responses = []
    for doctor_data in doctors:
        user_data = await db.users.find_one({"id": doctor_data["user_id"]})
        if user_data:
            doctor_response = DoctorResponse(
                id=doctor_data["id"],
                name=user_data["name"],
                specializations=doctor_data["specializations"],
                experience_years=doctor_data["experience_years"],
                qualifications=doctor_data["qualifications"],
                consultation_fee=doctor_data["consultation_fee"],
                available_days=doctor_data["available_days"],
                available_hours=doctor_data["available_hours"],
                is_available=doctor_data["is_available"]
            )
            doctor_responses.append(doctor_response)
    
    return doctor_responses

# Appointment Routes
@api_router.post("/appointments", response_model=dict)
async def book_appointment(
    appointment_data: AppointmentCreate,
    current_user: User = Depends(get_current_user)
):
    if current_user.user_type != "patient":
        raise HTTPException(status_code=403, detail="Only patients can book appointments")
    
    # Check if doctor exists and is available
    doctor = await db.doctors.find_one({"id": appointment_data.doctor_id, "is_available": True})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found or unavailable")
    
    # Check for conflicting appointments
    existing_appointment = await db.appointments.find_one({
        "doctor_id": appointment_data.doctor_id,
        "appointment_date": appointment_data.appointment_date,
        "status": {"$ne": "cancelled"}
    })
    
    if existing_appointment:
        raise HTTPException(status_code=400, detail="Time slot already booked")
    
    appointment = Appointment(
        patient_id=current_user.id,
        doctor_id=appointment_data.doctor_id,
        appointment_date=appointment_data.appointment_date,
        symptoms=appointment_data.symptoms
    )
    
    await db.appointments.insert_one(appointment.dict())
    
    return {"message": "Appointment booked successfully", "appointment_id": appointment.id}

@api_router.get("/appointments", response_model=List[AppointmentResponse])
async def get_appointments(current_user: User = Depends(get_current_user)):
    if current_user.user_type == "patient":
        appointments_cursor = db.appointments.find({"patient_id": current_user.id})
    elif current_user.user_type == "doctor":
        doctor_data = await db.doctors.find_one({"user_id": current_user.id})
        if not doctor_data:
            return []
        appointments_cursor = db.appointments.find({"doctor_id": doctor_data["id"]})
    else:  # admin
        appointments_cursor = db.appointments.find({})
    
    appointments = await appointments_cursor.to_list(length=100)
    
    appointment_responses = []
    for appt in appointments:
        patient_data = await db.users.find_one({"id": appt["patient_id"]})
        doctor_data = await db.doctors.find_one({"id": appt["doctor_id"]})
        doctor_user_data = await db.users.find_one({"id": doctor_data["user_id"]}) if doctor_data else None
        
        if patient_data and doctor_user_data:
            appointment_response = AppointmentResponse(
                id=appt["id"],
                patient_name=patient_data["name"],
                doctor_name=doctor_user_data["name"],
                appointment_date=appt["appointment_date"],
                symptoms=appt["symptoms"],
                status=appt["status"],
                notes=appt.get("notes")
            )
            appointment_responses.append(appointment_response)
    
    return appointment_responses

@api_router.put("/appointments/{appointment_id}", response_model=dict)
async def update_appointment(
    appointment_id: str,
    update_data: AppointmentUpdate,
    current_user: User = Depends(get_current_user)
):
    appointment = await db.appointments.find_one({"id": appointment_id})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Check permissions
    if current_user.user_type == "patient" and appointment["patient_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.user_type == "doctor":
        doctor_data = await db.doctors.find_one({"user_id": current_user.id})
        if not doctor_data or appointment["doctor_id"] != doctor_data["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Update appointment
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    if update_dict:
        await db.appointments.update_one({"id": appointment_id}, {"$set": update_dict})
    
    return {"message": "Appointment updated successfully"}

# Sample data creation endpoint (for testing)
@api_router.post("/create-sample-data")
async def create_sample_data():
    # Create sample admin user
    admin_user = User(
        email="admin@hospital.com",
        name="Hospital Admin",
        phone="1234567890",
        password_hash=hash_password("admin123"),
        user_type="admin"
    )
    await db.users.insert_one(admin_user.dict())
    
    # Create sample doctor users
    doctor_users = [
        User(
            email="dr.smith@hospital.com",
            name="Dr. John Smith",
            phone="1234567891",
            password_hash=hash_password("doctor123"),
            user_type="doctor"
        ),
        User(
            email="dr.jones@hospital.com",
            name="Dr. Sarah Jones",
            phone="1234567892",
            password_hash=hash_password("doctor123"),
            user_type="doctor"
        ),
        User(
            email="dr.brown@hospital.com",
            name="Dr. Michael Brown",
            phone="1234567893",
            password_hash=hash_password("doctor123"),
            user_type="doctor"
        )
    ]
    
    for doctor_user in doctor_users:
        await db.users.insert_one(doctor_user.dict())
    
    # Create sample doctors
    sample_doctors = [
        Doctor(
            user_id=doctor_users[0].id,
            specializations=["Cardiology", "Internal Medicine"],
            experience_years=15,
            qualifications="MD, FACC",
            consultation_fee=200.0,
            available_days=["Monday", "Wednesday", "Friday"],
            available_hours={
                "Monday": ["09:00", "10:00", "11:00", "14:00", "15:00"],
                "Wednesday": ["09:00", "10:00", "11:00", "14:00", "15:00"],
                "Friday": ["09:00", "10:00", "11:00", "14:00", "15:00"]
            }
        ),
        Doctor(
            user_id=doctor_users[1].id,
            specializations=["Dermatology", "Cosmetic Surgery"],
            experience_years=12,
            qualifications="MD, Board Certified Dermatologist",
            consultation_fee=150.0,
            available_days=["Tuesday", "Thursday", "Saturday"],
            available_hours={
                "Tuesday": ["10:00", "11:00", "14:00", "15:00", "16:00"],
                "Thursday": ["10:00", "11:00", "14:00", "15:00", "16:00"],
                "Saturday": ["09:00", "10:00", "11:00"]
            }
        ),
        Doctor(
            user_id=doctor_users[2].id,
            specializations=["Orthopedics", "Sports Medicine"],
            experience_years=18,
            qualifications="MD, Orthopedic Surgeon",
            consultation_fee=250.0,
            available_days=["Monday", "Tuesday", "Thursday"],
            available_hours={
                "Monday": ["08:00", "09:00", "13:00", "14:00"],
                "Tuesday": ["08:00", "09:00", "13:00", "14:00"],
                "Thursday": ["08:00", "09:00", "13:00", "14:00"]
            }
        )
    ]
    
    for doctor in sample_doctors:
        await db.doctors.insert_one(doctor.dict())
    
    return {"message": "Sample data created successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()