from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timezone
from app.models.user import UserRegister, UserLogin, UserResponse, Token
from app.database import user_collection
from app.utils.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserRegister):
    existing_user = await user_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_dict = user.model_dump()
    user_dict["password"] = hash_password(user.password)
    user_dict["createdAt"] = datetime.now(timezone.utc)

    result = await user_collection.insert_one(user_dict)
    
    return UserResponse(
        userId=str(result.inserted_id),
        firstName=user.firstName,
        lastName=user.lastName,
        email=user.email,
        phone=user.phone,
        userType=user.userType,
        createdAt=user_dict["createdAt"]
    )

@router.post("/login", response_model=Token)
async def login_user(credentials: UserLogin):
    user = await user_collection.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    user_id = str(user["_id"])
    access_token = create_access_token(data={"sub": user_id, "userType": user["userType"]})

    return Token(
        access_token=access_token,
        token_type="bearer",
        userType=user["userType"],
        userId=user_id
    )