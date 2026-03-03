"""
Urban Cortex AI – Auth Service
================================

Authentication business logic.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict

from fastapi import HTTPException, status

from app.core.collections import Collections
from app.core.security import hash_password, verify_password, create_access_token
from app.repositories.base_repository import BaseRepository, FirestoreError

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service."""
    
    def __init__(self):
        self.user_repo = BaseRepository(Collections.USERS)
    
    # ── Signup ──────────────────────────────────────────────────
    
    async def signup(
        self,
        name: str,
        email: str,
        password: str,
        city: str
    ) -> Dict:
        """
        Register new citizen user.
        
        Raises:
            HTTPException: 409 if email already exists
            HTTPException: 500 if creation fails
        """
        # Check if email already exists
        users = self.user_repo.list(filters=[("email", "==", email)], limit=1)
        if users:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        
        # Generate user ID
        user_id = str(uuid.uuid4())
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Create user document
        try:
            now = datetime.now(timezone.utc)
            user_data = {
                "user_id": user_id,
                "name": name,
                "email": email,
                "password": hashed_password,
                "role": "citizen",
                "assigned_truck_id": None,
                "city": city,
                "is_active": True,
                "created_at": now,
                "last_login": now,
            }
            
            created_user = self.user_repo.create(user_id, user_data)
            
            logger.info("User registered: %s (%s)", user_id, email)
            
            return created_user
            
        except FirestoreError as exc:
            logger.error("Failed to create user: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account",
            )
    
    # ── Login ───────────────────────────────────────────────────
    
    async def login(self, email: str, password: str) -> str:
        """
        Authenticate user and return JWT token.
        
        Raises:
            HTTPException: 401 if credentials invalid
        """
        # Find user by email
        users = self.user_repo.list(filters=[("email", "==", email)], limit=1)
        if not users:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        user = users[0]
        
        # Verify password
        if not verify_password(password, user.get("password", "")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        # Check if active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )
        
        # Update last_login
        try:
            self.user_repo.update(user["id"], {"last_login": datetime.now(timezone.utc)})
        except Exception as exc:
            logger.error("Failed to update last_login: %s", str(exc))
        
        # Generate JWT token
        access_token = create_access_token(data={"sub": user["id"]})
        
        logger.info("User logged in: %s (%s)", user["id"], email)
        
        return access_token
    
    # ── Get User Profile ────────────────────────────────────────
    
    def format_user_profile(self, user: Dict) -> Dict:
        """Format user data for profile response."""
        created_at = user.get("created_at")
        last_login = user.get("last_login")
        
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        
        if isinstance(last_login, datetime):
            last_login = last_login.isoformat()
        
        return {
            "user_id": user.get("user_id") or user.get("id"),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
            "assigned_truck_id": user.get("assigned_truck_id"),
            "city": user.get("city"),
            "is_active": user.get("is_active", True),
            "created_at": created_at,
            "last_login": last_login,
        }
