"""
Urban Cortex AI – FastAPI Dependencies
========================================

Authentication and authorization dependencies.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from fastapi import Depends, Header, HTTPException, status

from app.core.config import get_settings
from app.core.security import verify_access_token
from app.repositories.base_repository import BaseRepository
from app.core.collections import Collections

logger = logging.getLogger(__name__)


# ── Get Current User Dependency ────────────────────────────────

async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> Dict:
    """
    Extract JWT from Authorization header and return user.
    
    Raises:
        HTTPException: 401 if token missing or invalid
        HTTPException: 404 if user not found
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # Verify JWT token
    payload = verify_access_token(token)
    user_id = payload.get("sub")
    
    # Fetch user from Firestore
    try:
        user_repo = BaseRepository(Collections.USERS)
        user = user_repo.get_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to fetch user: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information",
        )


# ── Require Role Dependency Factory ────────────────────────────

def require_role(allowed_roles: List[str]):
    """
    Enforce role-based access control.
    
    Usage:
        @router.post("/admin-only")
        async def admin_endpoint(user=Depends(require_role(["admin"]))):
            return {"message": "Admin access"}
    """
    async def role_checker(user: Dict = Depends(get_current_user)) -> Dict:
        user_role = user.get("role")
        
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User role not assigned",
            )
        
        if user_role not in allowed_roles:
            logger.warning(
                "Access denied: user %s (role: %s) attempted to access endpoint requiring roles: %s",
                user.get("user_id"),
                user_role,
                allowed_roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}",
            )
        
        return user
    
    return role_checker


# ── System Authentication (API Key) ────────────────────────────

async def get_system_auth(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Dict:
    """
    Validate system API key for IoT endpoints.
    
    Raises:
        HTTPException: 401 if API key missing or invalid
    """
    settings = get_settings()
    
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
    
    if x_api_key != settings.iot_system_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    return {"role": "system"}


# ── Optional Authentication ────────────────────────────────────

async def get_current_user_optional(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> Optional[Dict]:
    """
    Extract user if token provided, otherwise return None.
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None
