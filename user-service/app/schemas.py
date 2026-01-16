"""
Pydantic schemas for User Service
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
import re


class UserRegistration(BaseModel):
    """Schema for user registration request"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=128, description="User's password (minimum 8 characters)")
    name: str = Field(..., min_length=1, max_length=255, description="User's full name")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name format"""
        if not v.strip():
            raise ValueError('Name cannot be empty')
        # Remove excessive whitespace
        return ' '.join(v.split())


class UserLogin(BaseModel):
    """Schema for user login request"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    email: str
    name: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Schema for authentication token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")


class UserProfileUpdate(BaseModel):
    """Schema for user profile update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="User's full name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name format"""
        if v is not None:
            if not v.strip():
                raise ValueError('Name cannot be empty')
            # Remove excessive whitespace
            return ' '.join(v.split())
        return v


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: dict = Field(..., description="Error details")
    
    @classmethod
    def create(cls, code: str, message: str, details: Optional[dict] = None):
        """Create an error response"""
        error_dict = {
            "code": code,
            "message": message
        }
        if details:
            error_dict["details"] = details
        return cls(error=error_dict)