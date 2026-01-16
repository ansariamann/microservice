"""
Business logic services for User Service
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional

from .models import User
from .schemas import UserRegistration, UserLogin, UserResponse, TokenResponse, UserProfileUpdate
from .auth import password_hasher, jwt_manager


class UserService:
    """Service class for user-related business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def register_user(self, user_data: UserRegistration) -> TokenResponse:
        """Register a new user"""
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError("Email already registered")
        
        # Hash password
        hashed_password = password_hasher.hash_password(user_data.password)
        
        # Create new user
        new_user = User(
            email=user_data.email,
            password_hash=hashed_password,
            name=user_data.name
        )
        
        try:
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Email already registered")
        
        # Generate JWT token
        access_token = jwt_manager.create_access_token(new_user.id, new_user.email)
        
        # Return token response
        user_response = UserResponse.model_validate(new_user)
        return TokenResponse(
            access_token=access_token,
            user=user_response
        )
    
    def authenticate_user(self, login_data: UserLogin) -> TokenResponse:
        """Authenticate a user and return JWT token"""
        # Find user by email
        user = self.db.query(User).filter(User.email == login_data.email).first()
        if not user:
            raise ValueError("Invalid email or password")
        
        # Verify password
        if not password_hasher.verify_password(login_data.password, user.password_hash):
            raise ValueError("Invalid email or password")
        
        # Generate JWT token
        access_token = jwt_manager.create_access_token(user.id, user.email)
        
        # Return token response
        user_response = UserResponse.model_validate(user)
        return TokenResponse(
            access_token=access_token,
            user=user_response
        )
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_profile(self, user: User) -> UserResponse:
        """Get user profile"""
        return UserResponse.model_validate(user)
    
    def update_user_profile(self, user: User, update_data: UserProfileUpdate) -> UserResponse:
        """Update user profile"""
        # Check if email is being updated and if it's already taken
        if update_data.email and update_data.email != user.email:
            existing_user = self.db.query(User).filter(User.email == update_data.email).first()
            if existing_user:
                raise ValueError("Email already registered")
        
        # Update fields if provided
        if update_data.name is not None:
            user.name = update_data.name
        if update_data.email is not None:
            user.email = update_data.email
        
        try:
            self.db.commit()
            self.db.refresh(user)
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Email already registered")
        
        return UserResponse.model_validate(user)