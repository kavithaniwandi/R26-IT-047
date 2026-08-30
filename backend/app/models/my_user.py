from pydantic import BaseModel, EmailStr, Field
from typing import Literal
from datetime import datetime

class UserRegister(BaseModel):
    firstName: str = Field(..., min_length=2)
    lastName: str = Field(..., min_length=2)
    email: str
    phone: str
    userType: Literal["admin", "donor", "disaster_officer", "volunteer"]
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    userId: str
    firstName: str
    lastName: str
    email: str
    phone: str
    userType: str
    createdAt: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    userType: str
    userId: str
