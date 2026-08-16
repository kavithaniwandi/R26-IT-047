from pydantic import BaseModel, EmailStr, Field
from typing import Literal
from datetime import datetime

class UserRegister(BaseModel):
    firstName: str = Field(..., min_length=2)
    lastName: str = Field(..., min_length=2)
    email: EmailStr
    phone: str
    userType: Literal["admin", "donor"]
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    userId: str
    firstName: str
    lastName: str
    email: EmailStr
    phone: str
    userType: str
    createdAt: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    userType: str
    userId: str