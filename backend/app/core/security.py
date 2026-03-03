"""
Urban Cortex AI – Security Module
===================================

JWT authentication and password hashing.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password Hashing ───────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Token Generation ───────────────────────────────────────

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Payload data (must include 'sub' for user_id)
        expires_delta: Token expiry duration
        
    Returns:
        Encoded JWT token string
    """
    settings = get_settings()
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


# ── JWT Token Verification ─────────────────────────────────────

def verify_access_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    settings = get_settings()
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )
        
        return payload
        
    except JWTError as exc:
        logger.warning("JWT verification failed: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# ── Ownership Validation ───────────────────────────────────────

def validate_ownership(
    user: Dict[str, Any],
    resource: Dict[str, Any],
    ownership_field: str = "created_by",
) -> None:
    """
    Validate that user owns the resource.
    
    Raises:
        HTTPException: 403 if ownership check fails
    """
    user_id = user.get("user_id") or user.get("id")
    resource_owner = resource.get(ownership_field)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User identification error",
        )
    
    if not resource_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: resource ownership cannot be determined",
        )
    
    if resource_owner != user_id:
        logger.warning(
            "Ownership validation failed: user %s attempted to access resource owned by %s",
            user_id,
            resource_owner,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: resource ownership mismatch",
        )


def validate_driver_truck_access(user: Dict[str, Any], truck_id: str) -> None:
    """
    Validate driver can access specified truck.
    
    Raises:
        HTTPException: 403 if driver not assigned to truck
    """
    if user.get("role") != "driver":
        return
    
    assigned_truck = user.get("assigned_truck_id")
    
    if not assigned_truck:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: no truck assigned to driver",
        )
    
    if assigned_truck != truck_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: truck not assigned to driver",
        )
