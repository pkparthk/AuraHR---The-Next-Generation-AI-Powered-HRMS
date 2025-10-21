from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from datetime import timedelta, datetime
from typing import Any

from app.core.database import get_database
from app.core.security import (
    verify_password, 
    create_access_token, 
    get_password_hash,
    get_current_user_token
)
from app.core.config import settings
from app.models.schemas import UserLogin, UserCreate, Token, User, UserResponse

router = APIRouter()
security = HTTPBearer()

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db=Depends(get_database)):
    """Authenticate user and return JWT token."""
    
    # Find user by email
    user_doc = await db.users.find_one({"email": user_credentials.email})
    
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(user_credentials.password, user_doc["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_doc["email"], "role": user_doc["role"], "user_id": str(user_doc["_id"])},
        expires_delta=access_token_expires
    )
    
    # Prepare user response
    user_response = UserResponse(
        id=str(user_doc["_id"]),
        email=user_doc["email"],
        role=user_doc["role"],
        employee_id=str(user_doc.get("employeeId")) if user_doc.get("employeeId") else None,
        created_at=user_doc["createdAt"]
    )
    
    return Token(
        access_token=access_token,
        user=user_response
    )

@router.get("/me", response_model=Any)
async def get_current_user_profile(
    token_data: dict = Depends(get_current_user_token),
    db=Depends(get_database)
):
    """Get current user's profile information."""
    
    user_id = token_data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Get user document
    user_doc = await db.users.find_one({"_id": user_id})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # If user has an employee profile, get employee data
    if user_doc.get("employeeId"):
        employee_doc = await db.employees.find_one({"_id": user_doc["employeeId"]})
        if employee_doc:
            # Combine user and employee data
            return {
                "id": str(user_doc["_id"]),
                "email": user_doc["email"],
                "role": user_doc["role"],
                "employee": {
                    "id": str(employee_doc["_id"]),
                    "firstName": employee_doc["firstName"],
                    "lastName": employee_doc["lastName"],
                    "jobTitle": employee_doc["jobTitle"],
                    "department": employee_doc["department"],
                    "managerId": str(employee_doc.get("managerId")) if employee_doc.get("managerId") else None,
                    "hireDate": employee_doc["hireDate"],
                    "contactInfo": employee_doc.get("contactInfo", {}),
                    "extractedSkills": employee_doc.get("extractedSkills", []),
                    "careerGoals": employee_doc.get("careerGoals", "")
                }
            }
    
    # Return user data only
    return UserResponse(
        id=str(user_doc["_id"]),
        email=user_doc["email"],
        role=user_doc["role"],
        employee_id=str(user_doc.get("employeeId")) if user_doc.get("employeeId") else None,
        created_at=user_doc["createdAt"]
    )

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db=Depends(get_database)):
    """Register a new user (for testing purposes)."""
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user document
    user_doc = {
        "email": user_data.email,
        "password": hashed_password,
        "role": user_data.role,  # Use provided role
        "employeeId": None,
        "createdAt": datetime.utcnow()
    }
    
    # Insert user
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    
    return UserResponse(
        id=str(user_doc["_id"]),
        email=user_doc["email"],
        role=user_doc["role"],
        employee_id=None,
        created_at=user_doc["createdAt"]
    )